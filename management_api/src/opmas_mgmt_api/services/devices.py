"""Device management service."""

from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
import asyncio
import aiohttp
import ipaddress

from opmas_mgmt_api.models.devices import Device
from opmas_mgmt_api.schemas.devices import DeviceCreate, DeviceUpdate, DeviceStatus, DeviceDiscovery
from opmas_mgmt_api.core.exceptions import OPMASException
from opmas_mgmt_api.core.nats import NATSManager

class DeviceService:
    """Device management service."""
    
    def __init__(self, db: Session, nats: NATSManager):
        """Initialize service with database session and NATS manager."""
        self.db = db
        self.nats = nats
        
    async def list_devices(
        self,
        skip: int = 0,
        limit: int = 100,
        device_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Device], int]:
        """List devices with pagination and filtering."""
        query = select(Device)
        
        if device_type:
            query = query.where(Device.device_type == device_type)
        if status:
            query = query.where(Device.status == status)
            
        total = len(await self.db.execute(query))
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        devices = result.scalars().all()
        
        return devices, total
        
    async def create_device(self, device: DeviceCreate) -> Device:
        """Create a new device."""
        db_device = Device(
            **device.model_dump(),
            status="inactive",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            self.db.add(db_device)
            await self.db.commit()
            await self.db.refresh(db_device)
            return db_device
        except IntegrityError as e:
            await self.db.rollback()
            raise OPMASException(
                status_code=400,
                detail=f"Device creation failed: {str(e)}"
            )
            
    async def get_device(self, device_id: UUID) -> Optional[Device]:
        """Get device by ID."""
        query = select(Device).where(Device.id == device_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
        
    async def update_device(
        self,
        device_id: UUID,
        device: DeviceUpdate
    ) -> Optional[Device]:
        """Update device details."""
        query = (
            update(Device)
            .where(Device.id == device_id)
            .values(
                **device.model_dump(exclude_unset=True),
                updated_at=datetime.utcnow()
            )
            .returning(Device)
        )
        
        try:
            result = await self.db.execute(query)
            await self.db.commit()
            return result.scalar_one_or_none()
        except IntegrityError as e:
            await self.db.rollback()
            raise OPMASException(
                status_code=400,
                detail=f"Device update failed: {str(e)}"
            )
            
    async def delete_device(self, device_id: UUID) -> bool:
        """Delete a device."""
        query = delete(Device).where(Device.id == device_id)
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0
        
    async def get_device_status(self, device_id: UUID) -> Optional[DeviceStatus]:
        """Get device status."""
        device = await self.get_device(device_id)
        if not device:
            return None
            
        return DeviceStatus(
            status=device.status,
            timestamp=device.updated_at,
            details={"last_seen": device.updated_at.isoformat()}
        )
        
    async def update_device_status(
        self,
        device_id: UUID,
        status: DeviceStatus
    ) -> Optional[DeviceStatus]:
        """Update device status."""
        query = (
            update(Device)
            .where(Device.id == device_id)
            .values(
                status=status.status,
                updated_at=datetime.utcnow()
            )
            .returning(Device)
        )
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        device = result.scalar_one_or_none()
        if not device:
            return None
            
        return DeviceStatus(
            status=device.status,
            timestamp=device.updated_at,
            details=status.details
        )

    async def discover_devices(
        self,
        network: str,
        device_types: Optional[List[str]] = None,
        timeout: int = 5
    ) -> List[DeviceDiscovery]:
        """Discover devices on the network."""
        try:
            network = ipaddress.ip_network(network)
        except ValueError as e:
            raise OPMASException(
                status_code=400,
                detail=f"Invalid network address: {str(e)}"
            )

        discovered_devices = []
        tasks = []

        async def check_device(ip: str) -> Optional[Dict[str, Any]]:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://{ip}/api/v1/status",
                        timeout=timeout
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return {
                                "ip_address": ip,
                                "hostname": data.get("hostname", ip),
                                "device_type": data.get("device_type", "unknown"),
                                "model": data.get("model"),
                                "firmware_version": data.get("firmware_version"),
                                "status": "available"
                            }
            except (aiohttp.ClientError, asyncio.TimeoutError):
                pass
            return None

        # Create tasks for each IP in the network
        for ip in network.hosts():
            tasks.append(check_device(str(ip)))

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)

        # Filter out None results and create DeviceDiscovery objects
        for result in results:
            if result and (not device_types or result["device_type"] in device_types):
                discovered_devices.append(DeviceDiscovery(**result))

        # Publish discovery results
        await self.nats.publish(
            "devices.discovered",
            {
                "network": str(network),
                "count": len(discovered_devices),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        return discovered_devices

    async def get_device_metrics(self, device_id: UUID) -> Dict[str, Any]:
        """Get device metrics."""
        device = await self.get_device(device_id)
        if not device:
            raise OPMASException(
                status_code=404,
                detail="Device not found"
            )

        # Request metrics from device
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{device.ip_address}/api/v1/metrics",
                    timeout=5
                ) as response:
                    if response.status == 200:
                        metrics = await response.json()
                        return {
                            "device_id": str(device_id),
                            "timestamp": datetime.utcnow().isoformat(),
                            "metrics": metrics
                        }
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise OPMASException(
                status_code=503,
                detail=f"Failed to get device metrics: {str(e)}"
            )

    async def update_device_configuration(
        self,
        device_id: UUID,
        configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update device configuration."""
        device = await self.get_device(device_id)
        if not device:
            raise OPMASException(
                status_code=404,
                detail="Device not found"
            )

        # Send configuration to device
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"http://{device.ip_address}/api/v1/config",
                    json=configuration,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Update device in database
                        await self.update_device(
                            device_id,
                            DeviceUpdate(
                                metadata={"last_config_update": datetime.utcnow().isoformat()}
                            )
                        )

                        # Publish configuration update event
                        await self.nats.publish(
                            "device.config.updated",
                            {
                                "device_id": str(device_id),
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )

                        return result
                    else:
                        raise OPMASException(
                            status_code=response.status,
                            detail=f"Device rejected configuration: {await response.text()}"
                        )
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise OPMASException(
                status_code=503,
                detail=f"Failed to update device configuration: {str(e)}"
            ) 
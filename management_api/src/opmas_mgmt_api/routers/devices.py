from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import device as device_models
from ..schemas import device as device_schemas
from ..database import get_db
from ..auth.dependencies import get_current_active_user
from datetime import datetime

router = APIRouter()

@router.get("/devices", response_model=List[device_schemas.DeviceInDB])
async def list_devices(
    skip: int = 0,
    limit: int = 100,
    device_type: Optional[str] = None,
    status: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = db.query(device_models.Device)
    
    if device_type:
        query = query.filter(device_models.Device.device_type == device_type)
    if status:
        query = query.filter(device_models.Device.status == status)
    if is_active is not None:
        query = query.filter(device_models.Device.is_active == is_active)
    
    devices = query.offset(skip).limit(limit).all()
    return devices

@router.post("/devices", response_model=device_schemas.DeviceInDB)
async def create_device(
    device: device_schemas.DeviceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Check if device with same hostname exists
    db_device = db.query(device_models.Device).filter(
        device_models.Device.hostname == device.hostname
    ).first()
    if db_device:
        raise HTTPException(
            status_code=400,
            detail="Device with this hostname already exists"
        )
    
    # Create new device
    db_device = device_models.Device(
        **device.dict(),
        status="pending",
        last_seen=datetime.utcnow()
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

@router.get("/devices/{device_id}", response_model=device_schemas.DeviceInDB)
async def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    device = db.query(device_models.Device).filter(
        device_models.Device.id == device_id
    ).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.put("/devices/{device_id}", response_model=device_schemas.DeviceInDB)
async def update_device(
    device_id: int,
    device: device_schemas.DeviceUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    db_device = db.query(device_models.Device).filter(
        device_models.Device.id == device_id
    ).first()
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check hostname uniqueness if being updated
    if device.hostname and device.hostname != db_device.hostname:
        existing = db.query(device_models.Device).filter(
            device_models.Device.hostname == device.hostname
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Device with this hostname already exists"
            )
    
    # Update device fields
    for key, value in device.dict(exclude_unset=True).items():
        setattr(db_device, key, value)
    
    db.commit()
    db.refresh(db_device)
    return db_device

@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    device = db.query(device_models.Device).filter(
        device_models.Device.id == device_id
    ).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db.delete(device)
    db.commit()
    return {"message": "Device deleted successfully"}

@router.get("/devices/{device_id}/status", response_model=device_schemas.DeviceStatus)
async def get_device_status(
    device_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    device = db.query(device_models.Device).filter(
        device_models.Device.id == device_id
    ).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "status": device.status,
        "last_seen": device.last_seen,
        "is_active": device.is_active
    }

@router.put("/devices/{device_id}/status", response_model=device_schemas.DeviceStatus)
async def update_device_status(
    device_id: int,
    status: str = Query(..., description="New device status"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    device = db.query(device_models.Device).filter(
        device_models.Device.id == device_id
    ).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.status = status
    device.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(device)
    
    return {
        "status": device.status,
        "last_seen": device.last_seen,
        "is_active": device.is_active
    }

@router.get("/devices/{device_id}/configuration", response_model=device_schemas.DeviceConfiguration)
async def get_device_configuration(
    device_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    device = db.query(device_models.Device).filter(
        device_models.Device.id == device_id
    ).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "configuration": device.configuration,
        "updated_at": device.updated_at or device.created_at
    }

@router.put("/devices/{device_id}/configuration", response_model=device_schemas.DeviceConfiguration)
async def update_device_configuration(
    device_id: int,
    configuration: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    device = db.query(device_models.Device).filter(
        device_models.Device.id == device_id
    ).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.configuration = configuration
    db.commit()
    db.refresh(device)
    
    return {
        "configuration": device.configuration,
        "updated_at": device.updated_at or device.created_at
    } 
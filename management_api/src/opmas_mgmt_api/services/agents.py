"""Agent management service."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from opmas_mgmt_api.core.exceptions import OPMASException
from opmas_mgmt_api.core.nats import NATSManager
from opmas_mgmt_api.models.agents import Agent
from opmas_mgmt_api.schemas.agents import AgentCreate, AgentDiscovery, AgentStatus, AgentUpdate
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AgentService:
    """Agent management service."""

    def __init__(self, db: AsyncSession, nats: NATSManager):
        """Initialize agent service."""
        self.db = db
        self.nats = nats
        self._discovery_responses = []
        self._registration_requests = {}

    async def start(self) -> None:
        """Start the agent service."""
        # Subscribe to registration requests
        await self.nats.subscribe("agent.registration.request", callback=self._handle_registration_request)
        logger.info("Subscribed to agent.registration.request")

    async def _handle_registration_request(self, msg) -> None:
        """Handle agent registration request."""
        try:
            request = json.loads(msg.data.decode())
            agent_id = request.get("agent_id")
            agent_type = request.get("agent_type")
            agent_metadata = request.get("agent_metadata", {})

            if not agent_id or not agent_type:
                logger.warning("Invalid registration request: missing required fields")
                return

            # Check if agent exists
            query = select(Agent).where(Agent.id == agent_id)
            result = await self.db.execute(query)
            existing_agent = result.scalar_one_or_none()

            try:
                if not existing_agent:
                    # Create new agent
                    new_agent = Agent(
                        id=agent_id,
                        name=agent_metadata.get("name", f"{agent_type}-{agent_id[:8]}"),
                        agent_type=agent_type,
                        status="active",
                        version=agent_metadata.get("version", "1.0.0"),
                        config=agent_metadata.get("config", {}),
                        agent_metadata=agent_metadata,
                        capabilities=agent_metadata.get("capabilities", []),
                        last_heartbeat=datetime.utcnow(),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    self.db.add(new_agent)
                    await self.db.commit()
                    logger.info("Registered new agent from sync: %s", agent_id)
                else:
                    # Update existing agent
                    existing_agent.last_heartbeat = datetime.utcnow()
                    existing_agent.status = "active"
                    existing_agent.agent_metadata = agent_metadata
                    existing_agent.updated_at = datetime.utcnow()
                    await self.db.commit()
                    logger.info("Updated existing agent from sync: %s", agent_id)

                # Send confirmation
                await self.nats.publish(
                    "agent.registration.confirm",
                    json.dumps({
                        "agent_id": agent_id,
                        "success": True,
                        "timestamp": datetime.utcnow().isoformat()
                    }).encode()
                )
            except Exception as e:
                logger.error("Error processing registration request: %s", e)
                await self.db.rollback()
                # Send failure confirmation
                await self.nats.publish(
                    "agent.registration.confirm",
                    json.dumps({
                        "agent_id": agent_id,
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }).encode()
                )
        except Exception as e:
            logger.error("Error handling registration request: %s", e)

    async def list_agents(
        self,
        skip: int = 0,
        limit: int = 100,
        agent_type: Optional[str] = None,
        status: Optional[str] = None,
        enabled: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "name",
        sort_direction: str = "asc",
    ) -> Dict[str, Any]:
        """List agents with pagination and filtering."""
        # Build base query with only existing columns
        query = select(
            Agent.id,
            Agent.name,
            Agent.agent_type,
            Agent.version,
            Agent.status,
            Agent.enabled,
            Agent.last_heartbeat,
            Agent.agent_metadata,
            Agent.capabilities,
        )

        # Apply filters
        if agent_type:
            query = query.where(Agent.agent_type == agent_type)
        if status:
            query = query.where(Agent.status == status)
        if enabled is not None:
            query = query.where(Agent.enabled == enabled)
        if search:
            query = query.where((Agent.name.ilike(f"%{search}%")) | (Agent.agent_type.ilike(f"%{search}%")))

        # Map frontend field names to model field names
        field_mapping = {
            "name": "name",
            "type": "agent_type",
            "status": "status",
            "enabled": "enabled",
            "lastHeartbeat": "last_heartbeat",
        }
        sort_field = field_mapping.get(sort_by, sort_by)

        # Apply sorting
        sort_column = getattr(Agent, sort_field, Agent.name)
        if sort_direction.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Get total count
        count_query = select(Agent.id)
        if query.whereclause is not None:
            count_query = count_query.where(query.whereclause)
        result = await self.db.execute(count_query)
        total = len(result.scalars().all())

        # Calculate pagination
        page = (skip // limit) + 1
        pages = (total + limit - 1) // limit

        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        agents = result.scalars().all()

        # Convert to response models
        agent_responses = []
        for agent in agents:
            agent_dict = {
                "id": agent.id,
                "name": agent.name,
                "agent_type": agent.agent_type,
                "status": agent.status,
                "enabled": agent.enabled,
                "last_seen": agent.last_heartbeat,
                "agent_metadata": agent.agent_metadata or {},
                "hostname": agent.agent_metadata.get("hostname", "") if agent.agent_metadata else "",
                "ip_address": agent.agent_metadata.get("ip_address", "127.0.0.1")
                if agent.agent_metadata
                else "127.0.0.1",
                "port": agent.agent_metadata.get("port", 8080) if agent.agent_metadata else 8080,
                "confidence": agent.agent_metadata.get("confidence", 1.0) if agent.agent_metadata else 1.0,
            }
            agent_responses.append(agent_dict)

        return {
            "agents": agent_responses,
            "total": total,
            "page": page,
            "size": limit,
            "pages": pages,
        }

    async def create_agent(self, agent: AgentCreate) -> Agent:
        """Create a new agent."""
        db_agent = Agent(
            **agent.model_dump(),
            status="inactive",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        try:
            self.db.add(db_agent)
            await self.db.commit()
            await self.db.refresh(db_agent)

            # Publish agent creation event
            await self.nats.publish(
                "agent.created",
                {
                    "agent_id": str(db_agent.id),
                    "agent_type": db_agent.agent_type,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            return db_agent
        except IntegrityError as e:
            await self.db.rollback()
            raise OPMASException(status_code=400, detail=f"Agent creation failed: {str(e)}")

    async def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        """Get agent by ID."""
        query = select(Agent).where(Agent.id == agent_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_agent(self, agent_id: UUID, agent: AgentUpdate) -> Optional[Agent]:
        """Update agent details."""
        query = (
            update(Agent)
            .where(Agent.id == agent_id)
            .values(**agent.model_dump(exclude_unset=True), updated_at=datetime.utcnow())
            .returning(Agent)
        )

        try:
            result = await self.db.execute(query)
            await self.db.commit()
            updated_agent = result.scalar_one_or_none()

            if updated_agent:
                # Publish agent update event
                await self.nats.publish(
                    "agent.updated",
                    {
                        "agent_id": str(agent_id),
                        "agent_type": updated_agent.agent_type,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            return updated_agent
        except IntegrityError as e:
            await self.db.rollback()
            raise OPMASException(status_code=400, detail=f"Agent update failed: {str(e)}")

    async def delete_agent(self, agent_id: UUID) -> bool:
        """Delete an agent."""
        query = delete(Agent).where(Agent.id == agent_id)
        result = await self.db.execute(query)
        await self.db.commit()

        if result.rowcount > 0:
            # Publish agent deletion event
            await self.nats.publish(
                "agent.deleted",
                {"agent_id": str(agent_id), "timestamp": datetime.utcnow().isoformat()},
            )
            return True
        return False

    async def get_agent_status(self, agent_id: UUID) -> Optional[AgentStatus]:
        """Get agent status."""
        agent = await self.get_agent(agent_id)
        if not agent:
            return None

        return AgentStatus(
            status=agent.status,
            timestamp=agent.updated_at,
            details={"last_heartbeat": (agent.last_heartbeat.isoformat() if agent.last_heartbeat else None)},
            metrics=agent.capabilities.get("metrics", {}) if agent.capabilities else {},
        )

    async def update_agent_status(self, agent_id: UUID, status: AgentStatus) -> Optional[AgentStatus]:
        """Update agent status."""
        query = (
            update(Agent)
            .where(Agent.id == agent_id)
            .values(status=status.status, last_heartbeat=datetime.utcnow(), updated_at=datetime.utcnow())
            .returning(Agent)
        )

        result = await self.db.execute(query)
        await self.db.commit()

        agent = result.scalar_one_or_none()
        if not agent:
            return None

        # Publish status update event
        await self.nats.publish(
            f"agent.status.{agent_id}",
            {
                "agent_id": str(agent_id),
                "status": status.status,
                "timestamp": datetime.utcnow().isoformat(),
                "details": status.details,
                "metrics": status.metrics,
            },
        )

        return AgentStatus(
            status=agent.status,
            timestamp=agent.updated_at,
            details=status.details,
            metrics=status.metrics,
        )

    async def discover_agents(self) -> List[AgentDiscovery]:
        """Discover available agents."""
        try:
            # Clear previous responses
            self._discovery_responses = []
            logger.info("Starting agent discovery process")

            # Subscribe to discovery responses
            async def handle_response(msg):
                try:
                    response = json.loads(msg.data.decode())
                    logger.info("Received discovery response: %s", response)
                    self._discovery_responses.append(response)
                except Exception as e:
                    logger.error("Error processing discovery response: %s", e)

            # Subscribe to responses
            logger.info("Subscribing to agent.discovery.response")
            await self.nats.subscribe("agent.discovery.response", callback=handle_response)
            logger.info("Successfully subscribed to agent.discovery.response")

            # Publish discovery request to NATS
            discovery_payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "discovery_request",
            }
            logger.info("Publishing discovery request to agent.discovery.broadcast: %s", discovery_payload)
            await self.nats.publish("agent.discovery.broadcast", json.dumps(discovery_payload).encode())
            logger.info("Successfully published discovery request")

            # Wait for responses
            logger.info("Waiting for discovery responses...")
            await asyncio.sleep(5)  # Increased timeout to 5 seconds
            logger.info("Discovery wait complete. Received %d responses", len(self._discovery_responses))

            # Process responses and register new agents
            for response in self._discovery_responses:
                try:
                    # Check if agent already exists
                    query = select(Agent).where(Agent.id == response["agent_id"])
                    result = await self.db.execute(query)
                    existing_agent = result.scalar_one_or_none()

                    # Extract agent metadata
                    agent_metadata = response.get("agent_metadata", {})
                    agent_type = response.get("agent_type", "unknown")
                    agent_name = agent_metadata.get("name", f"{agent_type}-{response['agent_id'][:8]}")

                    if not existing_agent:
                        # Create new agent
                        new_agent = Agent(
                            id=response["agent_id"],
                            name=agent_name,
                            agent_type=agent_type,
                            status="active",
                            version=agent_metadata.get("version", "1.0.0"),
                            config=agent_metadata.get("config", {}),
                            agent_metadata=agent_metadata,
                            capabilities=agent_metadata.get("capabilities", []),
                            last_heartbeat=datetime.utcnow(),
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                        )
                        self.db.add(new_agent)
                        await self.db.commit()
                        logger.info("Registered new agent: %s", response["agent_id"])
                    else:
                        # Update existing agent
                        existing_agent.last_heartbeat = datetime.utcnow()
                        existing_agent.status = "active"
                        existing_agent.agent_metadata = agent_metadata
                        existing_agent.updated_at = datetime.utcnow()
                        await self.db.commit()
                        logger.info("Updated existing agent: %s", response["agent_id"])
                except Exception as e:
                    logger.error("Error registering agent %s: %s", response["agent_id"], e)
                    await self.db.rollback()

            # Return currently registered agents
            query = select(Agent).where(Agent.status == "active")
            result = await self.db.execute(query)
            agents = result.scalars().all()

            return [
                AgentDiscovery(
                    name=agent.name,
                    agent_type=agent.agent_type,
                    hostname=agent.agent_metadata.get("hostname", "localhost"),
                    ip_address=agent.agent_metadata.get("ip_address", "127.0.0.1"),
                    port=agent.agent_metadata.get("port", 8080),
                    confidence=agent.agent_metadata.get("confidence", 1.0),
                    agent_metadata=agent.agent_metadata or {}
                )
                for agent in agents
            ]
        except Exception as e:
            logger.error("Error during agent discovery: %s", e)
            raise

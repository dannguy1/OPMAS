"""Import all models here for Alembic to detect them."""

from opmas_mgmt_api.db.base_class import Base
from opmas_mgmt_api.models.agents import Agent
from opmas_mgmt_api.models.devices import Device, DeviceStatusHistory 
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from opmas.models.device import Device
from opmas.models.log import Log
from opmas.models.rule import Rule
from opmas.models.base import Base
from datetime import datetime

# Create an in-memory SQLite database for testing
engine = create_engine('sqlite:///:memory:')
Session = sessionmaker(bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

def test_device_model(db_session):
    device = Device(id='test-device', hostname='Test Device', ip_address='192.168.1.1', device_type='sensor')
    db_session.add(device)
    db_session.commit()
    assert device.id == 'test-device'
    assert device.hostname == 'Test Device'
    assert device.ip_address == '192.168.1.1'
    assert device.device_type == 'sensor'

def test_log_model(db_session):
    log = Log(id='test-log', device_id='test-device', timestamp=datetime.now(), level='INFO', source='test', message='Test log message')
    db_session.add(log)
    db_session.commit()
    assert log.id == 'test-log'
    assert log.device_id == 'test-device'
    assert log.level == 'INFO'

def test_rule_model(db_session):
    rule = Rule(id='test-rule', name='Test Rule', pattern='value > 10', severity='WARNING')
    db_session.add(rule)
    db_session.commit()
    assert rule.id == 'test-rule'
    assert rule.name == 'Test Rule'
    assert rule.pattern == 'value > 10'
    assert rule.severity == 'WARNING' 
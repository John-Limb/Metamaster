"""Unit tests for AppSetting model"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.domain.settings.models import AppSetting
from tests.db_utils import TEST_DATABASE_URL


@pytest.fixture
def db():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_can_create_app_setting(db):
    setting = AppSetting(key="organisation_preset", value="plex")
    db.add(setting)
    db.commit()
    fetched = db.query(AppSetting).filter_by(key="organisation_preset").first()
    assert fetched is not None
    assert fetched.value == "plex"


def test_app_setting_updated_at_set_automatically(db):
    setting = AppSetting(key="foo", value="bar")
    db.add(setting)
    db.commit()
    assert setting.updated_at is not None
    assert isinstance(setting.updated_at, datetime)


def test_app_setting_updated_at_changes_on_update(db):
    setting = AppSetting(key="foo", value="bar")
    db.add(setting)
    db.commit()
    original_ts = setting.updated_at

    setting.value = "baz"
    db.commit()
    db.refresh(setting)

    assert setting.updated_at > original_ts

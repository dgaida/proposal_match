import os

from sqlalchemy import Boolean, Column, Integer, String, Text, create_engine, inspect
from sqlalchemy.orm import declarative_base

from app.utils.db_manager import DBManager


def test_db_migration():
    """
    Verifies that DBManager handles legacy database migration by adding new columns.
    """
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # 1. Create a "legacy" database without the new columns
    legacy_db_path = os.path.abspath("data/test_legacy.db")
    legacy_db_url = f"sqlite:///{legacy_db_path}"

    if os.path.exists(legacy_db_path):
        os.remove(legacy_db_path)

    Base = declarative_base()

    class LegacyCompany(Base):
        __tablename__ = "companies"
        id = Column(Integer, primary_key=True)
        name = Column(String(255))
        url = Column(String(255), unique=True, nullable=False)
        state = Column(String(100))
        city = Column(String(100))
        employees_count = Column(Integer)
        kmu_status = Column(Boolean)
        industry = Column(String(255))
        research_active = Column(Boolean)
        summary = Column(Text)
        products = Column(Text)

    engine = create_engine(legacy_db_url)
    Base.metadata.create_all(engine)

    # 2. Use DBManager to connect to this legacy database
    # The __init__ should trigger migration
    db_manager = DBManager(db_url=legacy_db_url)

    # 3. Verify that the columns now exist
    inspector = inspect(db_manager.engine)
    columns = [c["name"] for c in inspector.get_columns("companies")]

    assert "country" in columns
    assert "org_type" in columns

    if os.path.exists(legacy_db_path):
        os.remove(legacy_db_path)

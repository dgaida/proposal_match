import os
from sqlalchemy import Column, Integer, String, Boolean, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import List, Dict, Any

Base = declarative_base()

class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=True)
    url = Column(String(255), unique=True, nullable=False)
    state = Column(String(100))
    city = Column(String(100))
    employees_count = Column(Integer)
    kmu_status = Column(Boolean)
    industry = Column(String(255))
    country = Column(String(100))
    org_type = Column(String(100))
    research_active = Column(Boolean)
    summary = Column(Text)
    products = Column(Text)

class DBManager:
    def __init__(self, db_url: str = "sqlite:///data/companies.db"):
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self._ensure_columns_exist()
        self.Session = sessionmaker(bind=self.engine)

    def _ensure_columns_exist(self):
        """
        Ensures that all columns defined in the model exist in the database.
        This handles migrations for existing databases.
        """
        from sqlalchemy import inspect, text
        inspector = inspect(self.engine)
        if 'companies' in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('companies')]

            with self.engine.connect() as conn:
                if 'country' not in columns:
                    conn.execute(text("ALTER TABLE companies ADD COLUMN country VARCHAR(100)"))
                    conn.commit()
                if 'org_type' not in columns:
                    conn.execute(text("ALTER TABLE companies ADD COLUMN org_type VARCHAR(100)"))
                    conn.commit()

    def add_company(self, company_data: Dict[str, Any]):
        """
        Adds a new company to the database.
        """
        session = self.Session()
        company_data_copy = company_data.copy()
        if company_data_copy.get('employees_count') and not isinstance(company_data_copy['employees_count'], int):
            try:
                company_data_copy['employees_count'] = int(company_data_copy['employees_count'])
            except (ValueError, TypeError):
                company_data_copy['employees_count'] = None

        company = Company(**company_data_copy)
        session.merge(company)
        session.commit()
        session.close()

    def get_all_companies(self) -> List[Company]:
        """
        Retrieves all companies from the database.
        """
        session = self.Session()
        companies = session.query(Company).all()
        session.close()
        return companies

    def update_companies(self, updated_data: List[Dict[str, Any]]):
        """
        Batch updates companies in the database.
        """
        session = self.Session()
        try:
            for data in updated_data:
                # Assuming 'url' is the unique identifier for merging
                if 'url' in data:
                    company = session.query(Company).filter(Company.url == data['url']).first()
                    if company:
                        for key, value in data.items():
                            if hasattr(company, key):
                                setattr(company, key, value)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

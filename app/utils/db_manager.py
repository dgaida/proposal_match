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
    research_active = Column(Boolean)
    summary = Column(Text)
    products = Column(Text)

class DBManager:
    def __init__(self, db_url: str = "sqlite:///data/companies.db"):
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

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

import os
from sqlalchemy import Column, Integer, String, Boolean, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import List, Dict, Any, Union
from app.models.models import CompanyModel

Base = declarative_base()


class Company(Base):
    """SQLAlchemy model representing a company/organization.

    Attributes:
        id (int): Primary key.
        name (str): The name of the organization.
        url (str): The unique website URL.
        state (str): Federal state.
        city (str): City.
        employees_count (int): Approximate number of employees.
        kmu_status (bool): SME status.
        industry (str): Industrial sector.
        country (str): Country.
        org_type (str): Type (e.g., SME, Research).
        research_active (bool): Whether they do research.
        summary (str): Textual description.
        products (str): Description of products/services.
    """

    __tablename__ = "companies"
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
    """Manages SQLite database operations for companies using SQLAlchemy.

    Attributes:
        engine: SQLAlchemy engine.
        Session: sessionmaker instance.
    """

    def __init__(self, db_url: str = "sqlite:///data/companies.db"):
        """Initializes the database connection and ensures schema exists.

        Args:
            db_url (str): The database connection string.
        """
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self._ensure_columns_exist()
        self.Session = sessionmaker(bind=self.engine)

    def _ensure_columns_exist(self) -> None:
        """Ensures that all model columns exist in the DB (handles migrations)."""
        from sqlalchemy import inspect, text

        inspector = inspect(self.engine)
        if "companies" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("companies")]

            with self.engine.connect() as conn:
                if "country" not in columns:
                    conn.execute(
                        text("ALTER TABLE companies ADD COLUMN country VARCHAR(100)")
                    )
                    conn.commit()
                if "org_type" not in columns:
                    conn.execute(
                        text("ALTER TABLE companies ADD COLUMN org_type VARCHAR(100)")
                    )
                    conn.commit()

    def add_company(self, company_data: Union[Dict[str, Any], CompanyModel]) -> None:
        """Adds a new company or updates an existing one by URL.

        Args:
            company_data (Union[Dict[str, Any], CompanyModel]): Dictionary or model of company metadata.
        """
        if isinstance(company_data, CompanyModel):
            company_data = company_data.model_dump()

        session = self.Session()
        company_data_copy = company_data.copy()

        # Normalize URL: strip trailing slash
        if "url" in company_data_copy:
            company_data_copy["url"] = company_data_copy["url"].rstrip("/")

        if company_data_copy.get("employees_count") and not isinstance(
            company_data_copy["employees_count"], int
        ):
            try:
                company_data_copy["employees_count"] = int(
                    company_data_copy["employees_count"]
                )
            except (ValueError, TypeError):
                company_data_copy["employees_count"] = None

        try:
            # Check if company with this URL already exists to avoid IntegrityError even with session.merge
            # as unique constraints on String(255) might behave differently with merge in some SQLite versions
            existing = None
            if "url" in company_data_copy:
                existing = (
                    session.query(Company)
                    .filter(Company.url == company_data_copy["url"])
                    .first()
                )

            if existing:
                for key, value in company_data_copy.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                company = Company(**company_data_copy)
                session.add(company)

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_all_companies(self) -> List[Company]:
        """Retrieves all company records from the database.

        Returns:
            List[Company]: List of SQLAlchemy Company objects.
        """
        session = self.Session()
        companies = session.query(Company).all()
        session.close()
        return companies

    def deduplicate_companies(self) -> int:
        """Removes duplicate company entries based on normalized URLs.

        Returns:
            int: The number of duplicates removed.
        """
        session = self.Session()
        try:
            # Get all companies
            all_companies = session.query(Company).all()
            seen_urls = {}  # normalized_url -> id
            to_delete = []

            for company in all_companies:
                norm_url = (company.url or "").rstrip("/")
                if norm_url in seen_urls:
                    # Duplicate found! Keep the one that might have more info (simple heuristic: higher ID if data is equal, or just the first seen)
                    # For now, let's just delete the newer one
                    to_delete.append(company.id)
                else:
                    seen_urls[norm_url] = company.id

            if to_delete:
                session.query(Company).filter(Company.id.in_(to_delete)).delete(
                    synchronize_session=False
                )
                session.commit()
                return len(to_delete)
            return 0
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def is_url_indexed(self, url: str) -> bool:
        """Checks if a URL has already been indexed in the database.

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if it exists, False otherwise.
        """
        if not url:
            return False

        norm_url = url.rstrip("/")
        session = self.Session()
        exists = (
            session.query(Company).filter(Company.url.like(norm_url + "%")).first()
            is not None
        )
        # Better: check exactly for the normalized version or with slash
        exists = (
            session.query(Company)
            .filter((Company.url == norm_url) | (Company.url == norm_url + "/"))
            .first()
            is not None
        )
        session.close()
        return exists

    def update_companies(
        self, updated_data: List[Union[Dict[str, Any], CompanyModel]]
    ) -> None:
        """Performs a batch update of company records.

        Args:
            updated_data (List[Union[Dict[str, Any], CompanyModel]]): List of company data dicts or models (must include 'url').
        """
        session = self.Session()
        try:
            for data in updated_data:
                if isinstance(data, CompanyModel):
                    data = data.model_dump()

                # Assuming 'url' is the unique identifier for merging
                if "url" in data:
                    url = data["url"].rstrip("/")
                    company = session.query(Company).filter(Company.url == url).first()
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

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any


class CompanyModel(BaseModel):
    """
    Pydantic model representing a company/organization.
    """

    name: Optional[str] = None
    url: str
    state: Optional[str] = None
    city: Optional[str] = None
    employees_count: Optional[int] = None
    kmu_status: Optional[bool] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    org_type: Optional[str] = None
    research_active: Optional[bool] = None
    summary: Optional[str] = None
    products: Optional[str] = None


class ResearchCallModel(BaseModel):
    """
    Pydantic model representing a research call.
    """

    model_config = ConfigDict(populate_by_name=True)

    thema: str = Field(alias="Thema")
    zielsetzung: Optional[str] = Field(None, alias="Zielsetzung")
    deadline: Optional[str] = Field(None, alias="Deadline")
    sitz_der_organisation: Optional[str] = Field(None, alias="Sitz_der_Organisation")
    einstufig_zweistufig: Optional[str] = Field(None, alias="Einstufig_Zweistufig")
    anzahl_projektpartner: Optional[str] = Field(None, alias="Anzahl_Projektpartner")
    budget: Optional[str] = Field(None, alias="Budget")
    laufzeit: Optional[str] = Field(None, alias="Laufzeit")
    antragsberechtigt: Optional[str] = Field(None, alias="Antragsberechtigt")
    antragsberechtigt_details: Optional[str] = Field(
        None, alias="Antragsberechtigt_Details"
    )
    andere_metadaten: Optional[str] = Field(None, alias="Andere_Metadaten")
    link: Optional[str] = Field(None, alias="Link")
    beschreibung: Optional[str] = Field(None, alias="Beschreibung")


class MatchResultModel(BaseModel):
    """
    Pydantic model representing a match result.
    """

    name: str
    url: str
    relevance: float
    justification: Optional[str] = None
    summary: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    org_type: Optional[str] = None
    employees_count: Optional[int] = None
    kmu_status: Optional[bool] = None


class PartnerModel(BaseModel):
    """
    Pydantic model for partners in a proposal.
    """

    name: str
    role: str


class MissingPartnerSearchModel(BaseModel):
    """
    Pydantic model for missing partner searches.
    """

    type_description: str
    filters: Dict[str, Any]
    queries: List[str]
    keywords: Optional[str] = None
    intended_role: str


class ProposalModel(BaseModel):
    """
    Pydantic model for a research project proposal.
    """

    title: str
    description: str
    existing_partners: List[PartnerModel]
    missing_partners_search: List[MissingPartnerSearchModel]
    newly_found_partners: List[MatchResultModel] = []

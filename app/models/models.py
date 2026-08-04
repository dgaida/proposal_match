import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompanyModel(BaseModel):
    """
    Pydantic model representing a company/organization.
    """

    @field_validator("summary", "products", mode="before")
    @classmethod
    def ensure_string(cls, v: Any) -> str | None:
        """
        Ensures that fields that should be strings are converted from list or dict if necessary.
        """
        if v is None:
            return None
        if isinstance(v, list):
            return "\n".join(str(item) for item in v)
        if isinstance(v, dict):
            return json.dumps(v, ensure_ascii=False)
        return str(v)

    name: str | None = None
    url: str
    state: str | None = None
    city: str | None = None
    employees_count: int | None = None
    kmu_status: bool | None = None
    industry: str | None = None
    country: str | None = None
    org_type: str | None = None
    research_active: bool | None = None
    summary: str | None = None
    products: str | None = None


class ResearchCallModel(BaseModel):
    """
    Pydantic model representing a research call.
    """

    @field_validator("antragsberechtigt", "andere_metadaten", mode="before")
    @classmethod
    def ensure_string(cls, v: Any) -> str | None:
        """
        Ensures that fields that should be strings are converted from list or dict if necessary.
        """
        if v is None:
            return None
        if isinstance(v, list):
            return "\n".join(str(item) for item in v)
        if isinstance(v, dict):
            return json.dumps(v, ensure_ascii=False)
        return str(v)

    model_config = ConfigDict(populate_by_name=True)

    thema: str = Field(alias="Thema")
    zielsetzung: str | None = Field(None, alias="Zielsetzung")
    deadline: str | None = Field(None, alias="Deadline")
    sitz_der_organisation: str | None = Field(None, alias="Sitz_der_Organisation")
    einstufig_zweistufig: str | None = Field(None, alias="Einstufig_Zweistufig")
    anzahl_projektpartner: str | None = Field(None, alias="Anzahl_Projektpartner")
    budget: str | None = Field(None, alias="Budget")
    laufzeit: str | None = Field(None, alias="Laufzeit")
    antragsberechtigt: str | None = Field(None, alias="Antragsberechtigt")
    antragsberechtigt_details: str | None = Field(
        None, alias="Antragsberechtigt_Details"
    )
    andere_metadaten: str | None = Field(None, alias="Andere_Metadaten")
    link: str | None = Field(None, alias="Link")
    beschreibung: str | None = Field(None, alias="Beschreibung")


class MatchResultModel(BaseModel):
    """
    Pydantic model representing a match result.
    """

    name: str
    url: str
    relevance: float
    justification: str | None = None
    summary: str | None = None
    industry: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    org_type: str | None = None
    employees_count: int | None = None
    kmu_status: bool | None = None


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
    filters: dict[str, Any]
    queries: list[str]
    keywords: str | None = None
    intended_role: str


class ProposalModel(BaseModel):
    """
    Pydantic model for a research project proposal.
    """

    title: str
    description: str
    existing_partners: list[PartnerModel]
    missing_partners_search: list[MissingPartnerSearchModel]
    newly_found_partners: list[MatchResultModel] = []

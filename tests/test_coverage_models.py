import json

from app.models.models import (
    CompanyModel,
    MatchResultModel,
    MissingPartnerSearchModel,
    PartnerModel,
    ProposalModel,
    ResearchCallModel,
)


def test_company_model_validation():
    # Test valid input
    comp = CompanyModel(
        name="Test Company",
        url="https://test.com",
        summary="Short summary",
        products=["product1", "product2"],
    )
    assert comp.name == "Test Company"
    assert comp.url == "https://test.com"
    assert comp.summary == "Short summary"
    assert comp.products == "product1\nproduct2"

    # Test None conversion
    comp2 = CompanyModel(url="https://test.com", summary=None, products=None)
    assert comp2.summary is None
    assert comp2.products is None

    # Test dict conversion
    dict_val = {"key": "value"}
    comp3 = CompanyModel(url="https://test.com", summary=dict_val, products=dict_val)
    expected_json = json.dumps(dict_val, ensure_ascii=False)
    assert comp3.summary == expected_json
    assert comp3.products == expected_json

    # Test arbitrary types (e.g. integer)
    comp4 = CompanyModel(url="https://test.com", summary=123)
    assert comp4.summary == "123"


def test_research_call_model_validation():
    # Test list validation on antragsberechtigt and andere_metadaten
    call = ResearchCallModel(
        Thema="AI Research",
        Antragsberechtigt=["Uni", "Company"],
        Andere_Metadaten={"flag": True},
    )
    assert call.thema == "AI Research"
    assert call.antragsberechtigt == "Uni\nCompany"
    assert call.andere_metadaten == json.dumps({"flag": True})

    # Test None and standard string
    call2 = ResearchCallModel(
        Thema="Data Science",
        Antragsberechtigt=None,
        Andere_Metadaten="Standard string",
    )
    assert call2.antragsberechtigt is None
    assert call2.andere_metadaten == "Standard string"


def test_other_models():
    # MatchResultModel
    m = MatchResultModel(
        name="Test Match",
        url="https://match.com",
        relevance=0.95,
        justification="Highly relevant",
    )
    assert m.name == "Test Match"
    assert m.relevance == 0.95

    # PartnerModel
    p = PartnerModel(name="Uni Kassel", role="Research Coordinator")
    assert p.name == "Uni Kassel"
    assert p.role == "Research Coordinator"

    # MissingPartnerSearchModel
    mps = MissingPartnerSearchModel(
        type_description="SME for pilot",
        filters={"state": "NRW"},
        queries=["SME pilot", "industrial partner"],
        intended_role="Pilot site",
    )
    assert mps.type_description == "SME for pilot"
    assert mps.filters == {"state": "NRW"}

    # ProposalModel
    prop = ProposalModel(
        title="Project Green",
        description="A green initiative",
        existing_partners=[p],
        missing_partners_search=[mps],
        newly_found_partners=[m],
    )
    assert prop.title == "Project Green"
    assert len(prop.existing_partners) == 1
    assert len(prop.missing_partners_search) == 1
    assert len(prop.newly_found_partners) == 1

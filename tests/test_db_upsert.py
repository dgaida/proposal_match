import os
from app.utils.db_manager import DBManager

def test_db_upsert():
    """
    Verifies that DBManager handles upsert logic and URL normalization.
    """
    db_path = os.path.abspath("data/test_upsert.db")
    db_url = f"sqlite:///{db_path}"
    if os.path.exists(db_path):
        os.remove(db_path)

    db_manager = DBManager(db_url=db_url)

    # 1. Add a company with trailing slash
    company1 = {
        "name": "Test Company",
        "url": "https://example.com/",
        "country": "Germany"
    }
    db_manager.add_company(company1)

    # 2. Verify it's saved without trailing slash
    companies = db_manager.get_all_companies()
    assert len(companies) == 1
    assert companies[0].url == "https://example.com"

    # 3. Add same company without trailing slash (should update)
    company2 = {
        "name": "Test Company Updated",
        "url": "https://example.com",
        "country": "Germany"
    }
    db_manager.add_company(company2)

    # 4. Verify still 1 company and name is updated
    companies = db_manager.get_all_companies()
    assert len(companies) == 1
    assert companies[0].name == "Test Company Updated"

    if os.path.exists(db_path):
        os.remove(db_path)

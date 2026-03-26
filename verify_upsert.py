import os
from app.utils.db_manager import DBManager

db_url = "sqlite:///data/test_upsert.db"
if os.path.exists("data/test_upsert.db"):
    os.remove("data/test_upsert.db")

db_manager = DBManager(db_url=db_url)

# 1. Add a company with trailing slash
company1 = {
    "name": "Test Company",
    "url": "https://example.com/",
    "country": "Germany"
}
db_manager.add_company(company1)
print("Added company 1 (with trailing slash)")

# 2. Verify it's saved without trailing slash
companies = db_manager.get_all_companies()
assert len(companies) == 1
assert companies[0].url == "https://example.com"
print("Verified company 1 url normalization")

# 3. Add same company without trailing slash (should update)
company2 = {
    "name": "Test Company Updated",
    "url": "https://example.com",
    "country": "Germany"
}
db_manager.add_company(company2)
print("Added company 2 (without trailing slash, same root)")

# 4. Verify still 1 company and name is updated
companies = db_manager.get_all_companies()
assert len(companies) == 1
assert companies[0].name == "Test Company Updated"
print("Verified upsert logic successful (no IntegrityError and data updated)")

os.remove("data/test_upsert.db")

<a id="app.utils.db_manager"></a>

# app.utils.db\_manager

<a id="app.utils.db_manager.Company"></a>

## Company Objects

```python
class Company(Base)
```

SQLAlchemy model representing a company/organization.

**Attributes**:

- `id` _int_ - Primary key.  
- `name` _str_ - The name of the organization.  
- `url` _str_ - The unique website URL.  
- `state` _str_ - Federal state.  
- `city` _str_ - City.  
- `employees_count` _int_ - Approximate number of employees.  
- `kmu_status` _bool_ - SME status.  
- `industry` _str_ - Industrial sector.  
- `country` _str_ - Country.  
- `org_type` _str_ - Type (e.g., SME, Research).  
- `research_active` _bool_ - Whether they do research.  
- `summary` _str_ - Textual description.  
- `products` _str_ - Description of products/services.  

<a id="app.utils.db_manager.DBManager"></a>

## DBManager Objects

```python
class DBManager()
```

Manages SQLite database operations for companies using SQLAlchemy.

**Attributes**:

- `engine` - SQLAlchemy engine.  
- `Session` - sessionmaker instance.  

<a id="app.utils.db_manager.DBManager.__init__"></a>

#### \_\_init\_\_

```python
def __init__(db_url: str = "sqlite:///data/companies.db")
```

Initializes the database connection and ensures schema exists.

**Arguments**:

- `db_url` _str_ - The database connection string.  

<a id="app.utils.db_manager.DBManager.add_company"></a>

#### add\_company

```python
def add_company(company_data: Dict[str, Any]) -> None
```

Adds a new company or updates an existing one by URL.

**Arguments**:

- `company_data` _Dict[str, Any]_ - Dictionary of company metadata.  

<a id="app.utils.db_manager.DBManager.get_all_companies"></a>

#### get\_all\_companies

```python
def get_all_companies() -> List[Company]
```

Retrieves all company records from the database.

**Returns**:

- `List[Company]` - List of SQLAlchemy Company objects.  

<a id="app.utils.db_manager.DBManager.deduplicate_companies"></a>

#### deduplicate\_companies

```python
def deduplicate_companies() -> int
```

Removes duplicate company entries based on normalized URLs.

**Returns**:

- `int` - The number of duplicates removed.  

<a id="app.utils.db_manager.DBManager.is_url_indexed"></a>

#### is\_url\_indexed

```python
def is_url_indexed(url: str) -> bool
```

Checks if a URL has already been indexed in the database.

**Arguments**:

- `url` _str_ - The URL to check.  


**Returns**:

- `bool` - True if it exists, False otherwise.  

<a id="app.utils.db_manager.DBManager.update_companies"></a>

#### update\_companies

```python
def update_companies(updated_data: List[Dict[str, Any]]) -> None
```

Performs a batch update of company records.

**Arguments**:

- `updated_data` _List[Dict[str, Any]]_ - List of company data dicts (must include 'url').  

from unittest.mock import MagicMock, patch
from app.services.fit_service import FITService

def test_fit_service_login():
    """
    Verifies that FITService can authenticate with Keycloak.
    """
    with patch("httpx.Client.post") as mock_post:
        # Arrange
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"access_token": "mock_token"}

        fit_service = FITService(llm_service=MagicMock())
        username = "test_user"
        password = "test_password"

        # Act
        success = fit_service.login(username, password)

        # Assert
        assert success is True
        assert fit_service.client.headers.get("Authorization") == "Bearer mock_token"
        print("FITService login test passed.")

def test_fit_service_search():
    """
    Verifies that FITService can search for calls.
    """
    with patch("httpx.Client.get") as mock_get:
        # Arrange
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"docs": [{"title": "Test Call", "description": "This is a test call."}]}

        fit_service = FITService(llm_service=MagicMock())
        query = "Test Query"

        # Act
        results = fit_service.search_calls(query)

        # Assert
        assert results is not None
        assert len(results) == 1
        assert results[0]["title"] == "Test Call"
        print("FITService search test passed.")

if __name__ == "__main__":
    test_fit_service_login()
    test_fit_service_search()

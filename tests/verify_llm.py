import os
import sys
from unittest.mock import patch

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.llm_service import LLMService


def test_llm_service_initialization():
    """
    Verifies that LLMService can be initialized with a given provider.
    """
    # Using MagicMock for LLMClient as actual API keys are not available
    with patch("app.services.llm_service.LLMClient") as MockLLMClient:
        # Arrange
        provider = "openai"
        api_key = "test_key"
        llm_model = "gpt-4"

        # Act
        _service = LLMService(provider=provider, api_key=api_key, llm_model=llm_model)

        # Assert
        MockLLMClient.assert_called_once_with(api_choice=provider, llm=llm_model)
        assert os.environ.get("OPENAI_API_KEY") == api_key
        print("LLMService initialization test passed.")


def test_llm_service_chat_completion():
    """
    Verifies that LLMService can send a chat completion request.
    """
    with patch("app.services.llm_service.LLMClient") as MockLLMClient:
        # Arrange
        mock_client_instance = MockLLMClient.return_value
        mock_client_instance.chat_completion.return_value = "Mocked Response"

        _service = LLMService(provider="openai", api_key="test_key")
        messages = [{"role": "user", "content": "Hello"}]

        # Act
        response = _service.chat_completion(messages)

        # Assert
        assert response == "Mocked Response"
        mock_client_instance.chat_completion.assert_called_once_with(messages)
        print("LLMService chat completion test passed.")


if __name__ == "__main__":
    test_llm_service_initialization()
    test_llm_service_chat_completion()

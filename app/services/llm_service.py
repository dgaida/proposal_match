import os
from collections.abc import Callable

from llm_client import LLMClient


class LLMService:
    """
    Service for interacting with various LLM providers using the LLMClient library.

    Attributes:
        provider (str): The current LLM provider being used.
        api_key (Optional[str]): The API key for the current provider.
        llm_model (Optional[str]): The specific model name being used.
        available_providers (Dict[str, str]): A dictionary of providers and their API keys.
        client (LLMClient): The instance of the LLMClient used for API calls.
    """

    def __init__(
        self,
        provider: str = "openai",
        api_key: str | None = None,
        llm_model: str | None = None,
    ):
        """
        Initializes the LLMService with a provider, API key, and model.

        Args:
            provider (str): The LLM provider to use (e.g., 'openai', 'groq', 'gemini').
            api_key (Optional[str]): The API key for the provider.
            llm_model (Optional[str]): The specific model name to use.
        """
        self.provider = provider
        self.api_key = api_key
        self.llm_model = llm_model

        # Available providers and their keys from environment
        self.available_providers = {}
        for p in ["openai", "groq", "gemini", "kiconnect"]:
            key = os.getenv(f"{p.upper()}_API_KEY")
            if key:
                self.available_providers[p] = key

        # Set environment variable for llm_client to pick up if provided
        if api_key:
            self.available_providers[provider] = api_key
            self._set_env_key(provider, api_key)

        self.client = (
            LLMClient(api_choice=provider, llm=llm_model, max_tokens=8192)
            if llm_model
            else LLMClient(api_choice=provider, max_tokens=8192)
        )

    def _set_env_key(self, provider: str, api_key: str) -> None:
        """
        Sets the appropriate environment variable for the given provider.

        Args:
            provider (str): The LLM provider name.
            api_key (str): The API key for the provider.
        """
        if provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider == "groq":
            os.environ["GROQ_API_KEY"] = api_key
        elif provider == "gemini":
            os.environ["GEMINI_API_KEY"] = api_key
        elif provider == "kiconnect":
            os.environ["KICONNECT_API_KEY"] = api_key

    def chat_completion(self, messages: list[dict[str, str]]) -> str:
        """
        Sends a chat completion request to the current LLM provider.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries (role and content).

        Returns:
            str: The text response from the LLM.
        """
        return self.client.chat_completion(messages)

    def chat_with_fallback(
        self,
        messages: list[dict[str, str]],
        status_callback: Callable[[str], None] | None = None,
    ) -> str:
        """
        Sends a chat completion request with fallback to other available providers on failure.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries.
            status_callback (Optional[Callable[[str], None]]): Optional callback for status updates.

        Returns:
            str: The text response from the LLM.

        Raises:
            Exception: If all available providers fail or no providers are configured.
        """
        # Start with the currently configured provider
        providers_to_try = [self.provider]
        # Add other available providers
        providers_to_try.extend(
            [p for p in self.available_providers if p != self.provider]
        )

        last_exception = None

        for i, p in enumerate(providers_to_try):
            try:
                if i > 0:  # If not the first attempt, we need to switch
                    if status_callback:
                        status_callback(
                            f"Switching to {p.capitalize()} due to error..."
                        )
                    self.switch_config(p, self.available_providers[p], llm_model=None)

                if status_callback:
                    model_info = f" ({self.llm_model})" if self.llm_model else ""
                    status_callback(
                        f"Analyzing with {self.provider.capitalize()}{model_info}..."
                    )

                return self.chat_completion(messages)
            except Exception as e:
                last_exception = e
                print(f"Provider {p} failed: {e}")
                continue

        if last_exception:
            raise last_exception
        raise Exception("No LLM providers available.")

    def extract_structured_data(
        self,
        text: str,
        prompt: str,
        status_callback: Callable[[str], None] | None = None,
    ) -> str:
        """
        Uses the LLM to extract structured information from the provided text.

        Args:
            text (str): The source text to extract data from.
            prompt (str): The specific extraction instructions.
            status_callback (Optional[Callable[[str], None]]): Optional callback for status updates.

        Returns:
            str: The extracted data, typically in JSON format as a string.
        """
        messages = [
            {
                "role": "system",
                "content": "You are an expert at extracting structured information from text. Always return valid JSON.",
            },
            {"role": "user", "content": f"{prompt}\n\nText:\n{text}"},
        ]
        return self.chat_with_fallback(messages, status_callback=status_callback)

    def switch_config(
        self, provider: str, api_key: str, llm_model: str | None = None
    ) -> None:
        """
        Dynamically switches the LLM provider, API key, and model.

        Args:
            provider (str): The new LLM provider name.
            api_key (str): The new API key.
            llm_model (Optional[str]): The new model name.
        """
        self.provider = provider
        self.api_key = api_key
        self.llm_model = llm_model

        self._set_env_key(provider, api_key)

        # Update the internal client
        self.client.switch_provider(api_choice=provider, llm=llm_model)

        # Some versions of LLMClient might not properly update the underlying client
        # when switching if keys are passed via env vars after init.
        # To be absolutely safe, we can re-initialize the internal client if needed,
        # but LLMClient.switch_provider is designed for this.

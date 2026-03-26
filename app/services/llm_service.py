import os
from typing import List, Dict, Optional, Callable
from llm_client import LLMClient

class LLMService:
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, llm_model: Optional[str] = None):
        """
        Initializes the LLMClient with the given provider and API key.
        """
        self.provider = provider
        self.api_key = api_key
        self.llm_model = llm_model

        # Available providers and their keys from environment
        self.available_providers = {}
        for p in ["openai", "groq", "gemini"]:
            key = os.getenv(f"{p.upper()}_API_KEY")
            if key:
                self.available_providers[p] = key

        # Set environment variable for llm_client to pick up if provided
        if api_key:
            self.available_providers[provider] = api_key
            self._set_env_key(provider, api_key)

        self.client = LLMClient(api_choice=provider, llm=llm_model, max_tokens=4096) if llm_model else LLMClient(api_choice=provider, max_tokens=4096)

    def _set_env_key(self, provider: str, api_key: str):
        if provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider == "groq":
            os.environ["GROQ_API_KEY"] = api_key
        elif provider == "gemini":
            os.environ["GEMINI_API_KEY"] = api_key

    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Sends a chat completion request to the LLM.
        """
        return self.client.chat_completion(messages)

    def chat_with_fallback(self, messages: List[Dict[str, str]], status_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Sends a chat completion request with fallback to other providers if the primary one fails.
        """
        # Start with the currently configured provider
        providers_to_try = [self.provider]
        # Add other available providers
        providers_to_try.extend([p for p in self.available_providers if p != self.provider])

        last_exception = None

        for i, p in enumerate(providers_to_try):
            try:
                if i > 0: # If not the first attempt, we need to switch
                    if status_callback:
                        status_callback(f"Switching to {p.capitalize()} due to error...")
                    self.switch_config(p, self.available_providers[p], llm_model=None)

                if status_callback:
                    model_info = f" ({self.llm_model})" if self.llm_model else ""
                    status_callback(f"Analyzing with {self.provider.capitalize()}{model_info}...")

                return self.chat_completion(messages)
            except Exception as e:
                last_exception = e
                print(f"Provider {p} failed: {e}")
                continue

        if last_exception:
            raise last_exception
        raise Exception("No LLM providers available.")

    def extract_structured_data(self, text: str, prompt: str, status_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Uses the LLM to extract structured data from the given text.
        """
        messages = [
            {"role": "system", "content": "You are an expert at extracting structured information from text. Always return valid JSON."},
            {"role": "user", "content": f"{prompt}\n\nText:\n{text}"}
        ]
        return self.chat_with_fallback(messages, status_callback=status_callback)

    def switch_config(self, provider: str, api_key: str, llm_model: Optional[str] = None):
        """
        Dynamically switches the LLM provider and API key.
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

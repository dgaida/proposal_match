import os
from typing import List, Dict, Optional
from llm_client import LLMClient

class LLMService:
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, llm_model: Optional[str] = None):
        """
        Initializes the LLMClient with the given provider and API key.
        """
        self.provider = provider
        self.api_key = api_key
        self.llm_model = llm_model

        # Set environment variable for llm_client to pick up if provided
        if api_key:
            if provider == "openai":
                os.environ["OPENAI_API_KEY"] = api_key
            elif provider == "groq":
                os.environ["GROQ_API_KEY"] = api_key
            elif provider == "gemini":
                os.environ["GEMINI_API_KEY"] = api_key

        self.client = LLMClient(api_choice=provider, llm=llm_model) if llm_model else LLMClient(api_choice=provider)

    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Sends a chat completion request to the LLM.
        """
        return self.client.chat_completion(messages)

    def extract_structured_data(self, text: str, prompt: str) -> str:
        """
        Uses the LLM to extract structured data from the given text.
        """
        messages = [
            {"role": "system", "content": "You are an expert at extracting structured information from text. Always return valid JSON."},
            {"role": "user", "content": f"{prompt}\n\nText:\n{text}"}
        ]
        return self.chat_completion(messages)

    def switch_config(self, provider: str, api_key: str, llm_model: Optional[str] = None):
        """
        Dynamically switches the LLM provider and API key.
        """
        self.provider = provider
        self.api_key = api_key

        if provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider == "groq":
            os.environ["GROQ_API_KEY"] = api_key
        elif provider == "gemini":
            os.environ["GEMINI_API_KEY"] = api_key

        self.client.switch_provider(api_choice=provider, llm=llm_model)

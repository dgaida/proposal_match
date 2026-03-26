import json
from typing import List, Dict, Any, Optional
from linkedin_api import Linkedin
from app.services.llm_service import LLMService

class LinkedInService:
    def __init__(self, llm_service: LLMService, username: Optional[str] = None, password: Optional[str] = None):
        self.llm_service = llm_service
        self.api = None
        if username and password:
            try:
                self.api = Linkedin(username, password)
            except Exception as e:
                print(f"Failed to initialize LinkedIn API: {e}")

    def get_first_degree_contacts(self) -> List[Dict[str, Any]]:
        """
        Fetches 1st-degree contacts from LinkedIn.
        """
        if not self.api:
            return []

        try:
            # Using search_people with network_depths=['F'] for 1st-degree contacts.
            connections = self.api.search_people(network_depths=['F'])
            return connections
        except Exception as e:
            print(f"Error fetching LinkedIn contacts: {e}")
            return []

    def generate_outreach_message(self, contact_name: str, company_name: str, call_data: Dict[str, Any]) -> str:
        """
        Generates a personalized outreach message using the LLM.
        """
        prompt = f"""
        Generate a professional and personalized LinkedIn outreach message for my contact {contact_name}
        who works at or is associated with {company_name}.
        I want to propose a collaboration for the following research call:
        {json.dumps(call_data)}

        The message should be brief, engaging, and encourage a follow-up meeting.
        """
        messages = [
            {"role": "system", "content": "You are a professional networker and research collaboration expert."},
            {"role": "user", "content": prompt}
        ]
        return self.llm_service.chat_completion(messages)

    def find_matching_contacts_for_call(self, contacts: List[Dict[str, Any]], call_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Uses the LLM to identify matching contacts for a given call from a list of contacts.
        """
        if not contacts:
            return []

        contact_list_str = "\n".join([f"- {c.get('firstName')} {c.get('lastName')} (Headline: {c.get('occupation')})" for c in contacts])

        prompt = f"""
        Identify the most relevant LinkedIn contacts from the list below for the following research call:
        Call: {json.dumps(call_data)}

        Contacts:
        {contact_list_str}

        Return the names of the top 5 matching contacts as a list.
        """

        messages = [
            {"role": "system", "content": "You are an expert at matching professionals to research opportunities."},
            {"role": "user", "content": prompt}
        ]

        response = self.llm_service.chat_completion(messages)
        # Simplified matching for the purpose of the app
        matched_names = [line.strip("- ").strip("12345. ") for line in response.splitlines() if line.strip()]

        # Filter the original contact list
        matches = []
        for contact in contacts:
            full_name = f"{contact.get('firstName')} {contact.get('lastName')}"
            if any(name in full_name for name in matched_names):
                matches.append(contact)

        return matches

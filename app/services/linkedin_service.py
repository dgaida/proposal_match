import json
from typing import List, Dict, Any, Optional, Callable
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

    def get_first_degree_contacts(self, limit: int = -1, status_callback: Optional[Callable[[str], None]] = None) -> List[Dict[str, Any]]:
        """
        Fetches 1st-degree contacts from LinkedIn.
        """
        if not self.api:
            if status_callback:
                status_callback("LinkedIn API not initialized. Check credentials.")
            return []

        try:
            if status_callback:
                status_callback("Fetching 1st-degree contacts from LinkedIn (this may take a while)...")
            print("LinkedIn: Fetching 1st-degree contacts...")

            # Using search_people with network_depths=['F'] for 1st-degree contacts.
            connections = self.api.search_people(network_depths=['F'], limit=limit)

            if status_callback:
                status_callback(f"Successfully fetched {len(connections)} contacts.")
            print(f"LinkedIn: Successfully fetched {len(connections)} contacts.")

            # Print contact names comma-separated
            contact_names = [f"{c.get('firstName')} {c.get('lastName')}" for c in connections]
            print(f"LinkedIn Contacts: {', '.join(contact_names)}")

            return connections
        except Exception as e:
            msg = f"Error fetching LinkedIn contacts: {e}"
            if status_callback:
                status_callback(msg)
            print(f"LinkedIn: {msg}")
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

    def find_matching_contacts_for_call(self, contacts: List[Dict[str, Any]], call_data: Dict[str, Any], status_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """
        Uses the LLM to identify matching contacts for a given call from a list of contacts.
        """
        if not contacts:
            return {"matches": [], "identified_names": [], "criteria": ""}

        try:
            if status_callback:
                status_callback(f"Analyzing {len(contacts)} contacts for matching with the research call...")
            print(f"LinkedIn: Analyzing {len(contacts)} contacts for matching...")

            contact_list_str = "\n".join([f"- {c.get('firstName')} {c.get('lastName')} (Headline: {c.get('occupation')})" for c in contacts])

            prompt = f"""
            Identify the most relevant LinkedIn contacts from the list below for the following research call.
            Also, provide a brief explanation of the criteria used for matching.

            Call: {json.dumps(call_data)}

            Contacts:
            {contact_list_str}

            Please format your response exactly as follows:
            Criteria: <Your explanation of the matching criteria>
            Names:
            - <First Name> <Last Name>
            - <First Name> <Last Name>
            ...
            """

            messages = [
                {"role": "system", "content": "You are an expert at matching professionals to research opportunities."},
                {"role": "user", "content": prompt}
            ]

            response = self.llm_service.chat_completion(messages)

            criteria = "No criteria provided."
            matched_names = []

            if "Criteria:" in response and "Names:" in response:
                parts = response.split("Names:")
                criteria_part = parts[0].replace("Criteria:", "").strip()
                names_part = parts[1].strip()
                criteria = criteria_part
                matched_names = [line.strip("- ").strip() for line in names_part.splitlines() if line.strip()]
            else:
                # Fallback to previous logic if LLM didn't follow instructions perfectly
                matched_names = [line.strip("- ").strip("12345. ") for line in response.splitlines() if line.strip()]

            if status_callback:
                status_callback(f"LLM identified {len(matched_names)} potential matches. Filtering list...")
            print(f"LinkedIn: LLM identified {len(matched_names)} potential matches.")

            # Filter the original contact list
            matches = []
            for contact in contacts:
                full_name = f"{contact.get('firstName')} {contact.get('lastName')}"
                if any(name in full_name for name in matched_names):
                    matches.append(contact)

            if status_callback:
                status_callback(f"Found {len(matches)} matching contacts.")
            print(f"LinkedIn: Found {len(matches)} matching contacts.")

            return {
                "matches": matches,
                "identified_names": matched_names,
                "criteria": criteria
            }
        except Exception as e:
            msg = f"Error during contact matching: {e}"
            if status_callback:
                status_callback(msg)
            print(f"LinkedIn: {msg}")
            return {"matches": [], "identified_names": [], "criteria": ""}

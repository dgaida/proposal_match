from unittest.mock import MagicMock
from app.services.linkedin_service import LinkedInService
from app.services.llm_service import LLMService

def test_linkedin_service_outreach():
    """
    Verifies that LinkedInService can generate a personalized outreach message.
    """
    # Arrange
    mock_llm_service = MagicMock(spec=LLMService)
    mock_llm_service.chat_completion.return_value = "Hello John, I'd like to collaborate on the Green Energy call."

    linkedin_service = LinkedInService(mock_llm_service)
    contact_name = "John Doe"
    company_name = "Energy Corp"
    call_data = {"Thema": "Green Energy", "Deadline": "2026-10-10"}

    # Act
    message = linkedin_service.generate_outreach_message(contact_name, company_name, call_data)

    # Assert
    assert "Hello John" in message
    assert "Green Energy" in message
    print("LinkedInService outreach test passed.")

def test_linkedin_service_matching():
    """
    Verifies that LinkedInService can identify matching contacts.
    """
    # Arrange
    mock_llm_service = MagicMock(spec=LLMService)
    mock_llm_service.chat_completion.return_value = "Criteria: Experts in AI.\nNames:\n- John Doe\n- Jane Smith"

    linkedin_service = LinkedInService(mock_llm_service)
    contacts = [
        {"firstName": "John", "lastName": "Doe", "occupation": "Researcher"},
        {"firstName": "Jane", "lastName": "Smith", "occupation": "Engineer"},
        {"firstName": "Bob", "lastName": "Brown", "occupation": "Sales"}
    ]
    call_data = {"Thema": "AI and Robotics"}

    # Act
    result = linkedin_service.find_matching_contacts_for_call(contacts, call_data)
    matches = result["matches"]
    identified_names = result["identified_names"]
    criteria = result["criteria"]

    # Assert
    assert len(matches) == 2
    assert matches[0]["firstName"] == "John"
    assert matches[1]["firstName"] == "Jane"
    assert "John Doe" in identified_names
    assert "Jane Smith" in identified_names
    assert criteria == "Experts in AI."
    print("LinkedInService matching test passed.")

if __name__ == "__main__":
    test_linkedin_service_outreach()
    test_linkedin_service_matching()

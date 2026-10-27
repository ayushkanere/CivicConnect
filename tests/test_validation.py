import pytest
from app.services.reports import validate_report_input, strip_html, ValidationError


def test_allowed_categories():
    """Valid categories pass; invalid category raises ValidationError."""
    valid_cat, desc, area = validate_report_input(
        "Garbage/Waste", 
        "Valid description with more than 10 characters.", 
        "Valid Area"
    )
    assert valid_cat == "Garbage/Waste"

    with pytest.raises(ValidationError, match="Invalid category selected"):
        validate_report_input("Unicorn/Magic", "Valid description for test.", "Valid Area")


def test_description_length_bounds():
    """Description < 10 chars or > 500 chars must be rejected."""
    # Too short (<10)
    with pytest.raises(ValidationError, match="between 10 and 500 characters"):
        validate_report_input("Garbage/Waste", "Too short", "Valid Area")

    # Too long (>500)
    long_desc = "a" * 501
    with pytest.raises(ValidationError, match="between 10 and 500 characters"):
        validate_report_input("Garbage/Waste", long_desc, "Valid Area")

    # Valid boundary (10 characters, non-phone)
    _, desc_10, _ = validate_report_input("Garbage/Waste", "ExactlyTen", "Valid Area")
    assert len(desc_10) == 10


def test_area_length_bounds():
    """Area < 3 chars or > 80 chars must be rejected."""
    # Too short (<3)
    with pytest.raises(ValidationError, match="between 3 and 80 characters"):
        validate_report_input("Garbage/Waste", "Valid description for test.", "AB")

    # Too long (>80)
    long_area = "A" * 81
    with pytest.raises(ValidationError, match="between 3 and 80 characters"):
        validate_report_input("Garbage/Waste", "Valid description for test.", long_area)


def test_html_stripping():
    """Verifies that HTML tags are stripped from description and area inputs."""
    raw = "<script>alert('xss')</script><b>Broken</b> light on <a href='bad'>pole</a>."
    cleaned = strip_html(raw)
    assert "<script>" not in cleaned
    assert "<b>" not in cleaned
    assert "<a" not in cleaned
    assert "Broken light on pole." in cleaned


def test_privacy_email_rejection():
    """Ensures emails are rejected to protect user privacy."""
    with pytest.raises(ValidationError, match="Privacy notice: Please do not include email addresses"):
        validate_report_input(
            "Broken Streetlight", 
            "Contact me at resident@example.com regarding streetlight.", 
            "Main Street"
        )


def test_privacy_phone_rejection():
    """Ensures phone numbers with 10+ digits are rejected."""
    with pytest.raises(ValidationError, match="Privacy notice: Please do not include phone numbers"):
        validate_report_input(
            "Broken Streetlight", 
            "Call me on 9876543210 for details about the streetlight.", 
            "Main Street"
        )

    # Street or pole numbers like "Pole #14" or "Sector 2" must NOT be falsely rejected
    _, desc, area = validate_report_input(
        "Broken Streetlight", 
        "Pole #14 flickering continuously after 8 PM along Sector 2.", 
        "Sector 2 North Gate"
    )
    assert "Pole #14" in desc


def test_honeypot_bot_rejection(client):
    """Verifies that bot filling the hidden honeypot field is rejected."""
    response = client.post("/report", data={
        "category": "Garbage/Waste",
        "description": "Legitimate looking description for testing bot trap.",
        "area": "Hostel Road Sector",
        "website_url": "http://spambot.com"  # Bot filled field!
    })
    assert response.status_code == 200
    assert b"Bot submission detected" in response.data

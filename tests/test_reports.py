from app.models import Report, StatusHistory
from app.services.reports import create_report


def test_sequential_report_id_generation(db_session):
    """Verifies that report IDs are generated in sequential zero-padded format: CC-001, CC-002..."""
    r1 = create_report("Garbage/Waste", "Test description 1 for sequence validation.", "Campus Sector A")
    assert r1.report_id == "CC-001"
    assert r1.status == "Submitted"
    assert r1.is_public is False

    r2 = create_report("Broken Streetlight", "Test description 2 for sequence validation.", "Campus Sector B")
    assert r2.report_id == "CC-002"

    r3 = create_report("Water Leakage/Drainage", "Test description 3 for sequence validation.", "Campus Sector C")
    assert r3.report_id == "CC-003"


def test_first_status_history_row(db_session):
    """Verifies that creating a report logs the initial status history row with Submitted status."""
    report = create_report("Garbage/Waste", "Test description for history row creation.", "North Campus Block")
    
    history_entries = StatusHistory.query.filter_by(report_id=report.report_id).all()
    assert len(history_entries) == 1
    
    first_entry = history_entries[0]
    assert first_entry.old_status is None
    assert first_entry.new_status == "Submitted"
    assert first_entry.updated_by is None  # Resident submission has no admin user ID
    assert first_entry.is_public_note is True
    assert "submitted" in first_entry.note.lower()


def test_report_form_submission_http(client, db_session):
    """Tests end-to-end HTTP submission of a report form and confirmation page display."""
    response = client.post("/report", data={
        "category": "Garbage/Waste",
        "description": "Garbage collection needed near Community Park with overflowing bins.",
        "area": "Community Park North Entrance",
        "website_url": ""  # Honeypot empty
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Report Received Successfully!" in response.data
    assert b"CC-001" in response.data
    assert b"Copy Report ID" in response.data
    assert b"Track This Report Now" in response.data

    # Check database state
    report = Report.query.get("CC-001")
    assert report is not None
    assert report.category == "Garbage/Waste"
    assert report.area == "Community Park North Entrance"
    assert report.status == "Submitted"

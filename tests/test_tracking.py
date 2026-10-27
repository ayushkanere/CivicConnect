from app.services.reports import create_report, update_report_status, add_report_note


def test_track_by_id_found_public(client, sample_reports):
    """Verifies that an approved public report can be looked up and displays its status timeline."""
    response = client.get("/track?id=CC-001")
    assert response.status_code == 200
    assert b"CC-001" in response.data
    assert b"Submitted" in response.data
    assert b"Progress & Verification Timeline" in response.data


def test_track_by_id_found_non_public(client, sample_reports):
    """Verifies that tracking works even if the report is not yet approved for the public directory."""
    # CC-005 has is_public=False in sample_reports
    response = client.get("/track?id=CC-005")
    assert response.status_code == 200
    assert b"CC-005" in response.data
    assert b"Under Review / Private" in response.data


def test_track_by_id_not_found(client, db_session):
    """Verifies friendly not found state when an invalid or nonexistent report ID is entered."""
    response = client.get("/track?id=CC-999")
    assert response.status_code == 200
    assert b"Report ID Not Found" in response.data
    assert b"CC-999" in response.data


def test_internal_notes_never_exposed_on_public_track(client, admin_user, db_session):
    """
    CRITICAL PRIVACY TEST:
    Ensures that internal admin notes are strictly hidden from the public tracking view.
    """
    report = create_report("Damaged Road/Unsafe Infrastructure", "Pothole near library gate.", "Library Gate")
    report.admin_note = "CONFIDENTIAL INTERNAL NOTE: Contractor contact details."
    
    # Add a private status note
    update_report_status(report, "Under Review", admin_user.user_id, note="INTERNAL ONLY: Team review in progress.", is_public_note=False)

    # Add a public status note
    update_report_status(report, "In Progress", admin_user.user_id, note="PUBLIC NOTE: Work scheduled for Monday.", is_public_note=True)
    
    db_session.commit()

    # Query public track endpoint
    response = client.get(f"/track?id={report.report_id}")
    assert response.status_code == 200

    # Public note SHOULD appear
    assert b"PUBLIC NOTE: Work scheduled for Monday." in response.data

    # Confidential note and private status note MUST NOT appear
    assert b"CONFIDENTIAL INTERNAL NOTE" not in response.data
    assert b"INTERNAL ONLY: Team review in progress." not in response.data

from app.models import Report, StatusHistory, CommunityEvent
from app.services.reports import create_report


def test_admin_login_success(client, admin_user):
    """Verifies successful admin authentication."""
    response = client.post("/admin/login", data={
        "email_or_name": "TestAdmin",
        "password": "AdminPass123!"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome back, TestAdmin!" in response.data
    assert b"Admin Panel" in response.data


def test_admin_login_invalid_credentials(client, admin_user):
    """Verifies that invalid credentials show a generic error message."""
    response = client.post("/admin/login", data={
        "email_or_name": "TestAdmin",
        "password": "WrongPassword999!"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid credentials" in response.data


def test_protected_admin_routes_redirect_unauthenticated(client):
    """Verifies that unauthorized requests to /admin routes redirect to login."""
    endpoints = [
        "/admin/",
        "/admin/reports",
        "/admin/reports/CC-001",
        "/admin/events"
    ]
    for url in endpoints:
        response = client.get(url)
        assert response.status_code == 302
        assert "/admin/login" in response.headers["Location"]


def test_status_update_resolved_requires_verification_note(client, admin_user, db_session):
    """
    CRITICAL QUALITY RULE:
    Changing status to 'Resolved' strictly requires a verification note.
    """
    # Authenticate admin
    client.post("/admin/login", data={"email_or_name": "TestAdmin", "password": "AdminPass123!"})

    report = create_report("Damaged Road/Unsafe Infrastructure", "Pothole for resolution test.", "Main Road")

    # 1. Attempt to set 'Resolved' without a verification note -> MUST FAIL
    fail_res = client.post(f"/admin/reports/{report.report_id}", data={
        "action": "update_status",
        "status-status": "Resolved",
        "status-note": "",  # Empty note!
        "status-is_public_note": "y"
    }, follow_redirects=True)
    
    assert b"verification note is required to mark a report as Resolved" in fail_res.data
    # Status should remain Submitted
    db_session.refresh(report)
    assert report.status == "Submitted"

    # 2. Provide a valid verification note -> MUST SUCCEED
    success_res = client.post(f"/admin/reports/{report.report_id}", data={
        "action": "update_status",
        "status-status": "Resolved",
        "status-note": "Verification Note: Volunteer team cold-patched pothole; area inspected and confirmed safe.",
        "status-is_public_note": "y"
    }, follow_redirects=True)

    assert b"Status successfully updated to &#39;Resolved&#39;" in success_res.data
    db_session.refresh(report)
    assert report.status == "Resolved"

    # Verify status history row was created
    history = StatusHistory.query.filter_by(report_id=report.report_id, new_status="Resolved").first()
    assert history is not None
    assert history.old_status == "Submitted"
    assert history.updated_by == admin_user.user_id
    assert "cold-patched pothole" in history.note


def test_mark_duplicate_workflow(client, admin_user, db_session):
    """Verifies marking a report as duplicate links it and hides it from the public directory."""
    client.post("/admin/login", data={"email_or_name": "TestAdmin", "password": "AdminPass123!"})

    primary = create_report("Garbage/Waste", "Primary waste pile report.", "Sector 1")
    primary.is_public = True

    duplicate = create_report("Garbage/Waste", "Duplicate waste pile report from another resident.", "Sector 1")
    duplicate.is_public = True
    db_session.commit()

    # Admin marks duplicate
    res = client.post(f"/admin/reports/{duplicate.report_id}", data={
        "action": "mark_duplicate",
        "dup-duplicate_of": primary.report_id
    }, follow_redirects=True)

    assert b"marked as duplicate" in res.data
    db_session.refresh(duplicate)
    assert duplicate.is_duplicate is True
    assert duplicate.duplicate_of == primary.report_id
    assert duplicate.is_public is False  # Must be removed from public listing


def test_community_event_management(client, admin_user, db_session):
    """Verifies that an admin can create and manage community events."""
    client.post("/admin/login", data={"email_or_name": "TestAdmin", "password": "AdminPass123!"})

    res = client.post("/admin/events", data={
        "title": "Weekend Lake Cleanup",
        "date": "2026-11-20T09:00",
        "location": "Lake Promenade East",
        "organizer": "Student Environmental Society",
        "description": "Join us for a 2-hour volunteer litter collection drive."
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Community event created successfully!" in res.data
    
    event = CommunityEvent.query.filter_by(title="Weekend Lake Cleanup").first()
    assert event is not None
    assert event.location == "Lake Promenade East"


def test_init_db_and_admin_from_env(app, monkeypatch, db_session):
    """Verifies that init_db_and_admin creates an admin account from env variables."""
    from app.services.auth import init_db_and_admin, authenticate_user
    from app.models import User

    monkeypatch.setenv("ADMIN_NAME", "CloudAdmin")
    monkeypatch.setenv("ADMIN_EMAIL", "cloud@civicconnect.local")
    monkeypatch.setenv("ADMIN_PASSWORD", "SuperCloudPass987!")

    init_db_and_admin(app)

    user = User.query.filter_by(name="CloudAdmin").first()
    assert user is not None
    assert user.email == "cloud@civicconnect.local"
    assert user.role == "admin"
    assert user.check_password("SuperCloudPass987!") is True

    # Check authentication
    authenticated = authenticate_user("CloudAdmin", "SuperCloudPass987!")
    assert authenticated is not None
    assert authenticated.user_id == user.user_id


def test_init_db_and_admin_does_not_reset_password_on_restart(app, monkeypatch, db_session):
    """Verifies that subsequent restarts do not overwrite or reset an existing admin's password."""
    from app.services.auth import init_db_and_admin
    from app.models import User

    # 1. First startup with initial password
    monkeypatch.setenv("ADMIN_NAME", "PersistentAdmin")
    monkeypatch.setenv("ADMIN_EMAIL", "persist@civicconnect.local")
    monkeypatch.setenv("ADMIN_PASSWORD", "OriginalPass123!")

    init_db_and_admin(app)
    user = User.query.filter_by(name="PersistentAdmin").first()
    assert user.check_password("OriginalPass123!") is True

    # 2. Simulate restarting app with a different environment password
    monkeypatch.setenv("ADMIN_PASSWORD", "AttemptedOverwrite999!")
    init_db_and_admin(app)

    # Password must NOT have been changed
    db_session.refresh(user)
    assert user.check_password("OriginalPass123!") is True
    assert user.check_password("AttemptedOverwrite999!") is False


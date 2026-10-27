import os
import shutil
import tempfile
import pytest
from app import create_app
from app.extensions import db as _db
from app.models import User, Report, StatusHistory, CommunityEvent
from app.services.reports import create_report, update_report_status


@pytest.fixture(scope="session")
def app():
    """Session-wide test Flask application."""
    temp_upload_dir = tempfile.mkdtemp()
    
    app = create_app("testing")
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "UPLOAD_FOLDER": temp_upload_dir,
        "WTF_CSRF_ENABLED": False,  # Simplified for unit testing
        "RATELIMIT_ENABLED": True,
        "RATELIMIT_STORAGE_URI": "memory://",
    })

    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

    shutil.rmtree(temp_upload_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def client(app):
    """Test HTTP client."""
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    """Provides a clean database state for each test function."""
    with app.app_context():
        _db.session.rollback()
        # Clean up tables
        StatusHistory.query.delete()
        Report.query.delete()
        CommunityEvent.query.delete()
        User.query.delete()
        _db.session.commit()
        yield _db.session
        _db.session.rollback()


@pytest.fixture(scope="function")
def admin_user(db_session):
    """Creates a test admin user."""
    user = User(
        name="TestAdmin",
        email="admin@test.local",
        role="admin"
    )
    user.set_password("AdminPass123!")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def sample_reports(db_session, admin_user):
    """Seeds a variety of sample reports across statuses and categories."""
    r1 = create_report(
        category="Garbage/Waste",
        description="Fictional test report 1: Garbage accumulation near cafeteria bin.",
        area="Cafeteria Perimeter"
    )
    r1.is_public = True
    
    r2 = create_report(
        category="Broken Streetlight",
        description="Fictional test report 2: Pole fixture dark at night.",
        area="Hostel Sector Road"
    )
    update_report_status(r2, "Under Review", admin_user.user_id, note="Inspected streetlight pole.")
    r2.is_public = True

    r3 = create_report(
        category="Water Leakage/Drainage",
        description="Fictional test report 3: Blocked rainwater runoff drain.",
        area="Main Sports Complex"
    )
    update_report_status(r3, "In Progress", admin_user.user_id, note="Volunteers assigned.")
    r3.is_public = True

    r4 = create_report(
        category="Damaged Road/Unsafe Infrastructure",
        description="Fictional test report 4: Pothole repaired with gravel cold mix.",
        area="South Entrance Gate"
    )
    update_report_status(r4, "Resolved", admin_user.user_id, note="Verification: Site patched and confirmed safe.")
    r4.is_public = True

    r5 = create_report(
        category="Other",
        description="Fictional test report 5: Private submission not yet approved.",
        area="Library Rear Garden"
    )
    r5.is_public = False  # Not public

    db_session.commit()
    return [r1, r2, r3, r4, r5]

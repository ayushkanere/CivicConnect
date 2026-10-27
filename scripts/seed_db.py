"""
CivicConnect - Database Seeder Utility
Populates the database with 12 clearly labelled FICTIONAL sample reports and 3 awareness events.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.extensions import db
from app.models import User, Report, StatusHistory, CommunityEvent


def seed_database():
    app = create_app()
    with app.app_context():
        db.create_all()

        # 1. Admin Account (if not present)
        admin = User.query.filter_by(name="Campus Admin").first()
        if not admin:
            admin = User(
                name="Campus Admin",
                email="admin@civicconnect.local",
                role="admin"
            )
            admin.set_password("AdminPass123!")
            db.session.add(admin)
            db.session.commit()
            print("[+] Created admin user: Campus Admin / AdminPass123!")
        else:
            print("[*] Admin user already exists.")

        # 2. 12 Fictional Reports
        sample_reports_data = [
            ("CC-001", "Garbage/Waste", "Garbage accumulation near South Gate bus shelter overflowing onto footpath.", "South Gate Campus Perimeter", "Submitted", True, False, False, None, False, "New resident submission awaiting team visit."),
            ("CC-002", "Broken Streetlight", "Pole #14 flickering continuously and dark after 8 PM along Hostel Road.", "Hostel Road East Sector", "Under Review", True, False, False, None, False, "Inspected by team volunteer; confirmed lamp unit issue."),
            ("CC-003", "Water Leakage/Drainage", "Stagnant rainwater and blocked storm drain causing foul smell near Cafeteria lane.", "Cafeteria Outer Lane", "In Progress", True, False, False, None, False, "Volunteer clean-up drive scheduled for this Saturday."),
            ("CC-004", "Damaged Road/Unsafe Infrastructure", "Large pothole at junction of 2nd Cross and Main Avenue causing two-wheelers to slip.", "2nd Cross Junction", "Resolved", True, False, False, None, False, "Verification Note: Community volunteer team patched spot with cold mix; site safe."),
            ("CC-005", "Community Cleanliness/Awareness", "Flyers and plastic bottles dumped along community playground green belt.", "Playground Boundary Green Belt", "In Progress", True, False, False, None, False, "Community cleanliness campaign planned with CEP volunteers."),
            ("CC-006", "Garbage/Waste", "Overflowing garbage bin near North Quadrangle Block B.", "North Quadrangle Block B", "Submitted", False, False, False, None, False, "Pending admin public approval."),
            ("CC-007", "Water Leakage/Drainage", "Potable water pipe joint dripping continuously near drinking water kiosk.", "Sports Complex Drinking Kiosk", "Resolved", True, False, False, None, False, "Verification Note: Campus plumbing lead replaced washer; verified no further leakage."),
            ("CC-008", "Broken Streetlight", "Two streetlights completely dark along pedestrian pathway near Library.", "Library Rear Walkway", "Under Review", True, False, False, None, False, "Reported to campus maintenance committee."),
            ("CC-009", "Damaged Road/Unsafe Infrastructure", "Broken pavement slab with exposed rebar posing tripping hazard.", "Science Block Promenade", "Under Review", True, False, False, None, False, "Marked with safety warning tape pending repair."),
            ("CC-010", "Garbage/Waste", "Duplicate report of South Gate bus shelter garbage dump.", "South Gate Bus Stop Area", "Under Review", False, False, True, "CC-001", False, "Flagged as duplicate of CC-001."),
            ("CC-011", "Other", "Loose overhead cable hanging low across community pathway.", "Engineering Annexe Pathway", "Submitted", True, False, False, None, False, "Checked by student safety monitor."),
            ("CC-012", "Community Cleanliness/Awareness", "Unregulated poster pasting on campus boundary wall.", "West Boundary Wall", "Resolved", True, False, False, None, False, "Verification Note: Cleaned up and awareness poster placed reminding residents to keep walls clean.")
        ]

        now = datetime.utcnow()
        for i, (r_id, cat, desc, area, status, is_pub, is_hid, is_dup, dup_of, photo_appr, note) in enumerate(sample_reports_data):
            existing = db.session.get(Report, r_id)
            if not existing:
                created_time = now - timedelta(days=12 - i, hours=i * 2)
                rep = Report(
                    report_id=r_id,
                    category=cat,
                    description=desc,
                    area=area,
                    status=status,
                    is_public=is_pub,
                    is_hidden=is_hid,
                    is_duplicate=is_dup,
                    duplicate_of=dup_of,
                    photo_approved=photo_appr,
                    admin_note=note,
                    created_at=created_time,
                    updated_at=created_time
                )
                db.session.add(rep)

                # Add initial StatusHistory
                hist = StatusHistory(
                    report_id=r_id,
                    old_status=None,
                    new_status="Submitted",
                    updated_by=None,
                    updated_at=created_time,
                    note="Report submitted by resident.",
                    is_public_note=True
                )
                db.session.add(hist)

                # Add status update history if progressed
                if status != "Submitted":
                    update_time = created_time + timedelta(hours=8)
                    hist2 = StatusHistory(
                        report_id=r_id,
                        old_status="Submitted",
                        new_status=status,
                        updated_by=admin.user_id,
                        updated_at=update_time,
                        note=note,
                        is_public_note=True
                    )
                    db.session.add(hist2)

        # 3. 3 Fictional Events
        events_data = [
            ("Campus Cleanliness Drive & Plastic Audit", "Join student volunteers for a 2-hour morning clean-up and single-use plastic waste audit around the student centre and lake promenade.", now + timedelta(days=5), "Student Centre Amphitheatre", "CEP Green Campus Initiative"),
            ("Community Water Conservation Workshop", "Interactive session on fixing domestic drip leaks, rooftop rainwater harvesting basics, and neighborhood drainage awareness.", now + timedelta(days=12), "Civic Hall Room 102", "Youth Water Action Team"),
            ("Pedestrian Safety & Infrastructure Walk", "Walk-through assessment of pedestrian crossings, lighting blind spots, and sidewalk accessibility with volunteer surveyors.", now + timedelta(days=18), "Main Gate Clock Tower", "CEP Safety & Mobility Group")
        ]

        for title, desc, dt, loc, org in events_data:
            existing = CommunityEvent.query.filter_by(title=title).first()
            if not existing:
                ev = CommunityEvent(
                    title=title,
                    description=desc,
                    date=dt,
                    location=loc,
                    organizer=org,
                    created_by=admin.user_id,
                    created_at=now
                )
                db.session.add(ev)

        db.session.commit()
        print("[+] Seeded 12 sample reports and 3 awareness events successfully.")


if __name__ == "__main__":
    seed_database()

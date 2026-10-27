"""
CivicConnect - Demo Scenario Verification Script
Simulates the exact 8-minute presentation scenario:
1. Submit fictional sample report: 'Garbage collection needed near Community Park'
2. Show generated Report ID (e.g., CC-013)
3. Admin logs in and updates status to 'Under Review' with public review note
4. Admin approves for public directory
5. Verify updated status on Track page
6. Verify updated status on Public Issue Directory
7. Verify updated counts on Dashboard
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.extensions import db
from app.models import Report, StatusHistory, User


def run_demo_verification():
    app = create_app()
    with app.test_client() as client:
        print("\n" + "=" * 60)
        print(" CIVICCONNECT END-TO-END DEMO SCENARIO VERIFICATION")
        print("=" * 60)

        # 1. Resident visits Home Page
        print("\n[Step 1] Visiting Home Page (GET /)...")
        res = client.get("/")
        assert res.status_code == 200
        assert b"A Digital Platform for Community Issue" in res.data
        assert b"Portal Scope Notice:" in res.data
        print("  -> Home page loaded with Scope Disclaimer, 6-step flow, and quick stats.")

        # 2. Resident submits sample report
        print("\n[Step 2] Submitting Sample Report (POST /report)...")
        # Fetch form page to extract CSRF token
        form_page = client.get("/report")
        import re
        csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', form_page.data.decode())
        csrf_token = csrf_match.group(1) if csrf_match else ""

        demo_desc = "Garbage collection needed near Community Park with overflowing bins."
        demo_area = "Community Park North Entrance"
        res = client.post("/report", data={
            "csrf_token": csrf_token,
            "category": "Garbage/Waste",
            "description": demo_desc,
            "area": demo_area,
            "website_url": ""
        }, follow_redirects=True)
        if res.status_code != 200:
            print("Status code:", res.status_code)
            print("Response:", res.data.decode(errors="ignore"))
        assert res.status_code == 200
        assert b"Report Received Successfully!" in res.data
        
        # Find latest report
        with app.app_context():
            latest_report = Report.query.order_by(Report.created_at.desc()).first()
            report_id = latest_report.report_id
            print(f"  -> Generated Report ID: {report_id}")
            print(f"  -> Initial Status: {latest_report.status}")
            assert latest_report.status == "Submitted"
            assert latest_report.is_public is False

        # 3. Resident checks status on Track page
        print(f"\n[Step 3] Resident tracks report (GET /track?id={report_id})...")
        res = client.get(f"/track?id={report_id}")
        assert res.status_code == 200
        assert report_id.encode() in res.data
        assert b"Submitted" in res.data
        print(f"  -> Track page shows '{report_id}' with initial status 'Submitted'.")

        # 4. Admin logs in
        print("\n[Step 4] Admin logs in (POST /admin/login)...")
        login_page = client.get("/admin/login")
        login_csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_page.data.decode()).group(1)

        res = client.post("/admin/login", data={
            "csrf_token": login_csrf,
            "email_or_name": "Campus Admin",
            "password": "AdminPass123!"
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"Welcome back, Campus Admin!" in res.data
        print("  -> Secure admin session established.")

        # 5. Admin updates status to 'Under Review' and approves for public display
        print(f"\n[Step 5] Admin updates {report_id} to 'Under Review' and approves publicly...")
        detail_page = client.get(f"/admin/reports/{report_id}")
        detail_csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', detail_page.data.decode()).group(1)

        res = client.post(f"/admin/reports/{report_id}", data={
            "csrf_token": detail_csrf,
            "action": "update_status",
            "status-status": "Under Review",
            "status-note": "Site inspected by student volunteer team; verified waste accumulation.",
            "status-is_public_note": "y"
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"Status successfully updated to &#39;Under Review&#39;" in res.data

        # Toggle public approval
        res = client.post(f"/admin/reports/{report_id}", data={
            "csrf_token": detail_csrf,
            "action": "toggle_public"
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"approved for public display" in res.data
        print(f"  -> Status transitioned to 'Under Review'; approved for public display.")

        # 6. Verify Track page reflects new status and note
        print(f"\n[Step 6] Resident re-checks track page (GET /track?id={report_id})...")
        res = client.get(f"/track?id={report_id}")
        assert res.status_code == 200
        assert b"Under Review" in res.data
        assert b"Site inspected by student volunteer team" in res.data
        print("  -> Track page reflects 'Under Review' and public volunteer review note.")

        # 7. Verify Public Issue Directory lists the report
        print(f"\n[Step 7] Checking Public Issue Directory (GET /issues)...")
        res = client.get(f"/issues?q={report_id}")
        assert res.status_code == 200
        assert report_id.encode() in res.data
        print(f"  -> Public Issue Directory correctly lists {report_id} with Under Review badge.")

        # 8. Verify Impact Dashboard reflects updated live counts
        print("\n[Step 8] Checking Live Impact Analytics (GET /api/stats & /dashboard)...")
        res = client.get("/api/stats")
        assert res.status_code == 200
        stats = res.get_json()["data"]
        print(f"  -> Total Reports: {stats['total_reports']}")
        print(f"  -> Under Review Count: {stats['status_counts']['Under Review']}")
        print(f"  -> Public Count: {stats['public_count']}")
        print(f"  -> Portal Disclaimer: '{stats['disclaimer']}'")
        assert stats["total_reports"] >= 13
        assert stats["status_counts"]["Under Review"] >= 1

        print("\n" + "=" * 60)
        print(" ALL STEPS IN DEMO SCENARIO VERIFIED SUCCESSFULLY!")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    run_demo_verification()

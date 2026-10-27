from app.services.reports import create_report


def test_xss_escaping_in_views(client, db_session):
    """
    Verifies that malicious scripts and HTML payloads in user inputs are escaped
    by Jinja autoescaping and cannot cause XSS execution.
    """
    malicious_desc = "<script>alert('xss_attack')</script> & pothole hazard"
    malicious_area = "Sector <img src=x onerror=alert('xss')> 4"
    
    report = create_report("Damaged Road/Unsafe Infrastructure", malicious_desc, malicious_area)
    report.is_public = True
    db_session.commit()

    # View on public track page
    track_res = client.get(f"/track?id={report.report_id}")
    assert track_res.status_code == 200
    # Raw unescaped script tag should NOT exist in output HTML
    assert b"<script>alert('xss_attack')</script>" not in track_res.data

    # View on public issues page
    issues_res = client.get("/issues")
    assert issues_res.status_code == 200
    assert b"<script>alert" not in issues_res.data

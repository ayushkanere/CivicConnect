from app.services.stats import get_impact_statistics
from app.models import Report


def test_impact_statistics_accuracy(sample_reports):
    """Verifies that get_impact_statistics computes accurate counts from database records."""
    stats = get_impact_statistics()

    assert stats["total_reports"] == len(sample_reports)  # 5 reports in fixture
    assert stats["status_counts"]["Submitted"] == 2
    assert stats["status_counts"]["Under Review"] == 1
    assert stats["status_counts"]["In Progress"] == 1
    assert stats["status_counts"]["Resolved"] == 1

    # Categories: Garbage/Waste, Broken Streetlight, Water Leakage/Drainage, Damaged Road/Unsafe Infrastructure, Other
    assert stats["category_counts"]["Garbage/Waste"] == 1
    assert stats["category_counts"]["Broken Streetlight"] == 1
    assert stats["category_counts"]["Water Leakage/Drainage"] == 1
    assert stats["category_counts"]["Damaged Road/Unsafe Infrastructure"] == 1
    assert stats["category_counts"]["Other"] == 1
    assert stats["category_counts"]["Community Cleanliness/Awareness"] == 0


def test_api_stats_endpoint(client, sample_reports):
    """Verifies that GET /api/stats returns status code 200 and expected schema."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    json_data = response.get_json()

    assert json_data["status"] == "success"
    data = json_data["data"]
    assert data["total_reports"] == 5
    assert "disclaimer" in data
    assert "Counts reflect reports on this portal, not confirmed official resolution." in data["disclaimer"]


def test_public_issue_list_and_api_filters(client, sample_reports):
    """Verifies that only public non-hidden reports appear in /issues and /api/issues."""
    # 4 of the 5 sample reports have is_public=True
    response = client.get("/api/issues")
    assert response.status_code == 200
    json_data = response.get_json()

    assert json_data["total_results"] == 4
    report_ids = [r["report_id"] for r in json_data["reports"]]
    assert "CC-001" in report_ids
    assert "CC-005" not in report_ids  # CC-005 is_public=False

    # Test category filter in API
    cat_res = client.get("/api/issues?category=Garbage/Waste")
    cat_data = cat_res.get_json()
    assert cat_data["total_results"] == 1
    assert cat_data["reports"][0]["report_id"] == "CC-001"

    # Test HTML view search filter
    html_res = client.get("/issues?q=cafeteria")
    assert html_res.status_code == 200
    assert b"CC-001" in html_res.data

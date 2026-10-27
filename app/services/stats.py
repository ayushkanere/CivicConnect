from typing import Dict, Any
from sqlalchemy import func
from app.extensions import db
from app.models import Report
from app.config import Config


def get_impact_statistics() -> Dict[str, Any]:
    """
    Computes live aggregates of community reports from saved records:
    - Total reports count
    - Counts by status (Submitted, Under Review, In Progress, Resolved)
    - Counts by category (all predefined categories initialized to 0)
    - Counts of public and duplicate reports
    """
    # 1. Total count
    total_reports = db.session.query(func.count(Report.report_id)).scalar() or 0

    # 2. Status counts
    status_counts = {status: 0 for status in Config.STATUSES}
    status_rows = (
        db.session.query(Report.status, func.count(Report.report_id))
        .group_by(Report.status)
        .all()
    )
    for status, count in status_rows:
        if status in status_counts:
            status_counts[status] = count
        else:
            status_counts[status] = count

    # 3. Category counts
    category_counts = {cat: 0 for cat in Config.CATEGORIES}
    category_rows = (
        db.session.query(Report.category, func.count(Report.report_id))
        .group_by(Report.category)
        .all()
    )
    for cat, count in category_rows:
        if cat in category_counts:
            category_counts[cat] = count
        else:
            category_counts[cat] = count

    # 4. Auxiliary metrics
    public_count = (
        db.session.query(func.count(Report.report_id))
        .filter(Report.is_public == True, Report.is_hidden == False)
        .scalar() or 0
    )
    duplicate_count = (
        db.session.query(func.count(Report.report_id))
        .filter(Report.is_duplicate == True)
        .scalar() or 0
    )

    # Resolution rate calculation (portal-internal measure only)
    resolution_rate = round((status_counts.get("Resolved", 0) / total_reports * 100), 1) if total_reports > 0 else 0.0

    return {
        "total_reports": total_reports,
        "status_counts": status_counts,
        "category_counts": category_counts,
        "public_count": public_count,
        "duplicate_count": duplicate_count,
        "resolution_rate": resolution_rate,
        "disclaimer": "Counts reflect reports on this portal, not confirmed official resolution."
    }

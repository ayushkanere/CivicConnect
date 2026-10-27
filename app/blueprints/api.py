from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from app.models import Report
from app.services.stats import get_impact_statistics
from app.config import Config

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/stats")
def stats():
    """Returns JSON live counts by status, category, and total impact metrics."""
    data = get_impact_statistics()
    return jsonify({
        "status": "success",
        "data": data
    }), 200


@api_bp.route("/issues")
def issues():
    """
    Returns JSON list of public reports with filters and pagination.
    Only returns records where is_public=1 and is_hidden=0.
    """
    query_str = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "").strip()
    selected_status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 50)

    query = Report.query.filter(Report.is_public == True, Report.is_hidden == False)

    if query_str:
        query = query.filter(
            or_(
                Report.report_id.ilike(f"%{query_str}%"),
                Report.description.ilike(f"%{query_str}%"),
                Report.area.ilike(f"%{query_str}%")
            )
        )

    if selected_category and selected_category in Config.CATEGORIES:
        query = query.filter(Report.category == selected_category)

    if selected_status and selected_status in Config.STATUSES:
        query = query.filter(Report.status == selected_status)

    query = query.order_by(Report.created_at.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "status": "success",
        "page": paginated.page,
        "per_page": paginated.per_page,
        "total_results": paginated.total,
        "total_pages": paginated.pages,
        "reports": [r.to_dict(is_admin=False) for r in paginated.items]
    }), 200

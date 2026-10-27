import os
from flask import (
    Blueprint, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    flash, 
    abort, 
    send_from_directory,
    current_app
)
from flask_login import current_user
from sqlalchemy import or_
from app.extensions import db, limiter
from app.models import Report, StatusHistory, CommunityEvent
from app.forms import ReportForm, TrackForm
from app.services.reports import create_report, ValidationError
from app.services.uploads import validate_and_save_photo, UploadValidationError
from app.services.stats import get_impact_statistics
from app.config import Config

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    """Home page with purpose, 6-step flow, CTAs, disclaimer, and quick statistics."""
    stats = get_impact_statistics()
    # Fetch 3 most recent public reports for live activity preview
    recent_reports = (
        Report.query.filter(Report.is_public == True, Report.is_hidden == False)
        .order_by(Report.created_at.desc())
        .limit(3)
        .all()
    )
    return render_template("public/home.html", stats=stats, recent_reports=recent_reports)


@public_bp.route("/report", methods=["GET", "POST"])
@limiter.limit("15/hour; 5/minute", methods=["POST"])
def report():
    """Public issue report form with client and server validation."""
    form = ReportForm()

    if form.validate_on_submit():
        photo_filename = None
        photo_file = request.files.get("photo")

        # Process optional photo
        if photo_file and photo_file.filename:
            try:
                photo_filename = validate_and_save_photo(
                    photo_file, 
                    current_app.config["UPLOAD_FOLDER"]
                )
            except UploadValidationError as e:
                flash(f"Photo upload error: {str(e)}", "danger")
                return render_template("public/report.html", form=form)

        # Create report in database
        try:
            new_report = create_report(
                category=form.category.data,
                description=form.description.data,
                area=form.area.data,
                photo_filename=photo_filename
            )
            flash("Your report has been successfully submitted for team review!", "success")
            return redirect(url_for("public.confirmation", report_id=new_report.report_id))
        except ValidationError as e:
            flash(str(e), "danger")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to submit report: {e}")
            flash("An unexpected error occurred while saving your report. Please try again.", "danger")

    return render_template("public/report.html", form=form)


@public_bp.route("/report/confirmation/<report_id>")
def confirmation(report_id):
    """Confirmation page with unique report ID, copy button, and track link."""
    report_obj = db.session.get(Report, report_id)
    if not report_obj:
        abort(404)
    return render_template("public/confirmation.html", report=report_obj)


@public_bp.route("/issues")
def issues():
    """
    Public issue list showing only approved, non-hidden reports.
    Supports keyword search, category filter, status filter, and pagination.
    """
    query_str = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "").strip()
    selected_status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 9  # Responsive 3x3 grid

    # Base query: Public and not hidden
    query = Report.query.filter(Report.is_public == True, Report.is_hidden == False)

    # Search filter by report ID, description, or area
    if query_str:
        search_filter = or_(
            Report.report_id.ilike(f"%{query_str}%"),
            Report.description.ilike(f"%{query_str}%"),
            Report.area.ilike(f"%{query_str}%")
        )
        query = query.filter(search_filter)

    # Category filter
    if selected_category and selected_category in Config.CATEGORIES:
        query = query.filter(Report.category == selected_category)

    # Status filter
    if selected_status and selected_status in Config.STATUSES:
        query = query.filter(Report.status == selected_status)

    # Order by newest first
    query = query.order_by(Report.created_at.desc())

    paginated_reports = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "public/issues.html",
        reports=paginated_reports.items,
        pagination=paginated_reports,
        categories=Config.CATEGORIES,
        statuses=Config.STATUSES,
        q=query_str,
        current_category=selected_category,
        current_status=selected_status
    )


@public_bp.route("/track", methods=["GET", "POST"])
@limiter.limit("30/minute")
def track():
    """
    Track a report by ID:
    - Works even if the report is not yet public.
    - Shows status progression timeline from status_history in chronological order.
    - Never exposes admin-only internal notes.
    """
    form = TrackForm()
    searched_id = request.args.get("id", "").strip().upper()
    searched_report = None
    not_found = False

    if request.method == "POST" and form.validate_on_submit():
        searched_id = form.report_id.data.strip().upper()
        return redirect(url_for("public.track", id=searched_id))

    if searched_id:
        form.report_id.data = searched_id
        searched_report = db.session.get(Report, searched_id)
        if not searched_report:
            not_found = True

    # Filter out non-public internal notes from status history
    public_history = []
    if searched_report:
        for entry in searched_report.history:
            if entry.is_public_note:
                public_history.append(entry)

    return render_template(
        "public/track.html",
        form=form,
        report=searched_report,
        history=public_history,
        searched_id=searched_id,
        not_found=not_found
    )


@public_bp.route("/dashboard")
def dashboard():
    """Impact summary / stats page with live Chart.js figures and numeric cards."""
    stats = get_impact_statistics()
    return render_template(
        "public/dashboard.html",
        stats=stats,
        categories=Config.CATEGORIES,
        statuses=Config.STATUSES
    )


@public_bp.route("/awareness")
def awareness():
    """Community awareness events, workshops, and volunteer cleanup announcements."""
    events = (
        CommunityEvent.query
        .order_by(CommunityEvent.date.asc())
        .all()
    )
    return render_template("public/awareness.html", events=events)


@public_bp.route("/guidelines")
def guidelines():
    """Community Guidelines page with reporting rules, privacy notice, and anti-abuse policies."""
    return render_template("public/guidelines.html")


@public_bp.route("/about")
def about():
    """About / Responsible Use page detailing the college CEP mission, boundaries, and disclaimer."""
    return render_template("public/about.html")


@public_bp.route("/uploads/<filename>")
def uploaded_file(filename):
    """
    Secure file serving endpoint for photos:
    - If user is logged-in admin, always serves.
    - If resident/visitor, only serves if the report is public and photo_approved=True.
    - Never executes files.
    """
    report_obj = Report.query.filter_by(photo_path=filename).first()
    if not report_obj:
        abort(404)

    is_authorized = current_user.is_authenticated or (report_obj.is_public and report_obj.photo_approved)
    if not is_authorized:
        abort(403)

    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)

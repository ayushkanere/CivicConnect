from urllib.parse import urlparse, urljoin
from datetime import datetime
from flask import (
    Blueprint, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    flash, 
    abort, 
    current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from app.extensions import db, limiter
from app.models import Report, StatusHistory, CommunityEvent
from app.forms import (
    AdminLoginForm, 
    AdminStatusUpdateForm, 
    AdminNoteForm, 
    AdminDuplicateForm,
    CommunityEventForm
)
from app.services.auth import authenticate_user
from app.services.reports import (
    update_report_status, 
    add_report_note, 
    mark_as_duplicate, 
    unmark_duplicate,
    ValidationError
)
from app.services.stats import get_impact_statistics
from app.config import Config

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def is_safe_url(target):
    """Ensures redirect target is on the same host to prevent open redirect vulnerabilities."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5/minute")
def login():
    """Secure rate-limited admin login with generic error messages."""
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = AdminLoginForm()
    if form.validate_on_submit():
        user = authenticate_user(form.email_or_name.data, form.password.data)
        if user and user.role == "admin":
            login_user(user, remember=False)
            flash(f"Welcome back, {user.name}!", "success")
            next_page = request.args.get("next")
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid credentials. Please verify your login details.", "danger")

    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Secure logout endpoint requiring CSRF-protected POST."""
    logout_user()
    flash("You have been securely logged out.", "info")
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@admin_bp.route("/reports")
@login_required
def dashboard():
    """
    Admin reports management dashboard:
    - Lists all submitted reports with pagination and filtering
    - Shows duplicate flags, moderation flags, and quick review status
    """
    query_str = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    category_filter = request.args.get("category", "").strip()
    flag_filter = request.args.get("flag", "").strip()  # 'duplicate', 'hidden', 'unapproved_public'
    page = request.args.get("page", 1, type=int)
    per_page = 15

    query = Report.query

    if query_str:
        query = query.filter(
            or_(
                Report.report_id.ilike(f"%{query_str}%"),
                Report.description.ilike(f"%{query_str}%"),
                Report.area.ilike(f"%{query_str}%")
            )
        )

    if status_filter and status_filter in Config.STATUSES:
        query = query.filter(Report.status == status_filter)

    if category_filter and category_filter in Config.CATEGORIES:
        query = query.filter(Report.category == category_filter)

    if flag_filter == "duplicate":
        query = query.filter(Report.is_duplicate == True)
    elif flag_filter == "hidden":
        query = query.filter(Report.is_hidden == True)
    elif flag_filter == "pending_approval":
        query = query.filter(Report.is_public == False)
    elif flag_filter == "unapproved_photo":
        query = query.filter(Report.photo_path != None, Report.photo_approved == False)

    query = query.order_by(Report.created_at.desc())
    paginated_reports = query.paginate(page=page, per_page=per_page, error_out=False)

    stats = get_impact_statistics()

    return render_template(
        "admin/dashboard.html",
        reports=paginated_reports.items,
        pagination=paginated_reports,
        stats=stats,
        categories=Config.CATEGORIES,
        statuses=Config.STATUSES,
        q=query_str,
        current_status=status_filter,
        current_category=category_filter,
        current_flag=flag_filter
    )


@admin_bp.route("/reports/<report_id>", methods=["GET", "POST"])
@login_required
def report_detail(report_id):
    """
    Admin detailed review for a specific report:
    - Change status (requires verification note if 'Resolved')
    - Add public note or internal note
    - Request clarification from reporter
    - Mark or unmark duplicate
    - Toggle public visibility
    - Toggle hidden content flag
    - Approve / hide photo
    """
    report = db.get_or_404(Report, report_id)

    status_form = AdminStatusUpdateForm(prefix="status")
    note_form = AdminNoteForm(prefix="note")
    duplicate_form = AdminDuplicateForm(prefix="dup")

    # Handle actions submitted via POST
    action = request.form.get("action")

    if request.method == "POST":
        try:
            if action == "update_status" and status_form.validate_on_submit():
                update_report_status(
                    report=report,
                    new_status=status_form.status.data,
                    admin_user_id=current_user.user_id,
                    note=status_form.note.data,
                    is_public_note=status_form.is_public_note.data
                )
                flash(f"Status successfully updated to '{status_form.status.data}'.", "success")
                return redirect(url_for("admin.report_detail", report_id=report.report_id))

            elif action == "add_note" and note_form.validate_on_submit():
                add_report_note(
                    report=report,
                    admin_user_id=current_user.user_id,
                    note=note_form.note.data,
                    is_public=note_form.is_public.data,
                    is_clarification=note_form.is_clarification.data
                )
                flash("Note recorded successfully.", "success")
                return redirect(url_for("admin.report_detail", report_id=report.report_id))

            elif action == "update_internal_note":
                raw_note = request.form.get("internal_note", "").strip()
                report.admin_note = raw_note
                report.updated_at = datetime.utcnow()
                db.session.commit()
                flash("Internal administrative note saved.", "success")
                return redirect(url_for("admin.report_detail", report_id=report.report_id))

            elif action == "mark_duplicate" and duplicate_form.validate_on_submit():
                mark_as_duplicate(
                    report=report,
                    target_report_id=duplicate_form.duplicate_of.data,
                    admin_user_id=current_user.user_id
                )
                flash(f"Report marked as duplicate of {duplicate_form.duplicate_of.data}.", "warning")
                return redirect(url_for("admin.report_detail", report_id=report.report_id))

            elif action == "unmark_duplicate":
                unmark_duplicate(report=report, admin_user_id=current_user.user_id)
                flash("Duplicate flag removed.", "success")
                return redirect(url_for("admin.report_detail", report_id=report.report_id))

            elif action == "toggle_public":
                report.is_public = not report.is_public
                report.updated_at = datetime.utcnow()
                db.session.commit()
                status_label = "approved for public display" if report.is_public else "hidden from public directory"
                flash(f"Report is now {status_label}.", "info")
                return redirect(url_for("admin.report_detail", report_id=report.report_id))

            elif action == "toggle_hidden":
                report.is_hidden = not report.is_hidden
                report.updated_at = datetime.utcnow()
                db.session.commit()
                status_label = "flagged and hidden as unsuitable content" if report.is_hidden else "unhidden"
                flash(f"Report has been {status_label}.", "warning")
                return redirect(url_for("admin.report_detail", report_id=report.report_id))

            elif action == "toggle_photo_approval":
                report.photo_approved = not report.photo_approved
                report.updated_at = datetime.utcnow()
                db.session.commit()
                status_label = "approved for public viewing" if report.photo_approved else "hidden from public view"
                flash(f"Report photo is now {status_label}.", "info")
                return redirect(url_for("admin.report_detail", report_id=report.report_id))

        except ValidationError as e:
            flash(str(e), "danger")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Admin action error on {report_id}: {e}")
            flash(f"Action failed: {str(e)}", "danger")

    # Prepopulate forms for GET
    status_form.status.data = report.status
    if report.duplicate_of:
        duplicate_form.duplicate_of.data = report.duplicate_of

    return render_template(
        "admin/report_detail.html",
        report=report,
        status_form=status_form,
        note_form=note_form,
        duplicate_form=duplicate_form,
        history=report.history
    )


@admin_bp.route("/events", methods=["GET", "POST"])
@login_required
def events():
    """List and create community awareness events."""
    form = CommunityEventForm()
    if form.validate_on_submit():
        new_event = CommunityEvent(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            date=form.date.data,
            location=form.location.data.strip(),
            organizer=form.organizer.data.strip(),
            created_by=current_user.user_id
        )
        db.session.add(new_event)
        db.session.commit()
        flash("Community event created successfully!", "success")
        return redirect(url_for("admin.events"))

    all_events = CommunityEvent.query.order_by(CommunityEvent.date.desc()).all()
    return render_template("admin/events.html", events=all_events, form=form)


@admin_bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(event_id):
    """Edit an existing community awareness event."""
    event = db.get_or_404(CommunityEvent, event_id)
    form = CommunityEventForm(obj=event)

    if form.validate_on_submit():
        event.title = form.title.data.strip()
        event.description = form.description.data.strip()
        event.date = form.date.data
        event.location = form.location.data.strip()
        event.organizer = form.organizer.data.strip()
        db.session.commit()
        flash("Event updated successfully.", "success")
        return redirect(url_for("admin.events"))

    return render_template("admin/event_form.html", form=form, event=event)


@admin_bp.route("/events/<int:event_id>/delete", methods=["POST"])
@login_required
def delete_event(event_id):
    """Delete a community awareness event."""
    event = db.get_or_404(CommunityEvent, event_id)
    db.session.delete(event)
    db.session.commit()
    flash(f"Event '{event.title}' deleted.", "info")
    return redirect(url_for("admin.events"))

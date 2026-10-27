import re
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy import func
from app.extensions import db
from app.models import Report, StatusHistory
from app.config import Config

# Regex patterns for privacy protection
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", 
    re.IGNORECASE
)
# Matches 10+ digit phone numbers with optional country code, dashes, dots, spaces, or parentheses
PHONE_PATTERN = re.compile(
    r"(?:(?:\+|00)\d{1,3}[-.\s]*)?(?:\(?\d{2,5}\)?[-.\s]*)?\d{3,4}[-.\s]*\d{3,4}\b"
)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


class ValidationError(Exception):
    """Raised when report input fails validation."""
    pass


def strip_html(text: str) -> str:
    """Removes HTML tags from input string."""
    if not text:
        return ""
    return HTML_TAG_PATTERN.sub("", text)


def validate_report_input(category: str, description: str, area: str) -> Tuple[str, str, str]:
    """
    Validates report form inputs according to civic specification:
    - Checks category against allowed list
    - Trims whitespace and strips HTML
    - Validates character bounds (description: 10-500, area: 3-80)
    - Rejects personal data patterns (emails, phone numbers) for privacy protection
    """
    if not category or category not in Config.CATEGORIES:
        raise ValidationError(f"Invalid category selected. Must be one of: {', '.join(Config.CATEGORIES)}.")

    # Strip HTML and trim whitespace
    cleaned_desc = strip_html(description or "").strip()
    cleaned_area = strip_html(area or "").strip()

    # Reject empty or whitespace-only
    if not cleaned_desc:
        raise ValidationError("Description cannot be empty.")
    if not cleaned_area:
        raise ValidationError("Area / locality cannot be empty.")

    # Bounds validation
    if len(cleaned_desc) < 10 or len(cleaned_desc) > 500:
        raise ValidationError(
            f"Description must be between 10 and 500 characters (currently {len(cleaned_desc)})."
        )
    if len(cleaned_area) < 3 or len(cleaned_area) > 80:
        raise ValidationError(
            f"Area / locality must be between 3 and 80 characters (currently {len(cleaned_area)})."
        )

    # Privacy Protection: Check for emails
    if EMAIL_PATTERN.search(cleaned_desc) or EMAIL_PATTERN.search(cleaned_area):
        raise ValidationError(
            "Privacy notice: Please do not include email addresses in your report description or area."
        )

    # Privacy Protection: Check for phone numbers
    # Filter out small numbers like street numbers or pole numbers (e.g. 'Pole #14', 'Street 2')
    phone_match_desc = PHONE_PATTERN.search(cleaned_desc)
    phone_match_area = PHONE_PATTERN.search(cleaned_area)
    if phone_match_desc:
        digits_only = re.sub(r"\D", "", phone_match_desc.group())
        if len(digits_only) >= 10:
            raise ValidationError(
                "Privacy notice: Please do not include phone numbers in your report description."
            )
    if phone_match_area:
        digits_only = re.sub(r"\D", "", phone_match_area.group())
        if len(digits_only) >= 10:
            raise ValidationError(
                "Privacy notice: Please do not include phone numbers in the area / locality."
            )

    return category, cleaned_desc, cleaned_area


def generate_next_report_id() -> str:
    """
    Safely generates the next sequential zero-padded report ID (e.g., CC-001, CC-002).
    Extracts all numeric suffixes from existing IDs to prevent collisions.
    """
    existing_ids = db.session.query(Report.report_id).all()
    max_num = 0
    for (r_id,) in existing_ids:
        if r_id and r_id.startswith("CC-"):
            suffix = r_id[3:]
            if suffix.isdigit():
                max_num = max(max_num, int(suffix))

    next_num = max_num + 1
    return f"CC-{next_num:03d}"


def create_report(category: str, description: str, area: str, photo_filename: Optional[str] = None) -> Report:
    """
    Creates a new community report:
    - Validates inputs
    - Assigns next sequential report_id
    - Sets initial status to 'Submitted'
    - Creates initial StatusHistory record
    """
    cat, desc, loc = validate_report_input(category, description, area)

    # Generate next ID
    report_id = generate_next_report_id()

    report = Report(
        report_id=report_id,
        category=cat,
        description=desc,
        area=loc,
        photo_path=photo_filename,
        status="Submitted",
        is_public=False,  # Unapproved by default per specification
        is_hidden=False,
        is_duplicate=False,
        photo_approved=False,
        admin_note=None
    )
    db.session.add(report)

    # Create initial status history entry
    first_history = StatusHistory(
        report_id=report_id,
        old_status=None,
        new_status="Submitted",
        updated_by=None,  # Resident submission
        note="Report submitted by resident.",
        is_public_note=True
    )
    db.session.add(first_history)
    db.session.commit()

    return report


def update_report_status(
    report: Report, 
    new_status: str, 
    admin_user_id: int, 
    note: Optional[str] = None, 
    is_public_note: bool = True
) -> Report:
    """
    Updates the status of a report:
    - Validates status transition
    - Requires verification note if new status is 'Resolved'
    - Appends an entry to status_history
    """
    if new_status not in Config.STATUSES:
        raise ValidationError(f"Invalid status '{new_status}'. Allowed: {', '.join(Config.STATUSES)}.")

    note_clean = strip_html(note or "").strip()

    # Rule: Resolved requires a verification note
    if new_status == "Resolved" and not note_clean:
        raise ValidationError("A verification note is required to mark a report as Resolved.")

    old_status = report.status
    if old_status != new_status:
        report.status = new_status
        report.updated_at = datetime.utcnow()

    history_entry = StatusHistory(
        report_id=report.report_id,
        old_status=old_status,
        new_status=new_status,
        updated_by=admin_user_id,
        note=note_clean if note_clean else f"Status updated to {new_status}.",
        is_public_note=is_public_note
    )
    db.session.add(history_entry)
    db.session.commit()

    return report


def add_report_note(
    report: Report, 
    admin_user_id: int, 
    note: str, 
    is_public: bool = True,
    is_clarification: bool = False
) -> StatusHistory:
    """Adds a public update note or clarification request without altering the status."""
    clean_note = strip_html(note or "").strip()
    if not clean_note:
        raise ValidationError("Note content cannot be empty.")

    if is_clarification:
        prefix = "Clarification Requested: "
        if not clean_note.startswith(prefix):
            clean_note = prefix + clean_note

    history_entry = StatusHistory(
        report_id=report.report_id,
        old_status=report.status,
        new_status=report.status,
        updated_by=admin_user_id,
        note=clean_note,
        is_public_note=is_public
    )
    db.session.add(history_entry)
    report.updated_at = datetime.utcnow()
    db.session.commit()
    return history_entry


def mark_as_duplicate(report: Report, target_report_id: str, admin_user_id: int) -> Report:
    """Marks a report as a duplicate of an existing report."""
    target_id_clean = target_report_id.strip()
    if target_id_clean == report.report_id:
        raise ValidationError("A report cannot be marked as a duplicate of itself.")

    target = db.session.get(Report, target_id_clean)
    if not target:
        raise ValidationError(f"Referenced report ID '{target_id_clean}' does not exist.")

    report.is_duplicate = True
    report.duplicate_of = target.report_id
    report.is_public = False  # Hide duplicate from public list
    report.updated_at = datetime.utcnow()

    history = StatusHistory(
        report_id=report.report_id,
        old_status=report.status,
        new_status=report.status,
        updated_by=admin_user_id,
        note=f"Flagged as duplicate of {target.report_id}.",
        is_public_note=False
    )
    db.session.add(history)
    db.session.commit()
    return report


def unmark_duplicate(report: Report, admin_user_id: int) -> Report:
    """Removes the duplicate flag from a report."""
    old_target = report.duplicate_of
    report.is_duplicate = False
    report.duplicate_of = None
    report.updated_at = datetime.utcnow()

    history = StatusHistory(
        report_id=report.report_id,
        old_status=report.status,
        new_status=report.status,
        updated_by=admin_user_id,
        note=f"Removed duplicate flag (previously linked to {old_target}).",
        is_public_note=False
    )
    db.session.add(history)
    db.session.commit()
    return report

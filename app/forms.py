from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, 
    TextAreaField, 
    SelectField, 
    PasswordField, 
    BooleanField, 
    SubmitField,
    DateTimeLocalField
)
from wtforms.validators import (
    DataRequired, 
    Length, 
    Optional as WtOptional, 
    ValidationError as WtValidationError
)
from app.config import Config


class ReportForm(FlaskForm):
    """Public issue report submission form."""
    category = SelectField(
        "Issue Category",
        choices=[("", "-- Select an Issue Category --")] + [(c, c) for c in Config.CATEGORIES],
        validators=[DataRequired(message="Please select an issue category.")]
    )
    description = TextAreaField(
        "Description",
        validators=[
            DataRequired(message="Please enter a description."),
            Length(min=10, max=500, message="Description must be between 10 and 500 characters.")
        ],
        render_kw={
            "rows": 4, 
            "placeholder": "Describe what you observed (e.g., location marker, depth of pothole, duration of issue)...",
            "maxlength": 500
        }
    )
    area = StringField(
        "Area / Locality",
        validators=[
            DataRequired(message="Please enter the general area or neighborhood."),
            Length(min=3, max=80, message="Area must be between 3 and 80 characters.")
        ],
        render_kw={
            "placeholder": "e.g., South Gate Bus Shelter, Hostel Road Sector B",
            "maxlength": 80
        }
    )
    photo = FileField(
        "Photo (Optional, max 2 MB)",
        validators=[
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Only JPG, JPEG, PNG, and WEBP images are allowed.")
        ]
    )
    # Anti-bot honeypot field (hidden via CSS; bots will fill it, legitimate users won't)
    website_url = StringField("Leave blank", validators=[WtOptional()])

    def validate_website_url(self, field):
        if field.data:
            raise WtValidationError("Bot submission detected.")


class TrackForm(FlaskForm):
    """Lookup form for tracking a report by ID."""
    report_id = StringField(
        "Report ID",
        validators=[
            DataRequired(message="Please enter a Report ID (e.g., CC-001)."),
            Length(min=3, max=20, message="Report ID format is invalid.")
        ],
        render_kw={"placeholder": "e.g., CC-001", "autocomplete": "off"}
    )
    submit = SubmitField("Track Progress")


class AdminLoginForm(FlaskForm):
    """Admin credentials login form."""
    email_or_name = StringField(
        "Username or Email",
        validators=[DataRequired(message="Username or email is required.")],
        render_kw={"placeholder": "admin or admin@civicconnect.local", "autocomplete": "username"}
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password is required.")],
        render_kw={"placeholder": "••••••••••••", "autocomplete": "current-password"}
    )
    submit = SubmitField("Secure Admin Login")


class AdminStatusUpdateForm(FlaskForm):
    """Form for administrators to progress report status."""
    status = SelectField(
        "Update Status",
        choices=[(s, s) for s in Config.STATUSES],
        validators=[DataRequired()]
    )
    note = TextAreaField(
        "Status Update Note / Verification Note",
        validators=[WtOptional(), Length(max=1000)],
        render_kw={"rows": 3, "placeholder": "Explain the change or state verification details (Required for 'Resolved')..."}
    )
    is_public_note = BooleanField("Make this note visible on the public tracker", default=True)
    submit = SubmitField("Apply Status Change")


class AdminNoteForm(FlaskForm):
    """Form to add an ad-hoc note or request clarification from the reporter."""
    note = TextAreaField(
        "Note Message",
        validators=[DataRequired(message="Note cannot be empty."), Length(max=1000)],
        render_kw={"rows": 3, "placeholder": "Enter update message or clarification question..."}
    )
    is_public = BooleanField("Visible on Public Track Timeline", default=True)
    is_clarification = BooleanField("Mark as 'Clarification Requested' banner", default=False)
    submit = SubmitField("Post Note")


class AdminDuplicateForm(FlaskForm):
    """Form to link a duplicate report to an existing primary report."""
    duplicate_of = StringField(
        "Target Report ID",
        validators=[DataRequired(message="Please provide the original Report ID."), Length(max=20)],
        render_kw={"placeholder": "e.g., CC-001"}
    )
    submit = SubmitField("Flag as Duplicate")


class CommunityEventForm(FlaskForm):
    """Form for managing community awareness campaigns and events."""
    title = StringField(
        "Event Title",
        validators=[DataRequired(), Length(min=3, max=150)],
        render_kw={"placeholder": "e.g., Community Cleanliness Drive & Plastic Audit"}
    )
    description = TextAreaField(
        "Event Description",
        validators=[DataRequired(), Length(min=10, max=2000)],
        render_kw={"rows": 4, "placeholder": "Provide details on purpose, meeting point, and what volunteers should bring..."}
    )
    date = DateTimeLocalField(
        "Date and Time",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired(message="Please select a valid date and time (YYYY-MM-DD HH:MM).")],
        render_kw={"type": "datetime-local"}
    )
    location = StringField(
        "Location",
        validators=[DataRequired(), Length(min=3, max=150)],
        render_kw={"placeholder": "e.g., Student Centre Amphitheatre"}
    )
    organizer = StringField(
        "Organizer / Initiative",
        validators=[DataRequired(), Length(min=2, max=100)],
        render_kw={"placeholder": "e.g., CEP Green Campus Initiative"}
    )
    submit = SubmitField("Save Event")

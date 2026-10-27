from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    """Admin user account for reviewing and managing reports."""
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="admin")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    history_entries = db.relationship("StatusHistory", backref="updater", lazy="dynamic", foreign_keys="StatusHistory.updated_by")
    created_events = db.relationship("CommunityEvent", backref="author", lazy="dynamic", foreign_keys="CommunityEvent.created_by")

    def get_id(self):
        return str(self.user_id)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.user_id}: {self.name} ({self.role})>"


class Report(db.Model):
    """Community issue report submitted by a resident."""
    __tablename__ = "reports"

    report_id = db.Column(db.String(20), primary_key=True)  # e.g., 'CC-001'
    category = db.Column(db.String(60), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    area = db.Column(db.String(100), nullable=False)
    photo_path = db.Column(db.String(255), nullable=True)
    status = db.Column(
        db.String(50), 
        nullable=False, 
        default="Submitted", 
        index=True
    )  # 'Submitted', 'Under Review', 'In Progress', 'Resolved'
    is_public = db.Column(db.Boolean, nullable=False, default=False)
    is_hidden = db.Column(db.Boolean, nullable=False, default=False)
    is_duplicate = db.Column(db.Boolean, nullable=False, default=False)
    duplicate_of = db.Column(
        db.String(20), 
        db.ForeignKey("reports.report_id", ondelete="SET NULL"), 
        nullable=True
    )
    photo_approved = db.Column(db.Boolean, nullable=False, default=False)
    admin_note = db.Column(db.Text, nullable=True)  # Strictly internal notes
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(
        db.DateTime, 
        nullable=False, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )

    # Composite index on is_public and is_hidden for fast public query
    __table_args__ = (
        db.Index("idx_reports_public_hidden", "is_public", "is_hidden"),
    )

    # Relationships
    history = db.relationship(
        "StatusHistory", 
        backref="report", 
        lazy="joined", 
        cascade="all, delete-orphan",
        order_by="StatusHistory.updated_at.asc()"
    )
    duplicate_parent = db.relationship(
        "Report", 
        remote_side=[report_id], 
        backref=db.backref("child_duplicates", lazy="dynamic")
    )

    def to_dict(self, is_admin: bool = False) -> dict:
        """Serialize report data safely based on viewer role."""
        data = {
            "report_id": self.report_id,
            "category": self.category,
            "description": self.description,
            "area": self.area,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
            "is_public": self.is_public,
            "is_duplicate": self.is_duplicate,
            "photo_available": bool(self.photo_path and (is_admin or self.photo_approved)),
        }
        
        # Public photo only shown if photo_approved is True (or viewer is admin)
        if self.photo_path and (is_admin or self.photo_approved):
            data["photo_url"] = f"/uploads/{self.photo_path}"
        else:
            data["photo_url"] = None

        if is_admin:
            data["is_hidden"] = self.is_hidden
            data["duplicate_of"] = self.duplicate_of
            data["photo_approved"] = self.photo_approved
            data["admin_note"] = self.admin_note
            
        return data

    def __repr__(self):
        return f"<Report {self.report_id}: {self.category} [{self.status}]>"


class StatusHistory(db.Model):
    """Audit log of status changes and public/clarification updates for a report."""
    __tablename__ = "status_history"

    history_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    report_id = db.Column(
        db.String(20), 
        db.ForeignKey("reports.report_id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    old_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)
    updated_by = db.Column(
        db.Integer, 
        db.ForeignKey("users.user_id", ondelete="SET NULL"), 
        nullable=True
    )
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    note = db.Column(db.Text, nullable=True)
    is_public_note = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self, is_admin: bool = False) -> dict:
        """Serialize status history entry safely."""
        return {
            "history_id": self.history_id,
            "report_id": self.report_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
            "note": self.note if (is_admin or self.is_public_note) else None,
            "is_public_note": self.is_public_note
        }

    def __repr__(self):
        return f"<StatusHistory {self.history_id} on {self.report_id}: {self.old_status} -> {self.new_status}>"


class CommunityEvent(db.Model):
    """Local awareness campaigns, workshops, and volunteer cleanup drives."""
    __tablename__ = "community_events"

    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, index=True)
    location = db.Column(db.String(150), nullable=False)
    organizer = db.Column(db.String(100), nullable=False)
    created_by = db.Column(
        db.Integer, 
        db.ForeignKey("users.user_id", ondelete="SET NULL"), 
        nullable=True
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "description": self.description,
            "date": self.date.strftime("%Y-%m-%d %H:%M:%S") if self.date else None,
            "formatted_date": self.date.strftime("%A, %B %d, %Y at %I:%M %p") if self.date else None,
            "location": self.location,
            "organizer": self.organizer,
            "is_upcoming": self.date >= datetime.utcnow() if self.date else False
        }

    def __repr__(self):
        return f"<CommunityEvent {self.event_id}: {self.title}>"

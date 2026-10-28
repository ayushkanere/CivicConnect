<img width="1920" height="1020" alt="image" src="https://github.com/user-attachments/assets/57c39291-0f66-4619-94bd-8c2d6e41e4ef" />

# CivicConnect

> **A Digital Platform for Community Issue Reporting & Awareness**  
> Built for the College Community Engagement Project (CEP)  
> **Tagline:** REPORT (share local problems) • TRACK (follow progress) • IMPROVE (support community action)

# https://civicconnect-lu7s.onrender.com

---

## 1. Project Overview & Scope Rule

CivicConnect provides community members, students, and neighborhood residents with an organized, transparent platform to submit reports regarding local infrastructure and civic concerns (e.g., garbage accumulation, water drainage/leakage, damaged roadways, broken street fixtures). Each report receives a unique sequential ID (`CC-001`, `CC-002`, ...) and moves through a structured verification workflow reviewed by authorized project administrators.

### Critical Scope Rule (Mandatory Notice)
> **Version 1 is a reporting and tracking portal ONLY.**  
> It does **NOT** automatically forward complaints or dispatch requests to any municipal authority, utility board, or government agency. The site tracks reports internally for community action, volunteer coordination, and research.  
> **"Resolved"** denotes resolution verified by project members following physical inspection or community clean-up action.

---

## 2. Architecture & Text-Based System Diagram

```
+-----------------------------------------------------------------------------+
|                               USER / BROWSER                                |
|  - Responsive HTML5 / Vanilla CSS3 / JS UI (Mobile: 360px, Tablet, Desktop)  |
|  - Jinja2 Server-Rendered Views & Chart.js Visualizations                   |
+-----------------------------------------------------------------------------+
                                      |
                      HTTP / CSRF Protected Requests
                                      v
+-----------------------------------------------------------------------------+
|                             FLASK APPLICATION                               |
|                     (Application Factory & Blueprints)                       |
|                                                                             |
|  +--------------------+  +---------------------+  +----------------------+  |
|  |     public_bp      |  |      admin_bp       |  |        api_bp        |  |
|  |  /, /report,       |  |  /login, /logout    |  |  /api/stats          |  |
|  |  /track, /issues,  |  |  /reports, /events  |  |  /api/issues         |  |
|  |  /dashboard, etc.  |  |  (Protected Auth)   |  |  (JSON REST)         |  |
|  +--------------------+  +---------------------+  +----------------------+  |
|                                                                             |
|  +-----------------------------------------------------------------------+  |
|  |                            SERVICES LAYER                             |  |
|  |  - reports.py : Input sanitize, sequential ID (CC-xxx), transitions   |  |
|  |  - uploads.py : Pillow verify, 2MB bound, EXIF scrub, UUID names      |  |
|  |  - stats.py   : Real-time SQL aggregations for Chart.js               |  |
|  |  - auth.py    : Flask-Login, Werkzeug password hashing                |  |
|  +-----------------------------------------------------------------------+  |
|                                                                             |
|  Security Middleware: Flask-Limiter, Flask-WTF CSRF, HttpOnly Sessions      |
+-----------------------------------------------------------------------------+
                                      |
                       Parameterized Queries / ORM
                                      v
+-----------------------------------------------------------------------------+
|                          DATABASE STORAGE LAYER                             |
|  - MySQL 8.0 (Production default with utf8mb4, InnoDB, FKs, & Indexes)      |
|  - SQLite (Zero-config local development and automated pytest runner)       |
|                                                                             |
|  Tables:                                                                    |
|    - reports          : Core issue records, flags, notes, photo paths       |
|    - status_history   : Audit trail of all transitions & public notes       |
|    - users            : Admin accounts with password hashes                 |
|    - community_events : Scheduled cleanups, workshops, and awareness drives |
+-----------------------------------------------------------------------------+
```

---

## 3. Technology Stack

- **Backend**: Python 3.11+ with Flask (Application Factory, Blueprints).
- **Database**: MySQL 8 (production) / SQLite (testing/local fallback) using SQLAlchemy ORM with parameterized queries.
- **Frontend**: Semantic HTML5, Vanilla CSS3 (custom civic design system tokens, responsive mobile card stacking), Vanilla JavaScript.
- **Charts**: Chart.js 4.x (doughnut chart for status distribution, bar chart for categories, accessible table fallbacks).
- **Authentication**: Flask-Login session management with Werkzeug password hashing.
- **Security & Privacy**:
  - Flask-WTF CSRF protection on all mutating POST forms.
  - Flask-Limiter rate limiting (login: 5/min, submissions: 15/hr, tracking: 30/min).
  - Pillow image verification, 2 MB ceiling, EXIF/GPS metadata stripping, sanitized UUID filenames.
  - Privacy filters: automatic rejection of 10+ digit phone numbers and email addresses in public description/area.
- **Testing**: pytest test suite covering validation, auth, uploads, status transitions, duplicate handling, and XSS escaping.

---

## 4. Setup and Execution Guide

### Step 1: Create and Activate Virtual Environment
```bash
# Windows (PowerShell)
py -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env   # Windows
# or: cp .env.example .env # Linux/macOS
```
Adjust `DATABASE_URL` in `.env`:
- For MySQL 8: `DATABASE_URL=mysql+pymysql://civic_user:password@localhost:3306/civicconnect_db`
- For SQLite: `DATABASE_URL=sqlite:///civicconnect.db`

### Step 4: Database Setup & Seeding

#### Option A: Running with MySQL 8 (Production default)
1. Log into your MySQL console:
   ```bash
   mysql -u root -p
   ```
2. Execute the schema and seed scripts:
   ```sql
   SOURCE sql/schema.sql;
   SOURCE sql/seed.sql;
   ```

#### Option B: Running with SQLite (Local Development)
Execute the Python database seeder to create tables and load the 12 sample reports and 3 awareness events:
```bash
python scripts/seed_db.py
```

### Step 5: Create an Admin Account
To create or update an administrator account interactively:
```bash
python scripts/create_admin.py
```
*(Default test account seeded by `seed_db.py` / `seed.sql`: Username `Campus Admin`, Password `AdminPass123!`)*

### Step 6: Run the Application
```bash
python run.py
```
Open your web browser and navigate to `http://127.0.0.1:5000`.

### Step 7: Run Automated Tests
```bash
pytest -v
```

---

## 5. Live Presentation Demo Script (8-Minute CEP Flow)

This scenario demonstrates the end-to-end workflow for faculty, teammates, and community evaluators:

| Time | Phase | Action & What to Present |
|---|---|---|
| **0:00–1:00** | **Problem Intro** | Introduce CivicConnect and explain how local issues (overflowing trash, broken lighting) get lost in informal chat channels without tracking. |
| **1:00–2:00** | **CEP Objectives** | Highlight the 3 pillars: REPORT (structured logging), TRACK (transparency by ID), IMPROVE (data-backed community action). |
| **2:00–3:30** | **Resident Submission** | Open `http://127.0.0.1:5000/report`. Submit sample report: Category = *Garbage/Waste*, Description = *"Garbage collection needed near Community Park"*, Area = *"Community Park North Entrance"*. Show generated ID: `CC-013`. Click **Copy Report ID**. |
| **3:30–4:30** | **Resident Tracking** | Open `/track?id=CC-013`. Point out that the initial status is **Submitted** with the first chronological audit entry. |
| **4:30–6:00** | **Admin Review Workflow** | Navigate to `/admin/login`. Sign in (`Campus Admin` / `AdminPass123!`). Open `CC-013` from the table. Update status to **Under Review** with note *"Team visited site; confirmed pickup required."* Also approve for public listing. |
| **6:00–7:00** | **Verification & Impact** | Return to public `/track?id=CC-013` and `/issues` to show updated status. Navigate to `/dashboard` to show live Chart.js figures updated immediately. |
| **7:00–8:00** | **Privacy & Boundaries** | Reiterate that no personal phone numbers were collected, EXIF was stripped, and emphasize the scope disclaimer. |

---

## 6. Assumptions & Scope Boundaries

As required by Section 17 of the specification:
1. **Resident Anonymity**: Residents do not need to register or log in. No personal names, email addresses, or phone numbers are collected from reporters.
2. **Admin Accounts**: Only project team members have accounts; single admin role is used for MVP simplicity.
3. **Public Directory Approval**: Reports submitted by residents remain private on the Public Issue Directory until explicitly approved by an administrator to prevent vandalism. However, the submitter can always track progress via `/track` using their unique ID.
4. **Photo Moderation**: Uploaded photos are stored on the server with EXIF/GPS metadata stripped, but are withheld from public view until explicitly approved by an admin.
5. **Mandatory Verification Note**: Marking a report as "Resolved" strictly requires the admin to submit a verification note documenting physical inspection or volunteer action.
6. **No External Dispatches**: Version 1 has zero municipal API connections; no promises of official municipal dispatch are ever made.

---

## 7. Known Limitations & Future Scope

- **Email / SMS Alerts**: Notifications are currently manual (residents track status on the web portal by ID). Future versions could integrate opt-in SMS/WhatsApp updates.
- **Geospatial Mapping**: Approximate neighborhood area is recorded via text. Interactive Leaflet GIS mapping is implemented as an optional modular feature behind `ENABLE_MAP`.
- **Multi-Role RBAC**: The MVP uses a unified administrator role. A future version can add separate roles for field volunteers vs. lead organizers.

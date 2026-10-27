# CivicConnect QA & Testing Guide

This document details automated test coverage and the manual verification checklist for the CivicConnect web application.

---

## 1. Automated Test Suite (pytest)

The automated suite comprises **29 tests** validating core business logic, input sanitization, security constraints, and data integrity.

### Running Automated Tests
```bash
# Run full suite with verbose reporting
python -m pytest -v

# Run with test coverage
python -m pytest --cov=app tests/
```

### Test Coverage Matrix
| Module | Test File | Verified Specifications |
|---|---|---|
| **Reports Service** | `tests/test_reports.py` | Sequential zero-padded ID generation (`CC-001`, `CC-002`...), initial `status_history` creation, form submission and confirmation page rendering. |
| **Input Validation** | `tests/test_validation.py` | Category whitelist, description bounds (10-500 chars), area bounds (3-80 chars), HTML tag stripping, phone number rejection (10+ digits), email rejection, honeypot bot trap. |
| **Image Uploads** | `tests/test_uploads.py` | Allowed formats (JPG, PNG, WEBP), 2 MB size ceiling rejection, corrupted image rejection, randomized UUID filenames, unapproved photo privacy restriction. |
| **Report Tracking** | `tests/test_tracking.py` | Look up by ID for public reports, look up for unapproved reports, chronological order of status timeline, friendly not-found state, filtering out internal admin notes from public view. |
| **Admin Operations** | `tests/test_admin.py` | Session authentication, generic error messages on invalid login, route protection on `/admin/*`, mandatory verification note rule for "Resolved", duplicate consolidation, event management. |
| **Analytics & API** | `tests/test_stats.py` | Live counts calculation, JSON `/api/stats` endpoint and disclaimer, public-only and non-hidden filtering on `/issues` and `/api/issues`. |
| **Security & Privacy** | `tests/test_security.py` | Jinja autoescaping against XSS script injections in description and locality fields. |

---

## 2. Manual Test Checklist (Demo Flow)

Follow this checklist to verify portal functionality end-to-end:

### Phase A: Resident Submission & Tracking
- [ ] **Step 1: Open Home Page** (`http://127.0.0.1:5000/`)
  - Check that the scope disclaimer banner appears at the top.
  - Verify that the 6-step lifecycle and 4 KPI stat cards are rendered.
- [ ] **Step 2: Submit a Valid Report** (`/report`)
  - Choose Category: `Garbage/Waste`.
  - Enter Description: `Garbage collection needed near Community Park with overflowing bins.`
  - Enter Area: `Community Park North Entrance`.
  - Attach an optional test photo (<2 MB).
  - Submit the form. Verify redirection to `/report/confirmation/CC-XXX`.
- [ ] **Step 3: Confirmation Page Utilities**
  - Verify unique ID `CC-013` (or next sequence) is displayed.
  - Click **Copy Report ID**; confirm button changes to "Copied!".
  - Click **Track This Report Now**.
- [ ] **Step 4: Track by ID** (`/track?id=CC-XXX`)
  - Confirm the report details and the initial timeline entry (*Status: Submitted*) appear.
  - Confirm the report indicates "Under Review / Private" (not publicly listed yet).
  - Test searching a bogus ID like `CC-999`; confirm the friendly "Report ID Not Found" state displays.

### Phase B: Form Validation & Privacy Safeguards
- [ ] **Step 5: Validation Boundary Testing** (`/report`)
  - Try submitting with a description < 10 characters: verify inline error.
  - Try submitting with an area < 3 characters: verify inline error.
  - Try submitting with a phone number in the description (`Call me at 9876543210`): verify privacy rejection.
  - Try submitting with an email address: verify privacy rejection.
  - Try uploading a file > 2 MB: verify immediate file rejection.

### Phase C: Administrator Review & Moderation
- [ ] **Step 6: Admin Authentication** (`/admin/login`)
  - Try invalid password: confirm generic "Invalid credentials" error message appears.
  - Sign in with `Campus Admin` / `AdminPass123!`. Confirm success redirect to `/admin/reports`.
- [ ] **Step 7: Admin Review & Status Progression** (`/admin/reports/CC-XXX`)
  - Open the report submitted in Step 2.
  - Update status to `Under Review` with note *"Team visited site; verified bins are overflowing."*
  - Check the public track page (`/track?id=CC-XXX`): verify the new status and note appear immediately.
  - Return to Admin and try updating to `Resolved` **without a note**: confirm it fails with an error requiring a verification note.
  - Enter a valid verification note: *"Verification Note: Volunteer cleanup completed; bins emptied and sanitized."*
  - Submit: confirm status progresses to `Resolved`.
- [ ] **Step 8: Moderation Controls**
  - Toggle **Approve for Public Directory**: verify report now appears on `/issues`.
  - If a photo was uploaded, toggle **Approve Photo**: verify photo is visible on public track view.
  - Test **Mark Duplicate**: link a test report to `CC-001`. Confirm it is flagged and unlisted from `/issues`.

### Phase D: Public Impact Dashboard & Awareness
- [ ] **Step 9: Live Dashboard Verification** (`/dashboard`)
  - Confirm total report count and "Resolved" count reflect the updates made in Phase C.
  - Verify that the Chart.js doughnut chart and bar chart render properly.
  - Check the mandatory disclaimer note: *"Counts reflect reports on this portal, not confirmed official resolution."*
- [ ] **Step 10: Community Awareness** (`/awareness`)
  - Verify the 3 scheduled events appear with title, date, location, and organizer.
  - In Admin area (`/admin/events`), create a new test event and verify it displays on `/awareness`.

### Phase E: Responsive & Accessibility Checks
- [ ] **Mobile (360px width)**: Navbar collapses into hamburger menu; data tables collapse into readable cards.
- [ ] **Tablet (768px width)**: Grids reflow cleanly into 2 columns; touch targets are at least 44px.
- [ ] **Desktop (1280px width)**: Centered layout with max-width 1200px container; visible keyboard focus rings.

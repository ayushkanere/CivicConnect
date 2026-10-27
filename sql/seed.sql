-- CivicConnect Fictional Seed Data
-- ALL DATA IN THIS FILE IS STRICTLY FICTIONAL FOR DEMO AND TESTING PURPOSES ONLY.
-- None of these reports represent real individuals or live complaints sent to municipal bodies.

USE civicconnect_db;

-- Initial Admin Account (Password: AdminPass123! hashed with scrypt/pbkdf2 compatible format for SQL testing)
-- Note: In production or standard setup, create_admin.py is used to securely create credentials.
INSERT INTO users (user_id, name, email, password_hash, role, created_at)
VALUES (
    1, 
    'Campus Admin', 
    'admin@civicconnect.local', 
    'scrypt:32768:8:1$u7N3N4x7k7J7r8L8$34f2a7e7804470c1737e195155169a84b067f9d8a39ec861c841e21b8a4f6cfdd582e071b7643b0e11e0394236a2824cf48f8045610ec5043bf5a041f057e5e3', 
    'admin', 
    '2026-10-01 09:00:00'
) ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 12 Fictional Sample Reports
INSERT INTO reports (report_id, category, description, area, photo_path, status, is_public, is_hidden, is_duplicate, duplicate_of, photo_approved, admin_note, created_at, updated_at) VALUES
('CC-001', 'Garbage/Waste', 'Garbage accumulation near South Gate bus shelter overflowing onto footpath.', 'South Gate Campus Perimeter', NULL, 'Submitted', 1, 0, 0, NULL, 0, 'New resident submission awaiting team visit.', '2026-10-10 10:15:00', '2026-10-10 10:15:00'),
('CC-002', 'Broken Streetlight', 'Pole #14 flickering continuously and dark after 8 PM along Hostel Road.', 'Hostel Road East Sector', NULL, 'Under Review', 1, 0, 0, NULL, 0, 'Inspected by team volunteer; confirmed lamp unit issue.', '2026-10-11 11:30:00', '2026-10-12 14:00:00'),
('CC-003', 'Water Leakage/Drainage', 'Stagnant rainwater and blocked storm drain causing foul smell near Cafeteria lane.', 'Cafeteria Outer Lane', NULL, 'In Progress', 1, 0, 0, NULL, 0, 'Volunteer clean-up drive scheduled for this Saturday.', '2026-10-12 08:45:00', '2026-10-13 16:30:00'),
('CC-004', 'Damaged Road/Unsafe Infrastructure', 'Large pothole at junction of 2nd Cross and Main Avenue causing two-wheelers to slip.', '2nd Cross Junction', NULL, 'Resolved', 1, 0, 0, NULL, 0, 'Verification Note: Community volunteer team patched the spot with cold mix and gravel; site safe.', '2026-10-05 14:20:00', '2026-10-09 17:00:00'),
('CC-005', 'Community Cleanliness/Awareness', 'Flyers and plastic bottles dumped along community playground green belt.', 'Playground Boundary Green Belt', NULL, 'In Progress', 1, 0, 0, NULL, 0, 'Community cleanliness campaign planned with CEP volunteers.', '2026-10-14 09:10:00', '2026-10-15 11:00:00'),
('CC-006', 'Garbage/Waste', 'Overflowing garbage bin near North Quadrangle.', 'North Quadrangle Block B', NULL, 'Submitted', 0, 0, 0, NULL, 0, 'Pending admin public approval.', '2026-10-15 16:00:00', '2026-10-15 16:00:00'),
('CC-007', 'Water Leakage/Drainage', 'Potable water pipe joint dripping continuously near drinking water kiosk.', 'Sports Complex Drinking Kiosk', NULL, 'Resolved', 1, 0, 0, NULL, 0, 'Verification Note: Campus plumbing lead replaced washer; verified no further leakage.', '2026-10-06 13:00:00', '2026-10-08 12:00:00'),
('CC-008', 'Broken Streetlight', 'Two streetlights completely dark along pedestrian pathway near Library.', 'Library Rear Walkway', NULL, 'Under Review', 1, 0, 0, NULL, 0, 'Reported to campus maintenance committee.', '2026-10-16 19:25:00', '2026-10-17 10:15:00'),
('CC-009', 'Damaged Road/Unsafe Infrastructure', 'Broken pavement slab with exposed rebar posing tripping hazard.', 'Science Block Promenade', NULL, 'Under Review', 1, 0, 0, NULL, 0, 'Marked with safety warning tape pending repair.', '2026-10-17 15:40:00', '2026-10-18 09:30:00'),
('CC-010', 'Garbage/Waste', 'Duplicate report of South Gate bus shelter garbage dump.', 'South Gate Bus Stop Area', NULL, 'Under Review', 0, 0, 1, 'CC-001', 0, 'Flagged as duplicate of CC-001.', '2026-10-11 12:00:00', '2026-10-12 10:00:00'),
('CC-011', 'Other', 'Loose overhead cable hanging low across community pathway.', 'Engineering Annexe Pathway', NULL, 'Submitted', 1, 0, 0, NULL, 0, 'Checked by student safety monitor.', '2026-10-18 11:15:00', '2026-10-18 11:15:00'),
('CC-012', 'Community Cleanliness/Awareness', 'Unregulated poster pasting on campus boundary wall.', 'West Boundary Wall', NULL, 'Resolved', 1, 0, 0, NULL, 0, 'Verification Note: Cleaned up and awareness poster placed reminding residents to keep walls clean.', '2026-10-07 10:00:00', '2026-10-10 15:00:00')
ON DUPLICATE KEY UPDATE description=VALUES(description);

-- Status History for Fictional Reports
INSERT INTO status_history (report_id, old_status, new_status, updated_by, updated_at, note, is_public_note) VALUES
('CC-001', NULL, 'Submitted', NULL, '2026-10-10 10:15:00', 'Report submitted by resident.', 1),
('CC-002', NULL, 'Submitted', NULL, '2026-10-11 11:30:00', 'Report submitted by resident.', 1),
('CC-002', 'Submitted', 'Under Review', 1, '2026-10-12 14:00:00', 'Team reviewed details and confirmed streetlight fixture code.', 1),
('CC-003', NULL, 'Submitted', NULL, '2026-10-12 08:45:00', 'Report submitted by resident.', 1),
('CC-003', 'Submitted', 'Under Review', 1, '2026-10-12 15:00:00', 'Site visit conducted by student volunteers.', 1),
('CC-003', 'Under Review', 'In Progress', 1, '2026-10-13 16:30:00', 'Community drainage clearing drive coordinated for Saturday.', 1),
('CC-004', NULL, 'Submitted', NULL, '2026-10-05 14:20:00', 'Report submitted by resident.', 1),
('CC-004', 'Submitted', 'Under Review', 1, '2026-10-06 10:00:00', 'Assessed depth and traffic impact.', 1),
('CC-004', 'Under Review', 'In Progress', 1, '2026-10-07 11:00:00', 'Cold mix gravel patch materials procured by CEP team.', 1),
('CC-004', 'In Progress', 'Resolved', 1, '2026-10-09 17:00:00', 'Verification Note: Pothole filled and levelled by volunteer workgroup. Inspected and confirmed safe.', 1),
('CC-005', NULL, 'Submitted', NULL, '2026-10-14 09:10:00', 'Report submitted by resident.', 1),
('CC-005', 'Submitted', 'In Progress', 1, '2026-10-15 11:00:00', 'Cleanliness campaign organized with local student volunteers.', 1),
('CC-006', NULL, 'Submitted', NULL, '2026-10-15 16:00:00', 'Report submitted by resident.', 1),
('CC-007', NULL, 'Submitted', NULL, '2026-10-06 13:00:00', 'Report submitted by resident.', 1),
('CC-007', 'Submitted', 'Resolved', 1, '2026-10-08 12:00:00', 'Verification Note: Joint replaced; water leakage completely stopped.', 1),
('CC-008', NULL, 'Submitted', NULL, '2026-10-16 19:25:00', 'Report submitted by resident.', 1),
('CC-008', 'Submitted', 'Under Review', 1, '2026-10-17 10:15:00', 'Report verified by evening patrol.', 1),
('CC-009', NULL, 'Submitted', NULL, '2026-10-17 15:40:00', 'Report submitted by resident.', 1),
('CC-009', 'Submitted', 'Under Review', 1, '2026-10-18 09:30:00', 'Caution cones placed around damaged slab.', 1),
('CC-010', NULL, 'Submitted', NULL, '2026-10-11 12:00:00', 'Report submitted by resident.', 1),
('CC-010', 'Submitted', 'Under Review', 1, '2026-10-12 10:00:00', 'Marked as duplicate of CC-001 (same waste dump spot).', 1),
('CC-011', NULL, 'Submitted', NULL, '2026-10-18 11:15:00', 'Report submitted by resident.', 1),
('CC-012', NULL, 'Submitted', NULL, '2026-10-07 10:00:00', 'Report submitted by resident.', 1),
('CC-012', 'Submitted', 'Resolved', 1, '2026-10-10 15:00:00', 'Verification Note: Area cleaned and awareness board mounted.', 1);

-- 3 Fictional Community Awareness Events
INSERT INTO community_events (event_id, title, description, date, location, organizer, created_by, created_at) VALUES
(1, 'Campus Cleanliness Drive & Plastic Audit', 'Join student volunteers for a 2-hour morning clean-up and single-use plastic waste audit around the student centre and lake promenade.', '2026-11-08 08:30:00', 'Student Centre Amphitheatre', 'CEP Green Campus Initiative', 1, '2026-10-15 10:00:00'),
(2, 'Community Water Conservation Workshop', 'Interactive session on fixing domestic drip leaks, rooftop rainwater harvesting basics, and neighborhood drainage awareness.', '2026-11-15 14:00:00', 'Civic Hall Room 102', 'Youth Water Action Team', 1, '2026-10-16 14:30:00'),
(3, 'Pedestrian Safety & Infrastructure Walk', 'Walk-through assessment of pedestrian crossings, lighting blind spots, and sidewalk accessibility with volunteer surveyors.', '2026-11-22 17:00:00', 'Main Gate Clock Tower', 'CEP Safety & Mobility Group', 1, '2026-10-18 09:00:00')
ON DUPLICATE KEY UPDATE title=VALUES(title);

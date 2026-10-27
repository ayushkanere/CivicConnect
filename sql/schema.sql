-- CivicConnect MySQL 8 Schema
-- utf8mb4 charset, strict foreign keys, indexes, and ENUM constraints

CREATE DATABASE IF NOT EXISTS civicconnect_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE civicconnect_db;

-- 1. Users Table (Admin accounts)
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin') NOT NULL DEFAULT 'admin',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Reports Table
CREATE TABLE IF NOT EXISTS reports (
    report_id VARCHAR(20) PRIMARY KEY,
    category VARCHAR(60) NOT NULL,
    description TEXT NOT NULL,
    area VARCHAR(100) NOT NULL,
    photo_path VARCHAR(255) DEFAULT NULL,
    status ENUM('Submitted', 'Under Review', 'In Progress', 'Resolved') NOT NULL DEFAULT 'Submitted',
    is_public TINYINT(1) NOT NULL DEFAULT 0,
    is_hidden TINYINT(1) NOT NULL DEFAULT 0,
    is_duplicate TINYINT(1) NOT NULL DEFAULT 0,
    duplicate_of VARCHAR(20) DEFAULT NULL,
    photo_approved TINYINT(1) NOT NULL DEFAULT 0,
    admin_note TEXT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_reports_status (status),
    INDEX idx_reports_category (category),
    INDEX idx_reports_public_hidden (is_public, is_hidden),
    INDEX idx_reports_created_at (created_at),
    CONSTRAINT fk_reports_duplicate_of FOREIGN KEY (duplicate_of) 
        REFERENCES reports(report_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Status History Table
CREATE TABLE IF NOT EXISTS status_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    report_id VARCHAR(20) NOT NULL,
    old_status VARCHAR(50) DEFAULT NULL,
    new_status VARCHAR(50) NOT NULL,
    updated_by INT DEFAULT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    note TEXT DEFAULT NULL,
    is_public_note TINYINT(1) NOT NULL DEFAULT 1,
    INDEX idx_status_history_report (report_id),
    INDEX idx_status_history_updated_at (updated_at),
    CONSTRAINT fk_history_report_id FOREIGN KEY (report_id) 
        REFERENCES reports(report_id) ON DELETE CASCADE,
    CONSTRAINT fk_history_updated_by FOREIGN KEY (updated_by) 
        REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Community Events Table
CREATE TABLE IF NOT EXISTS community_events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    date DATETIME NOT NULL,
    location VARCHAR(150) NOT NULL,
    organizer VARCHAR(100) NOT NULL,
    created_by INT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_events_date (date),
    CONSTRAINT fk_events_created_by FOREIGN KEY (created_by) 
        REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

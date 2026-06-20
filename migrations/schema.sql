-- ═══════════════════════════════════════════════════════════════════
--  Maasai Mara Ecosystem Management & Safari Gate Clearance System
--  Database Schema — MySQL 8.x
--  Narok County Government
-- ═══════════════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS maasai_mara_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE maasai_mara_db;

-- ── Users ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    uuid             VARCHAR(36)  NOT NULL UNIQUE,
    full_name        VARCHAR(120) NOT NULL,
    email            VARCHAR(120) NOT NULL UNIQUE,
    phone            VARCHAR(20),
    id_number        VARCHAR(20)  UNIQUE,
    password_hash    VARCHAR(256) NOT NULL,
    role             ENUM('admin','guide') NOT NULL DEFAULT 'guide',
    is_active        TINYINT(1)  NOT NULL DEFAULT 1,
    is_verified      TINYINT(1)  NOT NULL DEFAULT 0,
    profile_photo    VARCHAR(256),
    license_number   VARCHAR(50),
    company          VARCHAR(120),
    created_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login       DATETIME,
    INDEX idx_email  (email),
    INDEX idx_role   (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Vehicles ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vehicles (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    user_id          INT         NOT NULL,
    plate_number     VARCHAR(20) NOT NULL UNIQUE,
    vehicle_type     ENUM('Land Cruiser','Land Rover','Minivan','Bus','Motorcycle','Other') NOT NULL,
    make             VARCHAR(60),
    model            VARCHAR(60),
    year             INT,
    color            VARCHAR(30),
    capacity         INT         NOT NULL DEFAULT 7,
    insurance_number VARCHAR(60),
    insurance_expiry DATE,
    is_active        TINYINT(1)  NOT NULL DEFAULT 1,
    created_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_plate  (plate_number),
    INDEX idx_owner  (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Gate Clearances ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gate_clearances (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    token            VARCHAR(36)  NOT NULL UNIQUE,
    guide_id         INT          NOT NULL,
    vehicle_id       INT          NOT NULL,
    gate             ENUM('Sekenani Gate','Oloololo Gate','Talek Gate','Musiara Gate',
                          'Sand River Gate','Ololaimutia Gate') NOT NULL,
    entry_date       DATE         NOT NULL,
    entry_time       TIME,
    exit_date        DATE,
    exit_time        TIME,
    passenger_count  INT          NOT NULL DEFAULT 0,
    adult_count      INT          NOT NULL DEFAULT 0,
    child_count      INT          NOT NULL DEFAULT 0,
    citizen_count    INT          NOT NULL DEFAULT 0,
    non_citizen_count INT         NOT NULL DEFAULT 0,
    purpose          ENUM('Game Drive','Research','Photography','Balloon Safari',
                          'Walking Safari','Night Drive','Other') DEFAULT 'Game Drive',
    status           ENUM('pending','approved','rejected','expired') NOT NULL DEFAULT 'pending',
    qr_code_path     VARCHAR(256),
    manifest_path    VARCHAR(256),
    fee_paid         DECIMAL(10,2) DEFAULT 0.00,
    fee_currency     VARCHAR(3)   DEFAULT 'KES',
    notes            TEXT,
    approved_by      INT,
    approved_at      DATETIME,
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (guide_id)    REFERENCES users(id),
    FOREIGN KEY (vehicle_id)  REFERENCES vehicles(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    INDEX idx_guide      (guide_id),
    INDEX idx_status     (status),
    INDEX idx_entry_date (entry_date),
    INDEX idx_gate       (gate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Passengers ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS passengers (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    clearance_id    INT          NOT NULL,
    full_name       VARCHAR(120) NOT NULL,
    nationality     VARCHAR(60),
    passport_id     VARCHAR(40),
    age_group       ENUM('adult','child') DEFAULT 'adult',
    is_citizen      TINYINT(1)   DEFAULT 0,
    FOREIGN KEY (clearance_id) REFERENCES gate_clearances(id) ON DELETE CASCADE,
    INDEX idx_clearance (clearance_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Wildlife Sightings ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wildlife_sightings (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    reported_by     INT          NOT NULL,
    clearance_id    INT,
    species         VARCHAR(100) NOT NULL,
    common_name     VARCHAR(100),
    category        ENUM('Big Five','Plains Game','Predator','Primate',
                         'Bird','Reptile','Other Mammal') DEFAULT 'Plains Game',
    count           INT          NOT NULL DEFAULT 1,
    latitude        DECIMAL(10,8) NOT NULL,
    longitude       DECIMAL(11,8) NOT NULL,
    location_name   VARCHAR(120),
    behavior        ENUM('Feeding','Resting','Moving','Hunting','Playing',
                         'Mating','Drinking','Other') DEFAULT 'Other',
    notes           TEXT,
    sighted_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_verified     TINYINT(1)   DEFAULT 0,
    threat_level    ENUM('none','low','medium','high') DEFAULT 'none',
    FOREIGN KEY (reported_by)  REFERENCES users(id),
    FOREIGN KEY (clearance_id) REFERENCES gate_clearances(id) ON DELETE SET NULL,
    INDEX idx_reporter   (reported_by),
    INDEX idx_sighted_at (sighted_at),
    INDEX idx_species    (species),
    INDEX idx_category   (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Sighting Photos ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sighting_photos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    sighting_id     INT          NOT NULL,
    filename        VARCHAR(256) NOT NULL,
    original_name   VARCHAR(256),
    file_size       INT,
    uploaded_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sighting_id) REFERENCES wildlife_sightings(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Revenue Records ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS revenue_records (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    clearance_id    INT          NOT NULL,
    gate            VARCHAR(60),
    amount          DECIMAL(10,2) NOT NULL,
    currency        VARCHAR(3)   DEFAULT 'KES',
    payment_method  ENUM('Cash','M-Pesa','Card','Bank Transfer') DEFAULT 'Cash',
    mpesa_ref       VARCHAR(30),
    collected_by    INT,
    collected_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT,
    FOREIGN KEY (clearance_id)  REFERENCES gate_clearances(id),
    FOREIGN KEY (collected_by)  REFERENCES users(id),
    INDEX idx_clearance    (clearance_id),
    INDEX idx_collected_at (collected_at),
    INDEX idx_gate         (gate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Alerts ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(200) NOT NULL,
    message     TEXT         NOT NULL,
    alert_type  ENUM('info','warning','danger','success') DEFAULT 'info',
    created_by  INT,
    is_active   TINYINT(1)   NOT NULL DEFAULT 1,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at  DATETIME,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_active     (is_active),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Audit Logs ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT,
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id   INT,
    details     TEXT,
    ip_address  VARCHAR(45),
    user_agent  VARCHAR(256),
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id   (user_id),
    INDEX idx_action    (action),
    INDEX idx_created   (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── alembic_version (for Flask-Migrate) ───────────────────────────
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
) ENGINE=InnoDB;

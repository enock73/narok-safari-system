-- ═══════════════════════════════════════════════════════════════════
--  Sample Data Seed Script
--  Run AFTER schema.sql
-- ═══════════════════════════════════════════════════════════════════

USE maasai_mara_db;

-- ── Users ─────────────────────────────────────────────────────────
-- Passwords: Admin@2024, Guide@2024, Guide@2024 (same for guides)
-- Hash generated with werkzeug pbkdf2:sha256

INSERT INTO users (uuid, full_name, email, phone, id_number, password_hash, role, is_active, is_verified, license_number, company) VALUES
('a1b2c3d4-0001-0001-0001-000000000001', 'Admin County Official',  'admin@maranaorok.go.ke', '+254700111001', 'ADMIN001', 'pbkdf2:sha256:600000$salt000000000000000000000001$5c2a5b3f5e6d7c8b9a0f1e2d3c4b5a6e7f8d9e0a1b2c3d4e5f6a7b8c9d0e1f', 'admin', 1, 1, NULL, 'Narok County Government'),
('a1b2c3d4-0002-0002-0002-000000000002', 'John Kipchoge',          'guide@example.com',      '+254712345678', 'NID12345678', 'pbkdf2:sha256:600000$salt000000000000000000000002$6d3b4c5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b', 'guide', 1, 1, 'KWS/TG/2021/001', 'Mara Expeditions Ltd'),
('a1b2c3d4-0003-0003-0003-000000000003', 'Mary Wanjiku Kamau',     'mary@safarico.co.ke',    '+254723456789', 'NID23456789', 'pbkdf2:sha256:600000$salt000000000000000000000002$6d3b4c5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b', 'guide', 1, 1, 'KWS/TG/2020/012', 'Savanna Safari Co.'),
('a1b2c3d4-0004-0004-0004-000000000004', 'Peter Omondi Onyango',   'peter@wildlifekenya.ke', '+254734567890', 'NID34567890', 'pbkdf2:sha256:600000$salt000000000000000000000002$6d3b4c5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b', 'guide', 1, 0, 'KWS/TG/2022/034', 'Kenya Wildlife Tours');

-- ── Vehicles ─────────────────────────────────────────────────────
INSERT INTO vehicles (user_id, plate_number, vehicle_type, make, model, year, color, capacity, insurance_number, insurance_expiry) VALUES
(2, 'KCB 123A', 'Land Cruiser', 'Toyota',    'Land Cruiser 76',  2019, 'White',  8, 'INS/2024/001', '2025-06-30'),
(2, 'KDD 456B', 'Land Rover',   'Land Rover','Defender 110',     2021, 'Khaki',  9, 'INS/2024/002', '2025-04-15'),
(3, 'KCC 789C', 'Minivan',      'Toyota',    'Hiace',            2020, 'White', 14, 'INS/2024/003', '2025-09-20'),
(4, 'KDA 321D', 'Land Cruiser', 'Toyota',    'Land Cruiser Prado',2022,'Silver', 7, 'INS/2024/004', '2026-01-10');

-- ── Gate Clearances ───────────────────────────────────────────────
INSERT INTO gate_clearances (token, guide_id, vehicle_id, gate, entry_date, entry_time, passenger_count, adult_count, child_count, citizen_count, non_citizen_count, purpose, status, fee_paid, approved_by, approved_at, created_at) VALUES
('token-0001-0001-0001-000000000001', 2, 1, 'Sekenani Gate',    CURDATE() - INTERVAL 5 DAY, '07:00:00', 6, 5, 1, 2, 3, 'Game Drive',   'approved', 42650.00, 1, NOW() - INTERVAL 5 DAY, NOW() - INTERVAL 5 DAY + INTERVAL 1 HOUR),
('token-0002-0002-0002-000000000002', 2, 1, 'Talek Gate',       CURDATE() - INTERVAL 4 DAY, '07:30:00', 4, 4, 0, 0, 4, 'Photography',  'approved', 42300.00, 1, NOW() - INTERVAL 4 DAY, NOW() - INTERVAL 4 DAY + INTERVAL 1 HOUR),
('token-0003-0003-0003-000000000003', 3, 3, 'Musiara Gate',     CURDATE() - INTERVAL 3 DAY, '06:30:00', 8, 6, 2, 4, 2, 'Game Drive',   'approved', 30100.00, 1, NOW() - INTERVAL 3 DAY, NOW() - INTERVAL 3 DAY + INTERVAL 1 HOUR),
('token-0004-0004-0004-000000000004', 2, 2, 'Oloololo Gate',    CURDATE() - INTERVAL 2 DAY, '08:00:00', 5, 5, 0, 1, 4, 'Game Drive',   'approved', 43050.00, 1, NOW() - INTERVAL 2 DAY, NOW() - INTERVAL 2 DAY + INTERVAL 1 HOUR),
('token-0005-0005-0005-000000000005', 4, 4, 'Sand River Gate',  CURDATE() - INTERVAL 1 DAY, '07:00:00', 6, 6, 0, 2, 4, 'Research',     'approved', 43300.00, 1, NOW() - INTERVAL 1 DAY, NOW() - INTERVAL 1 DAY + INTERVAL 1 HOUR),
('token-0006-0006-0006-000000000006', 3, 3, 'Sekenani Gate',    CURDATE(),                  '07:00:00', 7, 5, 2, 3, 2, 'Game Drive',   'pending',  0.00,     NULL, NULL, NOW() - INTERVAL 2 HOUR),
('token-0007-0007-0007-000000000007', 4, 4, 'Talek Gate',       CURDATE() + INTERVAL 1 DAY,'07:30:00', 4, 4, 0, 0, 4, 'Photography',  'pending',  0.00,     NULL, NULL, NOW() - INTERVAL 30 MINUTE),
('token-0008-0008-0008-000000000008', 2, 1, 'Ololaimutia Gate', CURDATE() - INTERVAL 6 DAY,'07:00:00', 3, 3, 0, 0, 3, 'Walking Safari','rejected', 0.00,    1, NOW() - INTERVAL 6 DAY, NOW() - INTERVAL 6 DAY);

-- ── Passengers ───────────────────────────────────────────────────
INSERT INTO passengers (clearance_id, full_name, nationality, passport_id, age_group, is_citizen) VALUES
(1,'James Mitchell','British','GB123456','adult',0),
(1,'Sarah Mitchell','British','GB123457','adult',0),
(1,'Tom Harrison','American','US987654','adult',0),
(1,'Aisha Kamau','Kenyan','NID111222','adult',1),
(1,'David Kamau','Kenyan','NID111333','adult',1),
(1,'Emma Kamau','Kenyan','NID111444','child',1),
(2,'Claire Dubois','French','FR456789','adult',0),
(2,'Jean-Pierre Dubois','French','FR456790','adult',0),
(2,'Susan Walker','Australian','AU789012','adult',0),
(2,'Michael Walker','Australian','AU789013','adult',0);

-- ── Revenue Records ───────────────────────────────────────────────
INSERT INTO revenue_records (clearance_id, gate, amount, currency, payment_method, collected_by, collected_at) VALUES
(1, 'Sekenani Gate',    42650.00, 'KES', 'M-Pesa',       1, NOW() - INTERVAL 5 DAY),
(2, 'Talek Gate',       42300.00, 'KES', 'Cash',         1, NOW() - INTERVAL 4 DAY),
(3, 'Musiara Gate',     30100.00, 'KES', 'Cash',         1, NOW() - INTERVAL 3 DAY),
(4, 'Oloololo Gate',    43050.00, 'KES', 'Card',         1, NOW() - INTERVAL 2 DAY),
(5, 'Sand River Gate',  43300.00, 'KES', 'M-Pesa',       1, NOW() - INTERVAL 1 DAY);

-- ── Wildlife Sightings ────────────────────────────────────────────
INSERT INTO wildlife_sightings (reported_by, clearance_id, species, common_name, category, count, latitude, longitude, location_name, behavior, notes, sighted_at, is_verified, threat_level) VALUES
(2, 1, 'Panthera leo',            'Lion',          'Big Five',   4, -1.5142, 35.1433, 'Near Sekenani River',        'Resting',  'Pride of 4 lions resting under acacia trees',           NOW() - INTERVAL 5 DAY,  1, 'none'),
(2, 1, 'Loxodonta africana',      'Elephant',      'Big Five',  12, -1.5300, 35.1600, 'Mara Triangle',              'Feeding',  'Large breeding herd feeding on grass',                   NOW() - INTERVAL 5 DAY,  1, 'none'),
(3, 3, 'Connochaetes taurinus',   'Wildebeest',    'Plains Game',200,-1.4500,35.0800, 'Near Mara River',            'Moving',   'Large wildebeest migration crossing observed',           NOW() - INTERVAL 3 DAY,  1, 'none'),
(2, 2, 'Panthera pardus',         'Leopard',       'Big Five',   1, -1.5600, 35.2100, 'Talek River Banks',          'Hunting',  'Leopard spotted stalking impala at dusk',                NOW() - INTERVAL 4 DAY,  1, 'medium'),
(4, 5, 'Acinonyx jubatus',        'Cheetah',       'Predator',   3, -1.6400, 35.3200, 'Sand River Plains',          'Hunting',  'Cheetah coalition of 3 males on open plains',           NOW() - INTERVAL 1 DAY,  0, 'none'),
(3, 3, 'Diceros bicornis',        'Black Rhino',   'Big Five',   2, -1.4200, 35.0500, 'Oloololo Escarpment',        'Feeding',  'Rare sighting of mother rhino with calf',                NOW() - INTERVAL 3 DAY,  1, 'high'),
(2, 4, 'Hippopotamus amphibius',  'Hippopotamus',  'Other Mammal',8,-1.5800, 35.1000, 'Mara River Pool',            'Resting',  'Hippo pod resting in river pool',                       NOW() - INTERVAL 2 DAY,  1, 'none'),
(4, 5, 'Equus quagga',            'Plains Zebra',  'Plains Game',50,-1.6500, 35.3000, 'Sand River Floodplains',     'Feeding',  'Large zebra herd grazing',                              NOW() - INTERVAL 1 DAY,  0, 'none'),
(2, NULL,'Syncerus caffer',       'African Buffalo','Big Five',  30,-1.5450, 35.1850, 'South Mara Triangle',        'Moving',   'Bachelor herd of buffalo moving towards water',         NOW() - INTERVAL 6 HOUR, 0, 'none'),
(3, NULL,'Crocodylus niloticus',  'Nile Crocodile','Reptile',    5, -1.5000, 35.1500, 'Mara River Crossing Point',  'Resting',  'Crocodiles waiting at wildebeest crossing',             NOW() - INTERVAL 3 HOUR, 0, 'low');

-- ── Alerts ────────────────────────────────────────────────────────
INSERT INTO alerts (title, message, alert_type, created_by, is_active) VALUES
('Wildebeest Migration Active', 'The Great Wildebeest Migration is currently active near the Mara River crossing points. Expect high vehicle density at Talek and Sand River gates.', 'info', 1, 1),
('Black Rhino Sighting', 'Black rhino mother and calf spotted near Oloololo Escarpment. All vehicles must maintain a minimum 200m distance. No off-road driving in this area.', 'warning', 1, 1),
('Road Closure Notice', 'Musiara Gate access road under maintenance. All vehicles must use the alternative Oloololo route. Expected completion in 3 days.', 'danger', 1, 1);

-- ── Audit Logs ────────────────────────────────────────────────────
INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, ip_address, created_at) VALUES
(1, 'LOGIN',    'User', 1, 'Admin login', '127.0.0.1', NOW() - INTERVAL 6 DAY),
(2, 'REGISTER', 'User', 2, 'New guide registration', '192.168.1.10', NOW() - INTERVAL 10 DAY),
(1, 'APPROVE',  'GateClearance', 1, 'Clearance approved for John Kipchoge', '127.0.0.1', NOW() - INTERVAL 5 DAY),
(1, 'APPROVE',  'GateClearance', 2, 'Clearance approved for John Kipchoge', '127.0.0.1', NOW() - INTERVAL 4 DAY),
(1, 'APPROVE',  'GateClearance', 3, 'Clearance approved for Mary Wanjiku', '127.0.0.1', NOW() - INTERVAL 3 DAY),
(1, 'LOGIN',    'User', 1, 'Admin login', '127.0.0.1', NOW() - INTERVAL 1 HOUR),
(2, 'LOGIN',    'User', 2, 'Guide login', '192.168.1.10', NOW() - INTERVAL 2 HOUR);

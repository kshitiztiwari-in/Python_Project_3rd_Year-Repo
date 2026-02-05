-- ==============================
-- RESET DONATIONS & BLOOD STOCK
-- ==============================

-- 1️⃣ Clear all donation history
TRUNCATE TABLE donations;

-- 2️⃣ Reset blood stock quantities & status
UPDATE blood_stock
SET quantity = 0,
    status = 'Critical',
    updated_at = CURRENT_TIMESTAMP;

-- 3️⃣ Ensure all blood groups exist (safe to run multiple times)
INSERT IGNORE INTO blood_stock (blood_group, quantity, status) VALUES
('A+', 0, 'Critical'),
('A-', 0, 'Critical'),
('B+', 0, 'Critical'),
('B-', 0, 'Critical'),
('AB+', 0, 'Critical'),
('AB-', 0, 'Critical'),
('O+', 0, 'Critical'),
('O-', 0, 'Critical');

-- ==============================
-- RESET COMPLETE
-- ==============================

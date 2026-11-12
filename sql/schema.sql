-- DROPs, tables + constraints, ISA-enforcement triggers.
--   * Each non-trivial FD has a key as its determinant.
--   * ISA hierarchies (user_account -> viewer/shipper/carrier, vehicle -> box_truck/
--     refrigerated_van/rail_car) are TOTAL + DISJOINT. The discriminator (role / vehicle_type)
--     lives only on the supertype.
--     Disjointness and type-matching are enforced by the triggers.
--   * shipment.current_status is NULL until the first scan arrives.

-- =========================================================
-- DROP
-- =========================================================

DROP VIEW IF EXISTS v_departure_load;
DROP PROCEDURE IF EXISTS book_shipment;
DROP FUNCTION IF EXISTS scan_status_rank;
DROP TABLE IF EXISTS scan_event;
DROP TABLE IF EXISTS booking;
DROP TABLE IF EXISTS shipment;
DROP TABLE IF EXISTS departure;
DROP TABLE IF EXISTS rail_car;
DROP TABLE IF EXISTS refrigerated_van;
DROP TABLE IF EXISTS box_truck;
DROP TABLE IF EXISTS vehicle;
DROP TABLE IF EXISTS hub;
DROP TABLE IF EXISTS viewer;
DROP TABLE IF EXISTS shipper;
DROP TABLE IF EXISTS carrier;
DROP TABLE IF EXISTS user_account;


-- =========================================================
-- USER ACCOUNT
-- =========================================================

CREATE TABLE user_account (
    account_id INT AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,

    PRIMARY KEY (account_id),

    UNIQUE (username),

    CHECK (
        role IN ('Shipper', 'Carrier', 'Viewer')
    )
) ENGINE=InnoDB;


-- =========================================================
-- USER ACCOUNT SUBTYPES
-- =========================================================

CREATE TABLE viewer (
    account_id INT,

    PRIMARY KEY (account_id),

    FOREIGN KEY (account_id)
        REFERENCES user_account(account_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE shipper (
    account_id INT,
    shipper_name VARCHAR(100) NOT NULL,

    PRIMARY KEY (account_id),

    FOREIGN KEY (account_id)
        REFERENCES user_account(account_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


CREATE TABLE carrier (
    account_id INT,
    carrier_name VARCHAR(100) NOT NULL,

    PRIMARY KEY (account_id),

    FOREIGN KEY (account_id)
        REFERENCES user_account(account_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


-- =========================================================
-- HUB
-- =========================================================

CREATE TABLE hub (
    hub_id VARCHAR(3),
    hub_name VARCHAR(100) NOT NULL,
    region VARCHAR(20) NOT NULL,

    PRIMARY KEY (hub_id),

    UNIQUE (hub_name),

    CHECK (
        region IN (
            'Northeast',
            'Southeast',
            'Midwest',
            'Southwest',
            'West'
        )
    )
) ENGINE=InnoDB;


-- =========================================================
-- VEHICLE
-- =========================================================

CREATE TABLE vehicle (
    vehicle_id INT AUTO_INCREMENT,
    carrier_id INT NOT NULL,
    home_hub_id VARCHAR(3) NOT NULL,
    vehicle_type VARCHAR(30) NOT NULL,

    PRIMARY KEY (vehicle_id),

    FOREIGN KEY (carrier_id)
        REFERENCES carrier(account_id),

    FOREIGN KEY (home_hub_id)
        REFERENCES hub(hub_id),

    CHECK (
        vehicle_type IN ('BOX_TRUCK', 'REFRIGERATED_VAN', 'RAIL_CAR')
    )
) ENGINE=InnoDB;


-- =========================================================
-- VEHICLE SUBTYPES
-- =========================================================

CREATE TABLE box_truck (
    vehicle_id INT,
    cargo_volume_m3 DECIMAL(10,2) NOT NULL,
    gross_weight_rating_kg DECIMAL(10,2) NOT NULL,

    PRIMARY KEY (vehicle_id),

    FOREIGN KEY (vehicle_id)
        REFERENCES vehicle(vehicle_id)
        ON DELETE CASCADE,

    CHECK (cargo_volume_m3 > 0),

    CHECK (gross_weight_rating_kg > 0)
) ENGINE=InnoDB;


CREATE TABLE refrigerated_van (
    vehicle_id INT,
    min_temperature_c DECIMAL(5,2) NOT NULL,
    max_temperature_c DECIMAL(5,2) NOT NULL,
    payload_limit_kg DECIMAL(10,2) NOT NULL,

    PRIMARY KEY (vehicle_id),

    FOREIGN KEY (vehicle_id)
        REFERENCES vehicle(vehicle_id)
        ON DELETE CASCADE,

    CHECK (min_temperature_c <= max_temperature_c),

    CHECK (payload_limit_kg > 0)
) ENGINE=InnoDB;


CREATE TABLE rail_car (
    vehicle_id INT,
    axle_count INT NOT NULL,
    track_gauge_mm DECIMAL(10,2) NOT NULL,

    PRIMARY KEY (vehicle_id),

    FOREIGN KEY (vehicle_id)
        REFERENCES vehicle(vehicle_id)
        ON DELETE CASCADE,

    CHECK (axle_count > 0),

    CHECK (track_gauge_mm > 0)
) ENGINE=InnoDB;


-- =========================================================
-- DEPARTURE
-- =========================================================

CREATE TABLE departure (
    departure_id INT AUTO_INCREMENT,
    vehicle_id INT NOT NULL,
    origin_hub_id VARCHAR(3) NOT NULL,
    destination_hub_id VARCHAR(3) NOT NULL,
    departure_datetime DATETIME NOT NULL,
    maximum_weight_kg DECIMAL(10,2) NOT NULL,

    PRIMARY KEY (departure_id),

    FOREIGN KEY (vehicle_id)
        REFERENCES vehicle(vehicle_id),

    FOREIGN KEY (origin_hub_id)
        REFERENCES hub(hub_id),

    FOREIGN KEY (destination_hub_id)
        REFERENCES hub(hub_id),

    CHECK (maximum_weight_kg > 0),

    CHECK (origin_hub_id <> destination_hub_id)
) ENGINE=InnoDB;


-- =========================================================
-- SHIPMENT
-- =========================================================

CREATE TABLE shipment (
    shipment_id INT AUTO_INCREMENT,
    shipper_id INT NOT NULL,
    origin_hub_id VARCHAR(3) NOT NULL,
    destination_hub_id VARCHAR(3) NOT NULL,
    weight_kg DECIMAL(10,2) NOT NULL,
    promised_delivery_date DATE NOT NULL,
    current_status VARCHAR(30) NULL,        -- NULL = no scans yet
    delivery_outcome VARCHAR(20) NULL,      -- NULL until delivered

    PRIMARY KEY (shipment_id),

    FOREIGN KEY (shipper_id)
        REFERENCES shipper(account_id),

    FOREIGN KEY (origin_hub_id)
        REFERENCES hub(hub_id),

    FOREIGN KEY (destination_hub_id)
        REFERENCES hub(hub_id),

    CHECK (weight_kg > 0),

    CHECK (origin_hub_id <> destination_hub_id),

    CHECK (
        current_status IS NULL
        OR current_status IN (
            'RECEIVED',
            'IN_TRANSIT',
            'ARRIVED_AT_HUB',
            'OUT_FOR_DELIVERY',
            'DELIVERED'
        )
    ),

    CHECK (
        delivery_outcome IS NULL
        OR delivery_outcome IN ('ON_TIME', 'LATE')
    )
) ENGINE=InnoDB;


-- =========================================================
-- BOOKING
-- =========================================================

CREATE TABLE booking (
    shipment_id INT,
    departure_id INT NOT NULL,
    booked_at DATETIME NOT NULL,

    PRIMARY KEY (shipment_id),

    FOREIGN KEY (shipment_id)
        REFERENCES shipment(shipment_id)
        ON DELETE CASCADE,

    FOREIGN KEY (departure_id)
        REFERENCES departure(departure_id)
) ENGINE=InnoDB;


-- =========================================================
-- SCAN EVENT (weak entity of shipment)
-- =========================================================

CREATE TABLE scan_event (
    shipment_id INT,
    scan_sequence_no INT,
    scan_timestamp DATETIME NOT NULL,
    hub_id VARCHAR(3) NOT NULL,
    status VARCHAR(30) NOT NULL,

    PRIMARY KEY (shipment_id, scan_sequence_no),

    FOREIGN KEY (shipment_id)
        REFERENCES shipment(shipment_id)
        ON DELETE CASCADE,

    FOREIGN KEY (hub_id)
        REFERENCES hub(hub_id),

    CHECK (scan_sequence_no > 0),

    CHECK (
        status IN (
            'RECEIVED',
            'IN_TRANSIT',
            'ARRIVED_AT_HUB',
            'OUT_FOR_DELIVERY',
            'DELIVERED'
        )
    )
) ENGINE=InnoDB;


-- =========================================================
-- ISA ENFORCEMENT (disjoint + type must match the subtype table)
-- Needs a client that understands DELIMITER (DBeaver script mode, MySQL Shell \sql, mysql CLI).
-- =========================================================

DELIMITER //

-- ---- vehicle subtypes: a row is allowed only if vehicle.vehicle_type matches this table ----

CREATE TRIGGER trg_box_truck_isa
BEFORE INSERT ON box_truck
FOR EACH ROW
BEGIN
    IF NOT EXISTS (SELECT 1 FROM vehicle
                   WHERE vehicle_id = NEW.vehicle_id AND vehicle_type = 'BOX_TRUCK') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'ISA violation: vehicle is not of type BOX_TRUCK';
    END IF;
END//

CREATE TRIGGER trg_refrigerated_van_isa
BEFORE INSERT ON refrigerated_van
FOR EACH ROW
BEGIN
    IF NOT EXISTS (SELECT 1 FROM vehicle
                   WHERE vehicle_id = NEW.vehicle_id AND vehicle_type = 'REFRIGERATED_VAN') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'ISA violation: vehicle is not of type REFRIGERATED_VAN';
    END IF;
END//

CREATE TRIGGER trg_rail_car_isa
BEFORE INSERT ON rail_car
FOR EACH ROW
BEGIN
    IF NOT EXISTS (SELECT 1 FROM vehicle
                   WHERE vehicle_id = NEW.vehicle_id AND vehicle_type = 'RAIL_CAR') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'ISA violation: vehicle is not of type RAIL_CAR';
    END IF;
END//

-- The discriminator cannot change after creation (would orphan the subtype row).
CREATE TRIGGER trg_vehicle_type_fixed
BEFORE UPDATE ON vehicle
FOR EACH ROW
BEGIN
    IF NEW.vehicle_type <> OLD.vehicle_type THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'vehicle_type cannot be changed; delete and recreate the vehicle';
    END IF;
END//

-- ---- account subtypes: a row is allowed only if user_account.role matches this table ----

CREATE TRIGGER trg_viewer_isa
BEFORE INSERT ON viewer
FOR EACH ROW
BEGIN
    IF NOT EXISTS (SELECT 1 FROM user_account
                   WHERE account_id = NEW.account_id AND role = 'Viewer') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'ISA violation: account role is not Viewer';
    END IF;
END//

CREATE TRIGGER trg_shipper_isa
BEFORE INSERT ON shipper
FOR EACH ROW
BEGIN
    IF NOT EXISTS (SELECT 1 FROM user_account
                   WHERE account_id = NEW.account_id AND role = 'Shipper') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'ISA violation: account role is not Shipper';
    END IF;
END//

CREATE TRIGGER trg_carrier_isa
BEFORE INSERT ON carrier
FOR EACH ROW
BEGIN
    IF NOT EXISTS (SELECT 1 FROM user_account
                   WHERE account_id = NEW.account_id AND role = 'Carrier') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'ISA violation: account role is not Carrier';
    END IF;
END//

CREATE TRIGGER trg_account_role_fixed
BEFORE UPDATE ON user_account
FOR EACH ROW
BEGIN
    IF NEW.role <> OLD.role THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'role cannot be changed; delete and recreate the account';
    END IF;
END//

DELIMITER ;

-- =========================================================
-- VIEW
-- =========================================================

CREATE VIEW v_departure_load AS
SELECT d.departure_id,
       d.vehicle_id,
       d.origin_hub_id,
       d.destination_hub_id,
       d.departure_datetime,
       d.maximum_weight_kg,
       COALESCE(SUM(s.weight_kg), 0)                                      AS booked_weight_kg,
       d.maximum_weight_kg - COALESCE(SUM(s.weight_kg), 0)                AS remaining_kg,
       ROUND(100 * COALESCE(SUM(s.weight_kg), 0) / d.maximum_weight_kg, 2) AS utilization_pct
FROM departure d
LEFT JOIN booking  b ON b.departure_id = d.departure_id
LEFT JOIN shipment s ON s.shipment_id  = b.shipment_id
GROUP BY d.departure_id, d.vehicle_id, d.origin_hub_id, d.destination_hub_id,
         d.departure_datetime, d.maximum_weight_kg;
 
 
-- =========================================================
-- PROCEDURE: book a shipment onto a departure (atomic, capacity-safe)
--   * One transaction. The departure row is locked (FOR UPDATE), so two concurrent bookings
--     for the same departure run one after the other and cannot overbook it.
--   * The booked weight is an aggregate over the existing bookings, not a stored counter.
--   * Any failure rolls everything back and raises SQLSTATE 45000 with a readable message
--     (the app just prints it). Success returns one result row.
--   * Note: START TRANSACTION commits any transaction the caller already had open;
--     call it with autocommit on (the default) and nothing pending.
-- =========================================================
 
DELIMITER //
 
CREATE PROCEDURE book_shipment(IN p_shipment_id INT, IN p_departure_id INT)
BEGIN
    DECLARE v_ship_weight  DECIMAL(10,2);
    DECLARE v_ship_origin  VARCHAR(3);
    DECLARE v_ship_dest    VARCHAR(3);
    DECLARE v_max_weight   DECIMAL(10,2);
    DECLARE v_dep_origin   VARCHAR(3);
    DECLARE v_dep_dest     VARCHAR(3);
    DECLARE v_booked       DECIMAL(12,2);
    DECLARE v_msg          VARCHAR(128);
 
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
 
    START TRANSACTION;
 
    -- lock the shipment row and read it
    SELECT weight_kg, origin_hub_id, destination_hub_id
      INTO v_ship_weight, v_ship_origin, v_ship_dest
      FROM shipment
     WHERE shipment_id = p_shipment_id
       FOR UPDATE;
 
    IF v_ship_weight IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Booking rejected: shipment does not exist';
    END IF;
 
    -- lock the departure row: this is what serializes competing bookings
    SELECT maximum_weight_kg, origin_hub_id, destination_hub_id
      INTO v_max_weight, v_dep_origin, v_dep_dest
      FROM departure
     WHERE departure_id = p_departure_id
       FOR UPDATE;
 
    IF v_max_weight IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Booking rejected: departure does not exist';
    END IF;
 
    IF EXISTS (SELECT 1 FROM booking WHERE shipment_id = p_shipment_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Booking rejected: shipment is already booked';
    END IF;
 
    IF v_ship_origin <> v_dep_origin OR v_ship_dest <> v_dep_dest THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Booking rejected: shipment origin/destination do not match the departure';
    END IF;
 
    -- aggregate over the existing bookings (not a counter)
    SELECT COALESCE(SUM(s.weight_kg), 0)
      INTO v_booked
      FROM booking b
      JOIN shipment s ON s.shipment_id = b.shipment_id
     WHERE b.departure_id = p_departure_id;
 
    IF v_booked + v_ship_weight > v_max_weight THEN
        SET v_msg = CONCAT('Booking rejected: capacity exceeded (booked ', v_booked,
                           ' kg + shipment ', v_ship_weight, ' kg > max ', v_max_weight, ' kg)');
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
    END IF;
 
    INSERT INTO booking (shipment_id, departure_id, booked_at)
    VALUES (p_shipment_id, p_departure_id, NOW());
 
    COMMIT;
 
    SELECT p_shipment_id            AS shipment_id,
           p_departure_id           AS departure_id,
           v_booked + v_ship_weight AS booked_weight_kg,
           v_max_weight             AS maximum_weight_kg,
           'BOOKED'                 AS result;
END//
 
 
-- =========================================================
-- Helper: order of scan statuses (used by the chronology trigger).
-- IN_TRANSIT and ARRIVED_AT_HUB share a rank so a shipment can go
-- in transit -> arrived at hub -> in transit again over several legs.
-- =========================================================
 
CREATE FUNCTION scan_status_rank(p_status VARCHAR(30)) RETURNS INT
DETERMINISTIC
NO SQL
BEGIN
    RETURN CASE p_status
        WHEN 'RECEIVED'         THEN 1
        WHEN 'IN_TRANSIT'       THEN 2
        WHEN 'ARRIVED_AT_HUB'   THEN 2
        WHEN 'OUT_FOR_DELIVERY' THEN 3
        WHEN 'DELIVERED'        THEN 4
    END;
END//
 
 
-- =========================================================
-- TRIGGER: enforce scan chronology (BEFORE INSERT on scan_event)
--   1. scan_sequence_no must be exactly previous + 1 (first scan = 1)
--   2. nothing can be scanned after DELIVERED
--   3. timestamp cannot predate the shipment's most recent scan
--   4. status cannot regress (e.g. DELIVERED -> IN_TRANSIT is impossible)
--   5. DELIVERED requires an earlier IN_TRANSIT scan
-- =========================================================
 
CREATE TRIGGER trg_scan_chronology
BEFORE INSERT ON scan_event
FOR EACH ROW
BEGIN
    DECLARE v_last_seq    INT;
    DECLARE v_last_ts     DATETIME;
    DECLARE v_last_status VARCHAR(30);
 
    SET v_last_seq = (SELECT MAX(scan_sequence_no)
                        FROM scan_event
                       WHERE shipment_id = NEW.shipment_id);
 
    IF v_last_seq IS NULL THEN
        IF NEW.scan_sequence_no <> 1 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Scan rejected: the first scan of a shipment must have sequence number 1';
        END IF;
    ELSE
        IF NEW.scan_sequence_no <> v_last_seq + 1 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Scan rejected: sequence number must be the previous one plus 1';
        END IF;
 
        SELECT scan_timestamp, status
          INTO v_last_ts, v_last_status
          FROM scan_event
         WHERE shipment_id = NEW.shipment_id
           AND scan_sequence_no = v_last_seq;
 
        IF v_last_status = 'DELIVERED' THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Scan rejected: shipment is already delivered';
        END IF;
 
        IF NEW.scan_timestamp < v_last_ts THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Scan rejected: timestamp is earlier than the most recent scan';
        END IF;
 
        IF scan_status_rank(NEW.status) < scan_status_rank(v_last_status) THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Scan rejected: status cannot go backwards';
        END IF;
    END IF;
 
    IF NEW.status = 'DELIVERED'
       AND NOT EXISTS (SELECT 1 FROM scan_event
                        WHERE shipment_id = NEW.shipment_id AND status = 'IN_TRANSIT') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Scan rejected: a shipment cannot be delivered before it has been in transit';
    END IF;
END//
 
 
-- =========================================================
-- TRIGGER: keep current_status and flag on-time / late delivery
-- (AFTER INSERT on scan_event). On time = the DELIVERED scan falls on or
-- before the end of the promised delivery date (i.e. before the next midnight).
-- =========================================================
 
CREATE TRIGGER trg_scan_status_outcome
AFTER INSERT ON scan_event
FOR EACH ROW
BEGIN
    UPDATE shipment
       SET current_status   = NEW.status,
           delivery_outcome = CASE
               WHEN NEW.status <> 'DELIVERED' THEN delivery_outcome
               WHEN NEW.scan_timestamp < promised_delivery_date + INTERVAL 1 DAY THEN 'ON_TIME'
               ELSE 'LATE'
           END
     WHERE shipment_id = NEW.shipment_id;
END//
 
DELIMITER ;

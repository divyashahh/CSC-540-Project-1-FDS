-- 01_schema.sql
-- Freight Tracking and Delivery Management (CSC 540 Project 1), MariaDB 10.5
-- Contains: DROPs, tables + constraints, ISA-enforcement triggers.
-- Run this file first, then 02_sample_data.sql.
--
-- Design notes
--   * Every table is in BCNF (hence 3NF): each non-trivial FD has a key as its determinant.
--   * ISA hierarchies (user_account -> viewer/shipper/carrier, vehicle -> box_truck/
--     refrigerated_van/rail_car) are TOTAL + DISJOINT. The discriminator (role / vehicle_type)
--     lives only on the supertype. Subtype tables carry no copy of it, so no extra FD is created.
--     Disjointness and type-matching are enforced by the triggers at the bottom of this file.
--   * Total participation (every account/vehicle must have a subtype row) cannot be declared in
--     SQL; it is enforced in application code (create account/vehicle + subtype row together).
--   * shipment.current_status is NULL until the first scan arrives.

-- =========================================================
-- DROP (reverse dependency order; dropping a table also drops its triggers)
-- =========================================================

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
    address VARCHAR(255) NOT NULL,
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

-- STILL TO ADD to this file: the booking procedure and the two scan triggers
-- (status/late flag, chronology) required by the handout.
-- IDs are inserted explicitly; AUTO_INCREMENT then continues from the highest value
--
-- account_id and username are separate: username is just the login name (placeholders below;
-- password for all: password123).
-- NOT IN THE SAMPLE (placeholders): hub.address (city, state), usernames/passwords,
-- booking.booked_at (noon the day before departure).
-- Not stored on purpose: the "Carrier" column of DEPARTURES (derivable via vehicle.carrier_id).
-- shipment.current_status / delivery_outcome are NOT inserted; the scan triggers set them.

-- ---------- Hubs ----------
INSERT INTO hub (hub_id, hub_name, address, region) VALUES
('RDU', 'Raleigh Hub',     'Raleigh, NC',     'Southeast'),
('ATL', 'Atlanta Hub',     'Atlanta, GA',     'Southeast'),
('MIA', 'Miami Hub',       'Miami, FL',       'Southeast'),
('JFK', 'New York Hub',    'New York, NY',    'Northeast'),
('BOS', 'Boston Hub',      'Boston, MA',      'Northeast'),
('ORD', 'Chicago Hub',     'Chicago, IL',     'Midwest'),
('STL', 'St. Louis Hub',   'St. Louis, MO',   'Midwest'),
('DFW', 'Dallas Hub',      'Dallas, TX',      'Southwest'),
('PHX', 'Phoenix Hub',     'Phoenix, AZ',     'Southwest'),
('LAX', 'Los Angeles Hub', 'Los Angeles, CA', 'West'),
('SEA', 'Seattle Hub',     'Seattle, WA',     'West');

-- ---------- Accounts (user_account first, then the subtype tables) ----------
INSERT INTO user_account (account_id, username, password_hash, role) VALUES
(1,  'piedmont',    SHA2('password123', 256), 'Carrier'),
(2,  'atlantic',    SHA2('password123', 256), 'Carrier'),
(3,  'plains',    SHA2('password123', 256), 'Carrier'),
(4, 'triangle',   SHA2('password123', 256), 'Shipper'),
(5, 'oakcity',   SHA2('password123', 256), 'Shipper'),
(6, 'carolina',   SHA2('password123', 256), 'Shipper'),
(7, 'coastal',   SHA2('password123', 256), 'Shipper'),
(8, 'fedex', SHA2('password123', 256), 'Viewer');

INSERT INTO carrier (account_id, carrier_name) VALUES
(1, 'Piedmont Freight Lines'),
(2, 'Atlantic Coast Haulers'),
(3, 'Plains Rail Co');

INSERT INTO shipper (account_id, shipper_name) VALUES
(4, 'Triangle Textiles'),
(5, 'Oak City Electronics'),
(6, 'Carolina Produce Co'),
(7, 'Coastal Furniture');

INSERT INTO viewer (account_id) VALUES
(8);

-- ---------- Vehicles (supertype, then subtypes) ----------
INSERT INTO vehicle (vehicle_id, carrier_id, home_hub_id, vehicle_type) VALUES
(101, 1, 'RDU', 'BOX_TRUCK'),
(102, 1, 'ATL', 'REFRIGERATED_VAN'),
(103, 1, 'RDU', 'BOX_TRUCK'),
(201, 2, 'JFK', 'BOX_TRUCK'),
(202, 2, 'ORD', 'BOX_TRUCK'),
(203, 2, 'ORD', 'REFRIGERATED_VAN'),
(301, 3, 'DFW', 'RAIL_CAR');

INSERT INTO box_truck (vehicle_id, cargo_volume_m3, gross_weight_rating_kg) VALUES
(101, 45.0, 12000),
(103, 30.0,  8000),
(201, 40.0, 10000),
(202, 50.0, 14000);

INSERT INTO refrigerated_van (vehicle_id, min_temperature_c, max_temperature_c, payload_limit_kg) VALUES
(102, -18.0,   4.0, 4000),
(203, -25.0, -10.0, 3000);

INSERT INTO rail_car (vehicle_id, axle_count, track_gauge_mm) VALUES
(301, 4, 1435);

-- ---------- Departures ----------
INSERT INTO departure (departure_id, vehicle_id, origin_hub_id, destination_hub_id, departure_datetime, maximum_weight_kg) VALUES
(1, 101, 'RDU', 'ATL', '2026-03-01 22:00:00', 10000),
(2, 102, 'ATL', 'MIA', '2026-03-04 06:00:00',  4000),
(3, 201, 'JFK', 'BOS', '2026-03-02 09:00:00',  8000),
(4, 202, 'ORD', 'DFW', '2026-03-02 20:00:00', 12000),
(5, 301, 'DFW', 'LAX', '2026-03-03 08:00:00',  9000),
(6, 101, 'RDU', 'ATL', '2026-03-07 22:00:00', 10000),
(7, 103, 'RDU', 'ATL', '2026-10-29 09:00:00',  2000),
(8, 101, 'RDU', 'ATL', '2026-10-30 09:00:00',  8000),
(9, 101, 'RDU', 'ATL', '2026-01-10 09:00:00', 10000),
(10, 101, 'RDU', 'ATL', '2026-02-10 09:00:00', 10000);

-- ---------- Shipments ----------
-- (current_status / delivery_outcome are filled in by the scan triggers)
INSERT INTO shipment (shipment_id, shipper_id, origin_hub_id, destination_hub_id, weight_kg, promised_delivery_date) VALUES
(1, 4, 'RDU', 'ATL', 3000, '2026-03-04'),
(2, 5, 'JFK', 'BOS', 2500, '2026-03-02'),
(3, 6, 'RDU', 'ATL', 2000, '2026-03-02'),
(4, 4, 'JFK', 'BOS', 1500, '2026-03-05'),
(5, 5, 'ATL', 'MIA', 2000, '2026-03-07'),
(6, 6, 'ATL', 'MIA', 1700, '2026-03-06'),
(7, 6, 'ORD', 'DFW', 3000, '2026-03-05'),
(8, 6, 'ORD', 'DFW', 4000, '2026-03-03'),
(9, 4, 'RDU', 'ATL', 2500, '2026-03-05'),
(10, 6, 'RDU', 'ATL', 2800, '2026-03-11'),
(11, 5, 'DFW', 'LAX', 3500, '2026-03-05'),
(12, 4, 'RDU', 'ATL', 1000, '2026-11-02'),
(13, 4, 'RDU', 'ATL', 1000, '2026-11-02'),
(14, 4, 'RDU', 'ATL',  500, '2026-11-03'),
(15, 4, 'RDU', 'ATL',  500, '2026-11-02'),
(16, 4, 'RDU', 'ATL',  500, '2026-10-30'),
(17, 4, 'RDU', 'ATL', 1000, '2026-10-31'),
(18, 4, 'RDU', 'ATL', 1000, '2026-11-02'),
(19, 4, 'RDU', 'ATL', 1000, '2026-11-03'),
(20, 4, 'RDU', 'ATL', 1000, '2026-01-11'),
(21, 4, 'RDU', 'ATL', 1000, '2026-01-12'),
(22, 4, 'RDU', 'ATL', 1000, '2026-02-11'),
(23, 4, 'RDU', 'ATL', 1000, '2026-02-12');

-- ---------- Bookings (S14 is intentionally unbooked) ----------
INSERT INTO booking (shipment_id, departure_id, booked_at) VALUES
(1, 1,  '2026-02-28 12:00:00'),
(3, 1,  '2026-02-28 12:00:00'),
(9, 1,  '2026-02-28 12:00:00'),
(2, 3,  '2026-03-01 12:00:00'),
(4, 3,  '2026-03-01 12:00:00'),
(5, 2,  '2026-03-03 12:00:00'),
(6, 2,  '2026-03-03 12:00:00'),
(7, 4,  '2026-03-01 12:00:00'),
(8, 4,  '2026-03-01 12:00:00'),
(10, 6,  '2026-03-06 12:00:00'),
(11, 5,  '2026-03-02 12:00:00'),
(12, 7,  '2026-10-28 12:00:00'),
(13, 7,  '2026-10-28 12:00:00'),
(15, 8,  '2026-10-29 12:00:00'),
(16, 8,  '2026-10-29 12:00:00'),
(17, 8,  '2026-10-29 12:00:00'),
(18, 8,  '2026-10-29 12:00:00'),
(19, 8,  '2026-10-29 12:00:00'),
(20, 9,  '2026-01-09 12:00:00'),
(21, 9,  '2026-01-09 12:00:00'),
(22, 10, '2026-02-09 12:00:00'),
(23, 10, '2026-02-09 12:00:00');

-- ---------- Scan events (inserted in order per shipment so the triggers accept them) ----------
INSERT INTO scan_event (shipment_id, scan_sequence_no, status, hub_id, scan_timestamp) VALUES
(1,  1, 'RECEIVED',         'RDU', '2026-03-01 21:00:00'),
(1,  2, 'IN_TRANSIT',       'RDU', '2026-03-01 22:05:00'),
(1,  3, 'OUT_FOR_DELIVERY', 'ATL', '2026-03-02 12:30:00'),
(1,  4, 'DELIVERED',        'ATL', '2026-03-02 14:00:00'),
(2,  1, 'RECEIVED',         'JFK', '2026-03-01 15:00:00'),
(2,  2, 'IN_TRANSIT',       'JFK', '2026-03-02 09:10:00'),
(2,  3, 'OUT_FOR_DELIVERY', 'BOS', '2026-03-03 08:00:00'),
(2,  4, 'DELIVERED',        'BOS', '2026-03-03 11:30:00'),
(3,  1, 'RECEIVED',         'RDU', '2026-03-01 19:15:00'),
(3,  2, 'IN_TRANSIT',       'RDU', '2026-03-01 22:05:00'),
(3,  3, 'OUT_FOR_DELIVERY', 'ATL', '2026-03-02 18:00:00'),
(3,  4, 'DELIVERED',        'ATL', '2026-03-02 20:45:00'),
(4,  1, 'RECEIVED',         'JFK', '2026-03-01 16:00:00'),
(4,  2, 'IN_TRANSIT',       'JFK', '2026-03-02 09:10:00'),
(5,  1, 'RECEIVED',         'ATL', '2026-03-03 15:00:00'),
(5,  2, 'IN_TRANSIT',       'ATL', '2026-03-04 06:10:00'),
(5,  3, 'OUT_FOR_DELIVERY', 'MIA', '2026-03-06 08:00:00'),
(5,  4, 'DELIVERED',        'MIA', '2026-03-06 12:15:00'),
(6,  1, 'RECEIVED',         'ATL', '2026-03-03 16:30:00'),
(6,  2, 'IN_TRANSIT',       'ATL', '2026-03-04 06:10:00'),
(6,  3, 'OUT_FOR_DELIVERY', 'MIA', '2026-03-07 09:00:00'),
(6,  4, 'DELIVERED',        'MIA', '2026-03-07 16:20:00'),
(7,  1, 'RECEIVED',         'ORD', '2026-03-02 11:00:00'),
(7,  2, 'IN_TRANSIT',       'ORD', '2026-03-02 20:15:00'),
(7,  3, 'OUT_FOR_DELIVERY', 'DFW', '2026-03-04 07:30:00'),
(7,  4, 'DELIVERED',        'DFW', '2026-03-04 11:00:00'),
(8,  1, 'RECEIVED',         'ORD', '2026-03-02 12:30:00'),
(8,  2, 'IN_TRANSIT',       'ORD', '2026-03-02 20:15:00'),
(8,  3, 'OUT_FOR_DELIVERY', 'DFW', '2026-03-05 07:00:00'),
(8,  4, 'DELIVERED',        'DFW', '2026-03-05 09:45:00'),
(9,  1, 'RECEIVED',         'RDU', '2026-03-01 18:40:00'),
(9,  2, 'IN_TRANSIT',       'RDU', '2026-03-01 22:05:00'),
(9,  3, 'OUT_FOR_DELIVERY', 'ATL', '2026-03-03 09:00:00'),
(9,  4, 'DELIVERED',        'ATL', '2026-03-03 12:00:00'),
(10, 1, 'RECEIVED',         'RDU', '2026-03-07 15:00:00'),
(10, 2, 'IN_TRANSIT',       'RDU', '2026-03-07 22:10:00'),
(10, 3, 'OUT_FOR_DELIVERY', 'ATL', '2026-03-10 08:00:00'),
(10, 4, 'DELIVERED',        'ATL', '2026-03-10 10:30:00'),
(11, 1, 'RECEIVED',         'DFW', '2026-03-02 19:00:00'),
(11, 2, 'IN_TRANSIT',       'DFW', '2026-03-03 08:30:00'),
(11, 3, 'OUT_FOR_DELIVERY', 'LAX', '2026-03-07 06:00:00'),
(11, 4, 'DELIVERED',        'LAX', '2026-03-07 08:30:00'),
(12, 1, 'RECEIVED',         'RDU', '2026-10-28 16:00:00'),
(13, 1, 'RECEIVED',         'RDU', '2026-10-28 16:30:00'),
(15, 1, 'RECEIVED',         'RDU', '2026-10-29 16:00:00'),
(16, 1, 'RECEIVED',         'RDU', '2026-10-29 17:00:00'),
(16, 2, 'IN_TRANSIT',       'RDU', '2026-10-30 09:10:00'),
(17, 1, 'RECEIVED',         'RDU', '2026-10-29 17:15:00'),
(17, 2, 'IN_TRANSIT',       'RDU', '2026-10-30 09:10:00'),
(18, 1, 'RECEIVED',         'RDU', '2026-10-29 17:30:00'),
(18, 2, 'IN_TRANSIT',       'RDU', '2026-10-30 09:10:00'),
(19, 1, 'RECEIVED',         'RDU', '2026-10-29 17:45:00'),
(19, 2, 'IN_TRANSIT',       'RDU', '2026-10-30 09:10:00'),
(20, 1, 'RECEIVED',         'RDU', '2026-01-09 16:00:00'),
(20, 2, 'IN_TRANSIT',       'RDU', '2026-01-10 09:10:00'),
(20, 3, 'OUT_FOR_DELIVERY', 'ATL', '2026-01-11 08:00:00'),
(20, 4, 'DELIVERED',        'ATL', '2026-01-11 10:00:00'),
(21, 1, 'RECEIVED',         'RDU', '2026-01-09 16:30:00'),
(21, 2, 'IN_TRANSIT',       'RDU', '2026-01-10 09:10:00'),
(21, 3, 'OUT_FOR_DELIVERY', 'ATL', '2026-01-11 08:15:00'),
(21, 4, 'DELIVERED',        'ATL', '2026-01-11 11:00:00'),
(22, 1, 'RECEIVED',         'RDU', '2026-02-09 16:00:00'),
(22, 2, 'IN_TRANSIT',       'RDU', '2026-02-10 09:10:00'),
(22, 3, 'OUT_FOR_DELIVERY', 'ATL', '2026-02-11 08:00:00'),
(22, 4, 'DELIVERED',        'ATL', '2026-02-11 10:00:00'),
(23, 1, 'RECEIVED',         'RDU', '2026-02-09 16:30:00'),
(23, 2, 'IN_TRANSIT',       'RDU', '2026-02-10 09:10:00'),
(23, 3, 'OUT_FOR_DELIVERY', 'ATL', '2026-02-13 08:00:00'),
(23, 4, 'DELIVERED',        'ATL', '2026-02-13 11:00:00');

-- ---------- Sanity checks (run by hand) ----------
-- SELECT COUNT(*) FROM scan_event;   -- 69
-- SELECT d.departure_id, SUM(s.weight_kg) AS booked_kg, d.maximum_weight_kg
--   FROM departure d JOIN booking b ON b.departure_id = d.departure_id
--   JOIN shipment s ON s.shipment_id = b.shipment_id
--   GROUP BY d.departure_id, d.maximum_weight_kg;      -- departure 1 = 7500/10000, departure 7 = 2000/2000
-- Once the scan triggers exist, SELECT shipment_id, current_status, delivery_outcome FROM shipment:
--   ON_TIME: shipments 1, 3, 5, 7, 9, 10, 20, 21, 22     LATE: 2, 6, 8, 11, 23
--   no outcome: 4, 12-19 (shipment 14 has no scans, so its status stays NULL)
-- Without the scan triggers, current_status / delivery_outcome stay NULL for every shipment.
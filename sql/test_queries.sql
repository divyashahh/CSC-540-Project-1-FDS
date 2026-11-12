-- Manual tests for the booking procedure and the scan triggers, on the sample data.
-- Rerun schema.sql and sample_data.sql to get back to a clean state.

-- ===== Booking procedure =====
CALL book_shipment(14, 7);   -- REJECT: capacity exceeded (departure 7 is full: 2000 + 500 > 2000)
CALL book_shipment(14, 3);   -- REJECT: shipment origin/destination do not match the departure
CALL book_shipment(1, 8);    -- REJECT: shipment 1 is already booked
CALL book_shipment(999, 8);  -- REJECT: shipment does not exist
CALL book_shipment(14, 8);   -- OK: departure 8 goes from 4000 to 4500 of 8000 kg
SELECT departure_id, booked_weight_kg, remaining_kg, utilization_pct
FROM v_departure_load WHERE departure_id IN (7, 8);   -- 7: 2000/2000   8: 4500/8000 (56.25 %)

-- ===== Scan triggers (shipment 4: last scan is #2 IN_TRANSIT at 2026-03-02 09:10, promised 2026-03-05) =====
INSERT INTO scan_event VALUES (4, 3, '2026-03-01 00:00:00', 'BOS', 'OUT_FOR_DELIVERY');  -- REJECT: timestamp earlier than last scan
INSERT INTO scan_event VALUES (4, 3, '2026-03-03 08:00:00', 'BOS', 'RECEIVED');          -- REJECT: status goes backwards
INSERT INTO scan_event VALUES (4, 5, '2026-03-03 08:00:00', 'BOS', 'OUT_FOR_DELIVERY');  -- REJECT: sequence number skips (must be 3)
INSERT INTO scan_event VALUES (4, 3, '2026-03-03 09:00:00', 'BOS', 'OUT_FOR_DELIVERY');  -- OK
SELECT shipment_id, current_status, delivery_outcome FROM shipment WHERE shipment_id = 4; -- OUT_FOR_DELIVERY, NULL
INSERT INTO scan_event VALUES (4, 4, '2026-03-06 10:00:00', 'BOS', 'DELIVERED');         -- OK: after 2026-03-05 -> LATE
SELECT shipment_id, current_status, delivery_outcome FROM shipment WHERE shipment_id = 4; -- DELIVERED, LATE
INSERT INTO scan_event VALUES (4, 5, '2026-03-07 10:00:00', 'BOS', 'IN_TRANSIT');        -- REJECT: already delivered

-- Shipment 14 has no scans yet (it was just booked above)
INSERT INTO scan_event VALUES (14, 1, '2026-10-29 10:00:00', 'RDU', 'DELIVERED');        -- REJECT: not in transit yet
INSERT INTO scan_event VALUES (14, 1, '2026-10-29 10:00:00', 'RDU', 'RECEIVED');         -- OK
SELECT shipment_id, current_status, delivery_outcome FROM shipment WHERE shipment_id = 14; -- RECEIVED, NULL

-- ===== ISA triggers =====
INSERT INTO rail_car VALUES (101, 4, 1435);   -- REJECT: vehicle 101 is a BOX_TRUCK, not a RAIL_CAR
UPDATE vehicle SET vehicle_type = 'RAIL_CAR' WHERE vehicle_id = 101;   -- REJECT: type cannot change
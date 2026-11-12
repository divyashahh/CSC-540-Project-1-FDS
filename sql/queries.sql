-- ---------------------------------------------------------
-- Query 1: number of vehicles of each type owned by each carrier
-- Expected: carrier 1 -> BOX_TRUCK 2, REFRIGERATED_VAN 1; carrier 2 -> BOX_TRUCK 2,
--           REFRIGERATED_VAN 1; carrier 3 -> RAIL_CAR 1
-- ---------------------------------------------------------
SELECT c.account_id   AS carrier_id,
       c.carrier_name,
       v.vehicle_type,
       COUNT(*)       AS vehicle_count
FROM carrier c
JOIN vehicle v ON v.carrier_id = c.account_id
GROUP BY c.account_id, c.carrier_name, v.vehicle_type
ORDER BY c.account_id, v.vehicle_type;


-- ---------------------------------------------------------
-- Query 2: for each lane, rank departures by weight utilization (window function)
-- Lane = (origin hub, destination hub). Rank 1 = most heavily loaded departure on that lane.
-- Departures with no bookings show 0 % utilization.
-- Expected, lane 
--           RDU->ATL: departure 7 (100 %) rank 1, departure 1 (75 %) rank 2,
--           		   departure 8 (50 %) rank 3, departure 6 (28 %) rank 4, 
--                     departures 9 and 10 (20 %) tied rank 5
--           ATL->MIA: dep 2 = 92.5 %, 
--           DFW->LAX: dep 5 = 38.89 %
--           JFK->BOS: dep 3 = 50 %
--           ORD->DFW: dep 4 = 58.33 %,
-- ---------------------------------------------------------
SELECT origin_hub_id,
       destination_hub_id,
       departure_id,
       departure_datetime,
       booked_weight_kg,
       maximum_weight_kg,
       utilization_pct,
       RANK() OVER (PARTITION BY origin_hub_id, destination_hub_id
                    ORDER BY utilization_pct DESC) AS lane_rank
FROM v_departure_load
ORDER BY origin_hub_id, destination_hub_id, lane_rank, departure_id;


-- ---------------------------------------------------------
-- Query 3: time elapsed between consecutive scan events of one shipment (window function LAG)
-- Parameter: shipment id.   Try 1 (4 scans) or 4 (2 scans).
-- Expected for shipment 1: first scan has NULL, then 65, 865 and 90 minutes.
-- ---------------------------------------------------------
SET @shipment_id = 1;

SELECT shipment_id,
       scan_sequence_no,
       status,
       hub_id,
       scan_timestamp,
       LAG(scan_timestamp) OVER w AS previous_scan_time,
       LAG(hub_id)         OVER w AS previous_hub,
       TIMESTAMPDIFF(MINUTE, LAG(scan_timestamp) OVER w, scan_timestamp)             AS minutes_since_previous,
       ROUND(TIMESTAMPDIFF(MINUTE, LAG(scan_timestamp) OVER w, scan_timestamp) / 60, 2) AS hours_since_previous
FROM scan_event
WHERE shipment_id = @shipment_id
WINDOW w AS (PARTITION BY shipment_id ORDER BY scan_sequence_no)
ORDER BY scan_sequence_no;


-- ---------------------------------------------------------
-- Query 4: per carrier, running total of delivered weight by week (window function SUM OVER)
-- A shipment counts in the week (Monday start) of its DELIVERED scan; its carrier is the one
-- that owns the vehicle of the departure it was booked on.
-- Expected: carrier 1: week 2026-01-05 2000 (cum 2000), 2026-02-09 2000 (cum 4000),
--                      2026-03-02 11200 (cum 15200), 2026-03-09 2800 (cum 18000)
--           carrier 2: week 2026-03-02 9500 (cum 9500)
--           carrier 3: week 2026-03-02 3500 (cum 3500)
-- ---------------------------------------------------------
WITH delivered AS (
    SELECT v.carrier_id,
           DATE_SUB(DATE(sc.scan_timestamp), INTERVAL WEEKDAY(sc.scan_timestamp) DAY) AS week_start,
           s.weight_kg
    FROM scan_event sc
    JOIN shipment  s ON s.shipment_id   = sc.shipment_id
    JOIN booking   b ON b.shipment_id   = s.shipment_id
    JOIN departure d ON d.departure_id  = b.departure_id
    JOIN vehicle   v ON v.vehicle_id    = d.vehicle_id
    WHERE sc.status = 'DELIVERED'
),
weekly AS (
    SELECT carrier_id, week_start, SUM(weight_kg) AS delivered_kg
    FROM delivered
    GROUP BY carrier_id, week_start
)
SELECT w.carrier_id,
       c.carrier_name,
       w.week_start,
       w.delivered_kg,
       SUM(w.delivered_kg) OVER (PARTITION BY w.carrier_id
                                 ORDER BY w.week_start
                                 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_delivered_kg
FROM weekly w
JOIN carrier c ON c.account_id = w.carrier_id
ORDER BY w.carrier_id, w.week_start;


-- ---------------------------------------------------------
-- Query 5: departures carrying shipments of at least two different shippers
-- Expected: departures 1, 2 and 3, each with 2 distinct shippers
-- ---------------------------------------------------------
SELECT b.departure_id,
       COUNT(DISTINCT s.shipper_id) AS distinct_shippers
FROM booking b
JOIN shipment s ON s.shipment_id = b.shipment_id
GROUP BY b.departure_id
HAVING COUNT(DISTINCT s.shipper_id) >= 2
ORDER BY b.departure_id;


-- ---------------------------------------------------------
-- Query 6: shipments with no scan events recorded
-- Expected: only shipment 14 (shipper 4, Triangle Textiles, RDU -> ATL, promised 2026-11-03)
-- ---------------------------------------------------------
SELECT s.shipment_id,
       s.shipper_id,
       sh.shipper_name,
       s.origin_hub_id,
       s.destination_hub_id,
       s.promised_delivery_date
FROM shipment s
JOIN shipper sh ON sh.account_id = s.shipper_id
WHERE NOT EXISTS (SELECT 1 FROM scan_event e WHERE e.shipment_id = s.shipment_id)
ORDER BY s.shipment_id;
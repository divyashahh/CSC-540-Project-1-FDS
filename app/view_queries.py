# view_queries.py - "View Queries" root-menu option: the 6 required analytical queries,
# numbered in the same order as the handout. Same SQL as 03_queries.sql, with %s parameters.

from .common import ask_int, run_menu, show

Q1 = """
SELECT c.account_id AS carrier_id, c.carrier_name, v.vehicle_type, COUNT(*) AS vehicle_count
FROM carrier c JOIN vehicle v ON v.carrier_id = c.account_id
GROUP BY c.account_id, c.carrier_name, v.vehicle_type
ORDER BY c.account_id, v.vehicle_type
"""

Q2 = """
SELECT * FROM (
    SELECT origin_hub_id, destination_hub_id, departure_id, departure_datetime,
           booked_weight_kg, maximum_weight_kg, utilization_pct,
           RANK() OVER (PARTITION BY origin_hub_id, destination_hub_id
                        ORDER BY utilization_pct DESC) AS lane_rank
    FROM v_departure_load
) ranked
WHERE lane_rank <= %s
ORDER BY origin_hub_id, destination_hub_id, lane_rank, departure_id
"""

Q3 = """
SELECT shipment_id, scan_sequence_no, status, hub_id, scan_timestamp,
       LAG(scan_timestamp) OVER w AS previous_scan_time,
       LAG(hub_id) OVER w AS previous_hub,
       TIMESTAMPDIFF(MINUTE, LAG(scan_timestamp) OVER w, scan_timestamp) AS minutes_since_previous,
       ROUND(TIMESTAMPDIFF(MINUTE, LAG(scan_timestamp) OVER w, scan_timestamp) / 60, 2) AS hours_since_previous
FROM scan_event
WHERE shipment_id = %s
WINDOW w AS (PARTITION BY shipment_id ORDER BY scan_sequence_no)
ORDER BY scan_sequence_no
"""

Q4 = """
WITH delivered AS (
    SELECT v.carrier_id,
           DATE_SUB(DATE(sc.scan_timestamp), INTERVAL WEEKDAY(sc.scan_timestamp) DAY) AS week_start,
           s.weight_kg
    FROM scan_event sc
    JOIN shipment  s ON s.shipment_id  = sc.shipment_id
    JOIN booking   b ON b.shipment_id  = s.shipment_id
    JOIN departure d ON d.departure_id = b.departure_id
    JOIN vehicle   v ON v.vehicle_id   = d.vehicle_id
    WHERE sc.status = 'DELIVERED'
),
weekly AS (
    SELECT carrier_id, week_start, SUM(weight_kg) AS delivered_kg
    FROM delivered GROUP BY carrier_id, week_start
)
SELECT w.carrier_id, c.carrier_name, w.week_start, w.delivered_kg,
       SUM(w.delivered_kg) OVER (PARTITION BY w.carrier_id ORDER BY w.week_start
                                 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_delivered_kg
FROM weekly w JOIN carrier c ON c.account_id = w.carrier_id
ORDER BY w.carrier_id, w.week_start
"""

Q5 = """
SELECT b.departure_id, COUNT(DISTINCT s.shipper_id) AS distinct_shippers
FROM booking b JOIN shipment s ON s.shipment_id = b.shipment_id
GROUP BY b.departure_id
HAVING COUNT(DISTINCT s.shipper_id) >= 2
ORDER BY b.departure_id
"""

Q6 = """
SELECT s.shipment_id, s.shipper_id, sh.shipper_name, s.origin_hub_id, s.destination_hub_id,
       s.promised_delivery_date
FROM shipment s JOIN shipper sh ON sh.account_id = s.shipper_id
WHERE NOT EXISTS (SELECT 1 FROM scan_event e WHERE e.shipment_id = s.shipment_id)
ORDER BY s.shipment_id
"""


def q1():
    show(Q1)


def q2():
    n = ask_int("Show the top N departures per lane (blank = all)", blank_ok=True)
    show(Q2, (n if n else 10**9,))


def q3():
    show(Q3, (ask_int("Shipment id"),))


def q4():
    show(Q4)


def q5():
    show(Q5)


def q6():
    show(Q6)


def menu():
    run_menu("View Queries", [
        ("Number of vehicles of each type per carrier", q1),
        ("Departures ranked by weight utilization per lane", q2),
        ("Dwell time between consecutive scans (prompts for a shipment)", q3),
        ("Running total of delivered weight by week per carrier", q4),
        ("Departures carrying shipments of at least two different shippers", q5),
        ("Shipments with no scan events", q6),
    ])
# carrier.py - Carrier menu. Ownership rules (own vehicles/departures only, scans only for
# departures it operates) are enforced here by filtering on vehicle.carrier_id = account.

from . import db
from .common import (ask, ask_choice, ask_datetime, ask_decimal, ask_hub, ask_int,
                    run_menu, show)

# type label -> (subtype table, [(column, prompt, kind)])
VEHICLE_TYPES = {
    "BOX_TRUCK": ("box_truck", [("cargo_volume_m3", "Cargo volume (m3)", "dec"),
                                ("gross_weight_rating_kg", "Gross weight rating (kg)", "dec")]),
    "REFRIGERATED_VAN": ("refrigerated_van", [("min_temperature_c", "Min temperature (C)", "dec"),
                                              ("max_temperature_c", "Max temperature (C)", "dec"),
                                              ("payload_limit_kg", "Payload limit (kg)", "dec")]),
    "RAIL_CAR": ("rail_car", [("axle_count", "Axle count", "int"),
                              ("track_gauge_mm", "Track gauge (mm)", "dec")]),
}
STATUSES = ["RECEIVED", "IN_TRANSIT", "ARRIVED_AT_HUB", "OUT_FOR_DELIVERY", "DELIVERED"]


def menu(acct):
    run_menu(f"Carrier: {acct[1]}", [
        ("Manage Vehicles", lambda: vehicles_menu(acct)),
        ("Manage Departures", lambda: departures_menu(acct)),
        ("Post Scan Event", lambda: post_scan(acct)),
        ("Reports: Weight utilization | On-time rate", lambda: reports(acct)),
    ], back_label="Log out")


def _ask_value(prompt, kind, blank_ok=False):
    if kind == "int":
        return ask_int(prompt, blank_ok=blank_ok)
    return ask_decimal(prompt, blank_ok=blank_ok)


def vehicles_menu(acct):
    run_menu("Vehicles: Create/Update", [
        ("List my vehicles", lambda: list_vehicles(acct)),
        ("Create a vehicle", lambda: create_vehicle(acct)),
        ("Update a vehicle", lambda: update_vehicle(acct)),
    ])


def list_vehicles(acct):
    show("SELECT v.vehicle_id, v.vehicle_type, v.home_hub_id AS home_hub, "
         "CASE v.vehicle_type "
         " WHEN 'BOX_TRUCK' THEN CONCAT(b.cargo_volume_m3, ' m3, rating ', b.gross_weight_rating_kg, ' kg') "
         " WHEN 'REFRIGERATED_VAN' THEN CONCAT(r.min_temperature_c, ' to ', r.max_temperature_c, "
         "   ' C, payload ', r.payload_limit_kg, ' kg') "
         " WHEN 'RAIL_CAR' THEN CONCAT(rc.axle_count, ' axles, ', rc.track_gauge_mm, ' mm gauge') "
         "END AS details "
         "FROM vehicle v "
         "LEFT JOIN box_truck b ON b.vehicle_id = v.vehicle_id "
         "LEFT JOIN refrigerated_van r ON r.vehicle_id = v.vehicle_id "
         "LEFT JOIN rail_car rc ON rc.vehicle_id = v.vehicle_id "
         "WHERE v.carrier_id = %s ORDER BY v.vehicle_id", (acct[0],))


def create_vehicle(acct):
    vtype = ask_choice("Vehicle type", list(VEHICLE_TYPES))
    table, attrs = VEHICLE_TYPES[vtype]
    home = ask_hub("Home hub code")
    values = [_ask_value(p, k) for _, p, k in attrs]
    # vehicle row + subtype row together; the ISA trigger checks the type matches.
    with db.transaction() as cur:
        cur.execute("INSERT INTO vehicle (carrier_id, home_hub_id, vehicle_type) VALUES (%s, %s, %s)",
                    (acct[0], home, vtype))
        vid = cur.lastrowid
        cols = ", ".join(c for c, _, _ in attrs)
        cur.execute(f"INSERT INTO {table} (vehicle_id, {cols}) VALUES (%s{', %s' * len(attrs)})",
                    [vid] + values)
    print(f"  Vehicle {vid} ({vtype}) created.")


def _my_vehicle_type(acct, vid):
    _, rows = db.query("SELECT vehicle_type FROM vehicle WHERE vehicle_id = %s AND carrier_id = %s",
                       (vid, acct[0]))
    return rows[0][0] if rows else None


def update_vehicle(acct):
    list_vehicles(acct)
    vid = ask_int("Vehicle id to update")
    vtype = _my_vehicle_type(acct, vid)
    if vtype is None:
        print("  That is not one of your vehicles.")
        return
    table, attrs = VEHICLE_TYPES[vtype]
    field = ask_choice("Field to change", ["Home hub"] + [p for _, p, _ in attrs])
    if field == "Home hub":
        hub = ask_hub("New home hub code")
        db.execute("UPDATE vehicle SET home_hub_id = %s WHERE vehicle_id = %s AND carrier_id = %s",
                   (hub, vid, acct[0]))
    else:
        col, prompt, kind = next(a for a in attrs if a[1] == field)
        val = _ask_value(f"New {prompt}", kind)
        db.execute(f"UPDATE {table} SET {col} = %s WHERE vehicle_id = %s", (val, vid))
    print(f"  Vehicle {vid} updated.")


def departures_menu(acct):
    run_menu("Departures: Create/Update", [
        ("List my departures", lambda: list_departures(acct)),
        ("Schedule a departure", lambda: create_departure(acct)),
        ("Update a departure", lambda: update_departure(acct)),
    ])


def list_departures(acct):
    show("SELECT l.departure_id, l.vehicle_id, l.origin_hub_id AS origin, l.destination_hub_id AS destination, "
         "l.departure_datetime, l.maximum_weight_kg, l.booked_weight_kg "
         "FROM v_departure_load l JOIN vehicle v ON v.vehicle_id = l.vehicle_id "
         "WHERE v.carrier_id = %s ORDER BY l.departure_id", (acct[0],))


def _vehicle_weight_limit(vid):
    """Application-level rule: a departure's max weight cannot exceed what the vehicle can carry."""
    _, rows = db.query(
        "SELECT COALESCE(b.gross_weight_rating_kg, r.payload_limit_kg) FROM vehicle v "
        "LEFT JOIN box_truck b ON b.vehicle_id = v.vehicle_id "
        "LEFT JOIN refrigerated_van r ON r.vehicle_id = v.vehicle_id WHERE v.vehicle_id = %s", (vid,))
    return rows[0][0] if rows and rows[0][0] is not None else None   # rail cars: no limit stored


def create_departure(acct):
    list_vehicles(acct)
    vid = ask_int("Vehicle id")
    if _my_vehicle_type(acct, vid) is None:
        print("  That is not one of your vehicles.")
        return
    origin = ask_hub("Origin hub code")
    dest = ask_hub("Destination hub code")
    if origin == dest:
        print("  Origin and destination must differ.")
        return
    when = ask_datetime("Departure date/time (YYYY-MM-DD HH:MM)")
    max_w = ask_decimal("Maximum total weight (kg)", positive=True)
    limit = _vehicle_weight_limit(vid)
    if limit is not None and max_w > limit:
        print(f"  Rejected: this vehicle can carry at most {limit} kg.")
        return
    new_id = db.execute(
        "INSERT INTO departure (vehicle_id, origin_hub_id, destination_hub_id, departure_datetime, "
        "maximum_weight_kg) VALUES (%s, %s, %s, %s, %s)", (vid, origin, dest, when, max_w))
    print(f"  Departure {new_id} scheduled.")


def update_departure(acct):
    list_departures(acct)
    did = ask_int("Departure id to update")
    _, rows = db.query(
        "SELECT l.vehicle_id, l.departure_datetime, l.maximum_weight_kg, l.booked_weight_kg "
        "FROM v_departure_load l JOIN vehicle v ON v.vehicle_id = l.vehicle_id "
        "WHERE l.departure_id = %s AND v.carrier_id = %s", (did, acct[0]))
    if not rows:
        print("  That is not one of your departures.")
        return
    vid, when_old, max_old, booked = rows[0]
    print("  Leave a field blank to keep its current value.")
    when = ask_datetime("New departure date/time (YYYY-MM-DD HH:MM)", blank_ok=True) or when_old
    max_w = ask_decimal("New maximum weight (kg)", positive=True, blank_ok=True) or max_old
    if max_w < booked:
        print(f"  Rejected: {booked} kg are already booked on this departure.")
        return
    limit = _vehicle_weight_limit(vid)
    if limit is not None and max_w > limit:
        print(f"  Rejected: this vehicle can carry at most {limit} kg.")
        return
    db.execute("UPDATE departure SET departure_datetime = %s, maximum_weight_kg = %s "
               "WHERE departure_id = %s", (when, max_w, did))
    print(f"  Departure {did} updated.")


def post_scan(acct):
    print("\n  Shipments booked on your departures:")
    rows = show("SELECT s.shipment_id, s.origin_hub_id AS origin, s.destination_hub_id AS destination, "
                "COALESCE(s.current_status, 'NO SCANS YET') AS status, b.departure_id "
                "FROM booking b JOIN shipment s ON s.shipment_id = b.shipment_id "
                "JOIN departure d ON d.departure_id = b.departure_id "
                "JOIN vehicle v ON v.vehicle_id = d.vehicle_id "
                "WHERE v.carrier_id = %s ORDER BY s.shipment_id", (acct[0],))
    if not rows:
        return
    sid = ask_int("Shipment id")
    if sid not in [r[0] for r in rows]:
        print("  You can only post scans for shipments on your own departures.")
        return
    hub = ask_hub("Hub where scanned")
    status = ask_choice("New status", STATUSES)
    when = ask_datetime("Scan time (YYYY-MM-DD HH:MM)", default_now=True)
    # Next sequence number is computed inside the INSERT; the triggers enforce chronology
    # and update the shipment's status / on-time flag.
    db.execute("INSERT INTO scan_event (shipment_id, scan_sequence_no, scan_timestamp, hub_id, status) "
               "SELECT %s, COALESCE(MAX(scan_sequence_no), 0) + 1, %s, %s, %s "
               "FROM scan_event WHERE shipment_id = %s", (sid, when, hub, status, sid))
    _, r = db.query("SELECT current_status, COALESCE(delivery_outcome, '-') FROM shipment "
                    "WHERE shipment_id = %s", (sid,))
    print(f"  Scan posted. Shipment {sid} is now {r[0][0]} (outcome: {r[0][1]}).")


def reports(acct):
    print("\n  Weight utilization per departure:")
    show("SELECT l.departure_id, l.origin_hub_id AS origin, l.destination_hub_id AS destination, "
         "l.departure_datetime, l.booked_weight_kg AS booked_kg, l.maximum_weight_kg AS max_kg, "
         "l.utilization_pct AS utilization_pct "
         "FROM v_departure_load l JOIN vehicle v ON v.vehicle_id = l.vehicle_id "
         "WHERE v.carrier_id = %s ORDER BY l.departure_id", (acct[0],))
    print("\n  Your on-time delivery rate (delivered shipments only):")
    show("SELECT COUNT(*) AS delivered, "
         "COALESCE(SUM(s.delivery_outcome = 'ON_TIME'), 0) AS on_time, "
         "COALESCE(SUM(s.delivery_outcome = 'LATE'), 0) AS late, "
         "ROUND(100 * SUM(s.delivery_outcome = 'ON_TIME') / NULLIF(COUNT(*), 0), 1) AS on_time_pct "
         "FROM shipment s JOIN booking b ON b.shipment_id = s.shipment_id "
         "JOIN departure d ON d.departure_id = b.departure_id "
         "JOIN vehicle v ON v.vehicle_id = d.vehicle_id "
         "WHERE v.carrier_id = %s AND s.delivery_outcome IS NOT NULL", (acct[0],))
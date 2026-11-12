# shipper.py - Shipper menu. Ownership rule (a shipper only touches its own shipments)
# is enforced here by always filtering on shipper_id = the logged-in account.
from . import db
from .common import (ask, ask_date, ask_decimal, ask_hub, ask_int, run_menu,
                    show, show_tracking)


def menu(acct):
    run_menu(f"Shipper: {acct[1]}", [
        ("Create/Update Shipment", lambda: create_or_update(acct)),
        ("Book Shipment onto Departure", lambda: book(acct)),
        ("Track Shipment", lambda: track(acct)),
        ("Reports: On-time vs. late | In transit", lambda: reports(acct)),
        ("List my shipments", lambda: list_mine(acct)),
    ], back_label="Log out")



def list_mine(acct):
    show("SELECT s.shipment_id, s.origin_hub_id AS origin, s.destination_hub_id AS destination, "
         "s.weight_kg, s.promised_delivery_date AS promised, "
         "COALESCE(s.current_status, '-') AS status, COALESCE(s.delivery_outcome, '-') AS outcome, "
         "b.departure_id AS booked_on "
         "FROM shipment s LEFT JOIN booking b ON b.shipment_id = s.shipment_id "
         "WHERE s.shipper_id = %s ORDER BY s.shipment_id", (acct[0],))


def _my_shipment(acct, shipment_id):
    _, rows = db.query("SELECT shipment_id, origin_hub_id, destination_hub_id, weight_kg, "
                       "promised_delivery_date FROM shipment "
                       "WHERE shipment_id = %s AND shipper_id = %s", (shipment_id, acct[0]))
    return rows[0] if rows else None


def create_or_update(acct):
    run_menu("Shipments: Create/Update", [
        ("Create a shipment", lambda: create(acct)),
        ("Update a shipment", lambda: update(acct)),
    ])


def create(acct):
    origin = ask_hub("Origin hub code")
    dest = ask_hub("Destination hub code")
    if origin == dest:
        print("  Origin and destination must differ.")
        return
    weight = ask_decimal("Weight (kg)", positive=True)
    promised = ask_date("Promised delivery date (YYYY-MM-DD)")
    new_id = db.execute(
        "INSERT INTO shipment (shipper_id, origin_hub_id, destination_hub_id, weight_kg, "
        "promised_delivery_date) VALUES (%s, %s, %s, %s, %s)",
        (acct[0], origin, dest, weight, promised))
    print(f"  Shipment {new_id} created ({origin} -> {dest}, {weight} kg, promised {promised}).")


def update(acct):
    list_mine(acct)
    sid = ask_int("Shipment id to update")
    row = _my_shipment(acct, sid)
    if row is None:
        print("  That is not one of your shipments.")
        return
    # Application-level rule: changing weight/lane after booking could overbook a departure.
    if db.query("SELECT 1 FROM booking WHERE shipment_id = %s", (sid,))[1]:
        print("  Only unbooked shipments can be updated.")
        return
    print("  Leave a field blank to keep its current value.")
    origin = ask_hub("New origin hub", blank_ok=True) or row[1]
    dest = ask_hub("New destination hub", blank_ok=True) or row[2]
    weight = ask_decimal("New weight (kg)", positive=True, blank_ok=True) or row[3]
    promised = ask_date("New promised date (YYYY-MM-DD)", blank_ok=True) or row[4]
    if origin == dest:
        print("  Origin and destination must differ.")
        return
    db.execute("UPDATE shipment SET origin_hub_id=%s, destination_hub_id=%s, weight_kg=%s, "
               "promised_delivery_date=%s WHERE shipment_id=%s AND shipper_id=%s",
               (origin, dest, weight, promised, sid, acct[0]))
    print(f"  Shipment {sid} updated.")


def book(acct):
    print("\n  Your unbooked shipments:")
    rows = show("SELECT s.shipment_id, s.origin_hub_id AS origin, s.destination_hub_id AS destination, "
                "s.weight_kg, s.promised_delivery_date AS promised FROM shipment s "
                "WHERE s.shipper_id = %s AND NOT EXISTS "
                "(SELECT 1 FROM booking b WHERE b.shipment_id = s.shipment_id) "
                "ORDER BY s.shipment_id", (acct[0],))
    if not rows:
        return
    sid = ask_int("Shipment id to book")
    mine = [r for r in rows if r[0] == sid]
    if not mine:
        print("  Pick one of the shipments listed above.")
        return
    _, origin, dest, weight, _ = mine[0]
    print(f"\n  Departures on lane {origin} -> {dest} ('fits' = enough room for {weight} kg):")
    deps = show("SELECT l.departure_id, l.departure_datetime, l.booked_weight_kg, l.maximum_weight_kg, "
                "l.remaining_kg, IF(l.remaining_kg >= %s, 'yes', 'no') AS fits "
                "FROM v_departure_load l WHERE l.origin_hub_id = %s AND l.destination_hub_id = %s "
                "ORDER BY l.departure_datetime", (weight, origin, dest))
    if not deps:
        return
    did = ask_int("Departure id to book onto")
    # The stored procedure does the capacity check atomically and rejects bad bookings.
    results = db.call_proc("book_shipment", (sid, did))
    print(f"\n  Booked shipment {sid} onto departure {did}.")
    if results and results[0][1]:
        row = results[0][1][0]          # (shipment_id, departure_id, booked_weight_kg, maximum_weight_kg, result)
        print(f"  Departure load is now {row[2]} of {row[3]} kg.")


def track(acct):
    list_mine(acct)
    sid = ask_int("Shipment id to track")
    show_tracking(sid, shipper_id=acct[0])


def reports(acct):
    print("\n  On-time vs. late (delivered shipments only):")
    show("SELECT COUNT(*) AS delivered, "
         "COALESCE(SUM(delivery_outcome = 'ON_TIME'), 0) AS on_time, "
         "COALESCE(SUM(delivery_outcome = 'LATE'), 0) AS late, "
         "ROUND(100 * SUM(delivery_outcome = 'ON_TIME') / NULLIF(COUNT(*), 0), 1) AS on_time_pct "
         "FROM shipment WHERE shipper_id = %s AND delivery_outcome IS NOT NULL", (acct[0],))
    print("\n  Shipments currently in transit (scanned, not yet delivered):")
    show("SELECT shipment_id, origin_hub_id AS origin, destination_hub_id AS destination, "
         "current_status, promised_delivery_date AS promised FROM shipment "
         "WHERE shipper_id = %s AND current_status IS NOT NULL AND current_status <> 'DELIVERED' "
         "ORDER BY shipment_id", (acct[0],))
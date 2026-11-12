# viewer.py - Viewer menu: read-only. Only SELECT statements are used here.

from .common import ask_int, run_menu, show, show_tracking


def menu(acct):
    run_menu(f"Viewer: {acct[1]}", [
        ("Track Shipment", track),
        ("Published Performance Reports", reports),
    ], back_label="Log out")


def track():
    show_tracking(ask_int("Shipment id"))


def reports():
    print("\n  On-time rate by lane (delivered shipments only):")
    show("SELECT origin_hub_id AS origin, destination_hub_id AS destination, COUNT(*) AS delivered, "
         "SUM(delivery_outcome = 'ON_TIME') AS on_time, SUM(delivery_outcome = 'LATE') AS late, "
         "ROUND(100 * SUM(delivery_outcome = 'ON_TIME') / COUNT(*), 1) AS on_time_pct "
         "FROM shipment WHERE delivery_outcome IS NOT NULL "
         "GROUP BY origin_hub_id, destination_hub_id ORDER BY origin_hub_id, destination_hub_id")
    print("\n  On-time rate by carrier (delivered shipments only):")
    show("SELECT c.account_id AS carrier_id, c.carrier_name, COUNT(*) AS delivered, "
         "SUM(s.delivery_outcome = 'ON_TIME') AS on_time, SUM(s.delivery_outcome = 'LATE') AS late, "
         "ROUND(100 * SUM(s.delivery_outcome = 'ON_TIME') / COUNT(*), 1) AS on_time_pct "
         "FROM shipment s JOIN booking b ON b.shipment_id = s.shipment_id "
         "JOIN departure d ON d.departure_id = b.departure_id "
         "JOIN vehicle v ON v.vehicle_id = d.vehicle_id "
         "JOIN carrier c ON c.account_id = v.carrier_id "
         "WHERE s.delivery_outcome IS NOT NULL "
         "GROUP BY c.account_id, c.carrier_name ORDER BY c.account_id")
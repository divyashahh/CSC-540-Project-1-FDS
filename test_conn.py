# check if server is reachable and data loads

import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

# Connect and show who/where we are
try:
    conn = mysql.connector.connect(**DB_CONFIG, connection_timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT VERSION(), DATABASE(), CURRENT_USER()")
    version, database, user = cur.fetchone()
    print("Connected!")
    print("  Server version:", version)
    print("  Database      :", database)
    print("  Logged in as  :", user)
except Error as e:
    print("Connection FAILED:", e)
    print("Check: VPN/campus network, MySQL password, database name in config.py")
    raise SystemExit(1)

# Row counts after running sample_data.sql
expected = {
    "hub": 11, "user_account": 8, "carrier": 3, "shipper": 4, "viewer": 1,
    "vehicle": 7, "box_truck": 4, "refrigerated_van": 2, "rail_car": 1,
    "departure": 10, "shipment": 23, "booking": 22, "scan_event": 69,
}
for table, want in expected.items():
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        got = cur.fetchone()[0]
        flag = "OK " if got == want else "BAD"
        print(f"[{flag}] {table:18} got {got:3}  expected {want}")
    except Error as e:
        print(f"[ERR] {table:18} {e}")

# Did the triggers set the on-time / late outcome?
try:
    cur.execute("SELECT shipment_id, current_status, delivery_outcome "
                "FROM shipment ORDER BY shipment_id")
    for r in cur.fetchall():
        print(r)
except Error as e:
    print("Query failed:", e)

cur.close()
conn.close()
print("Connection closed.")
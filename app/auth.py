# auth.py - application-level login (role + username + password).

import getpass

from . import db

ROLES = ("Shipper", "Carrier", "Viewer")


def login(role):
    """Ask for credentials (3 tries). Returns (account_id, display_name) or None.
    The password is compared against SHA2-256 inside the database."""
    for _ in range(3):
        username = input(f"{role} username: ").strip()
        password = getpass.getpass("Password: ")
        _, rows = db.query(
            "SELECT a.account_id, COALESCE(c.carrier_name, s.shipper_name, a.username) "
            "FROM user_account a "
            "LEFT JOIN carrier c ON c.account_id = a.account_id "
            "LEFT JOIN shipper s ON s.account_id = a.account_id "
            "WHERE a.username = %s AND a.password_hash = SHA2(%s, 256) AND a.role = %s",
            (username, password, role))
        if rows:
            print(f"\nWelcome, {rows[0][1]} ({role}).")
            return rows[0]
        print("  Invalid username/password for this role.")
    return None
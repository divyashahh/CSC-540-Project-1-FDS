# main.py - entry point. Run from the project folder:  python main.py

from mysql.connector import Error

from app import auth, carrier, db, shipper, view_queries, viewer
from app.common import run_menu


def role_entry(role, menu_fn):
    def go():
        acct = auth.login(role)
        if acct:
            menu_fn(acct)
        else:
            print("  Too many failed attempts.")
    return go


def main():
    try:
        db.get_conn()
    except Error as e:
        print(f"Cannot connect to the database: {e}")
        print("Check config.py (host, user, password, database) and that you are on campus/VPN.")
        return
    try:
        run_menu("Freight Tracking and Delivery Management", [
            ("Shipper", role_entry("Shipper", shipper.menu)),
            ("Carrier", role_entry("Carrier", carrier.menu)),
            ("Viewer", role_entry("Viewer", viewer.menu)),
            ("View Queries", view_queries.menu),
        ], back_label="Exit")
    except (EOFError, KeyboardInterrupt):
        pass
    print("\nGoodbye.")


if __name__ == "__main__":
    main()
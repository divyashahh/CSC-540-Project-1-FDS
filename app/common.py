# common.py - input helpers, table printing, menu loop, shipment tracking display.

from datetime import datetime
from decimal import Decimal, InvalidOperation

from mysql.connector import Error

from . import db


def ask(prompt, default=""):
    suffix = f" [{default}]" if default != "" else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val if val else default


def ask_int(prompt, blank_ok=False):
    while True:
        val = ask(prompt)
        if val == "" and blank_ok:
            return None
        if val.lstrip("-").isdigit():
            return int(val)
        print("  Please enter a whole number.")


def ask_decimal(prompt, positive=False, blank_ok=False):
    while True:
        val = ask(prompt)
        if val == "" and blank_ok:
            return None
        try:
            num = Decimal(val)
            if positive and num <= 0:
                print("  Must be greater than 0.")
                continue
            return num
        except InvalidOperation:
            print("  Please enter a number.")


def ask_date(prompt, blank_ok=False):
    while True:
        val = ask(prompt)
        if val == "" and blank_ok:
            return None
        try:
            return datetime.strptime(val, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            print("  Use the format YYYY-MM-DD.")


def ask_datetime(prompt, default_now=False, blank_ok=False):
    default = datetime.now().strftime("%Y-%m-%d %H:%M") if default_now else ""
    while True:
        val = ask(prompt, default)
        if val == "" and blank_ok:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(val, fmt).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        print("  Use the format YYYY-MM-DD HH:MM.")


def ask_hub(prompt, blank_ok=False):
    _, rows = db.query("SELECT hub_id FROM hub ORDER BY hub_id")
    codes = [r[0] for r in rows]
    print("  Hubs: " + ", ".join(codes))
    while True:
        val = ask(prompt).upper()
        if val == "" and blank_ok:
            return None
        if val in codes:
            return val
        print("  Unknown hub code.")


def ask_choice(prompt, options):
    """options: list of labels. Returns the chosen label."""
    for i, label in enumerate(options, 1):
        print(f"  {i}) {label}")
    while True:
        val = ask(prompt)
        if val.isdigit() and 1 <= int(val) <= len(options):
            return options[int(val) - 1]
        print("  Invalid choice.")


def print_table(cols, rows):
    if not rows:
        print("  (no rows)")
        return
    text = [["-" if v is None else str(v) for v in row] for row in rows]
    widths = [max(len(str(c)), *(len(r[i]) for r in text)) for i, c in enumerate(cols)]
    line = "  " + "  ".join(str(c).ljust(w) for c, w in zip(cols, widths))
    print(line)
    print("  " + "  ".join("-" * w for w in widths))
    for r in text:
        print("  " + "  ".join(v.ljust(w) for v, w in zip(r, widths)))


def show(sql, params=None):
    cols, rows = db.query(sql, params)
    print_table(cols, rows)
    return rows


def run_menu(title, options, back_label="Back"):
    """options: list of (label, function). Database errors (trigger/procedure messages
    included) are printed instead of crashing the program."""
    while True:
        print(f"\n=== {title} ===")
        for i, (label, _) in enumerate(options, 1):
            print(f"  {i}) {label}")
        print(f"  0) {back_label}")
        choice = input("Select: ").strip()
        if choice == "0":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            try:
                options[int(choice) - 1][1]()
            except Error as e:
                print(f"\n  ! {e.msg}")
        else:
            print("  Invalid choice.")


def show_tracking(shipment_id, shipper_id=None):
    """Movement history + current status. Pass shipper_id to restrict to one shipper's shipments."""
    sql = ("SELECT s.shipment_id, sh.shipper_name, s.origin_hub_id, s.destination_hub_id, "
           "s.weight_kg, s.promised_delivery_date, "
           "COALESCE(s.current_status, 'NO SCANS YET') AS current_status, "
           "COALESCE(s.delivery_outcome, '-') AS delivery_outcome "
           "FROM shipment s JOIN shipper sh ON sh.account_id = s.shipper_id "
           "WHERE s.shipment_id = %s")
    params = [shipment_id]
    if shipper_id is not None:
        sql += " AND s.shipper_id = %s"
        params.append(shipper_id)
    cols, rows = db.query(sql, params)
    if not rows:
        print("  No such shipment" + (" for your account." if shipper_id is not None else "."))
        return
    print()
    for c, v in zip(cols, rows[0]):
        print(f"  {c:<26}{v}")
    print("\n  Movement history:")
    show("SELECT scan_sequence_no AS seq, scan_timestamp, hub_id, status "
         "FROM scan_event WHERE shipment_id = %s ORDER BY scan_sequence_no", (shipment_id,))
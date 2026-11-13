import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from app import db


# =========================================================
# GENERAL HELPERS
# =========================================================

def clear_root():
    for widget in root.winfo_children():
        widget.destroy()


def create_title(text, subtitle=None):
    ttk.Label(
        root,
        text=text,
        font=("Arial", 18, "bold")
    ).pack(pady=(25, 8))

    if subtitle:
        ttk.Label(
            root,
            text=subtitle,
            font=("Arial", 11)
        ).pack(pady=(0, 15))


def create_tree(parent, columns, headings, widths=None):
    tree = ttk.Treeview(
        parent,
        columns=columns,
        show="headings"
    )

    for i, column in enumerate(columns):
        tree.heading(column, text=headings[i])
        tree.column(
            column,
            width=widths[i] if widths else 120,
            anchor="center"
        )

    scrollbar = ttk.Scrollbar(
        parent,
        orient="vertical",
        command=tree.yview
    )

    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(
        side="left",
        fill="both",
        expand=True
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    return tree


def show_rows(
    title,
    columns,
    headings,
    rows,
    widths=None,
    back_command=None
):
    clear_root()

    create_title(title)

    frame = ttk.Frame(root)
    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    tree = create_tree(
        frame,
        columns,
        headings,
        widths
    )

    for row in rows:
        tree.insert("", "end", values=row)

    ttk.Button(
        root,
        text="Back",
        command=back_command or show_home,
        width=25
    ).pack(pady=15)


def get_hubs():
    _, rows = db.query(
        "SELECT hub_id FROM hub ORDER BY hub_id"
    )
    return [row[0] for row in rows]


def valid_datetime(value):
    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d %H:%M"
        ).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError(
            "Use date/time format YYYY-MM-DD HH:MM."
        )


def valid_date(value):
    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(
            "Use date format YYYY-MM-DD."
        )


# =========================================================
# HOME SCREEN
# =========================================================

def show_home():
    clear_root()

    create_title(
        "Freight Tracking and Delivery Management",
        "Select a role"
    )

    ttk.Button(
        root,
        text="Shipper",
        command=lambda: show_login("Shipper"),
        width=30
    ).pack(pady=10)

    ttk.Button(
        root,
        text="Carrier",
        command=lambda: show_login("Carrier"),
        width=30
    ).pack(pady=10)

    ttk.Button(
        root,
        text="Viewer",
        command=lambda: show_login("Viewer"),
        width=30
    ).pack(pady=10)

    ttk.Button(
        root,
        text="View Queries",
        command=show_queries_menu,
        width=30
    ).pack(pady=10)

    ttk.Button(
        root,
        text="Exit",
        command=root.destroy,
        width=30
    ).pack(pady=25)


# =========================================================
# LOGIN
# =========================================================

def show_login(role):
    clear_root()

    create_title(f"{role} Login")

    form = ttk.Frame(root)
    form.pack(pady=10)

    ttk.Label(
        form,
        text="Username"
    ).grid(
        row=0,
        column=0,
        padx=10,
        pady=10
    )

    username_entry = ttk.Entry(
        form,
        width=30
    )
    username_entry.grid(
        row=0,
        column=1,
        padx=10,
        pady=10
    )

    ttk.Label(
        form,
        text="Password"
    ).grid(
        row=1,
        column=0,
        padx=10,
        pady=10
    )

    password_entry = ttk.Entry(
        form,
        width=30,
        show="*"
    )
    password_entry.grid(
        row=1,
        column=1,
        padx=10,
        pady=10
    )

    def attempt_login():
        username = username_entry.get().strip()
        password = password_entry.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing Information",
                "Enter both username and password."
            )
            return

        try:
            _, rows = db.query(
                """
                SELECT
                    a.account_id,
                    COALESCE(
                        c.carrier_name,
                        s.shipper_name,
                        a.username
                    )
                FROM user_account a
                LEFT JOIN carrier c
                    ON c.account_id = a.account_id
                LEFT JOIN shipper s
                    ON s.account_id = a.account_id
                WHERE a.username = %s
                  AND a.password_hash = SHA2(%s, 256)
                  AND a.role = %s
                """,
                (username, password, role)
            )

            if not rows:
                messagebox.showerror(
                    "Login Failed",
                    "Invalid username or password for this role."
                )
                return

            account_id, display_name = rows[0]

            if role == "Shipper":
                show_shipper_dashboard(
                    account_id,
                    display_name
                )

            elif role == "Carrier":
                show_carrier_dashboard(
                    account_id,
                    display_name
                )

            else:
                show_viewer_dashboard(
                    account_id,
                    display_name
                )

        except Exception as e:
            messagebox.showerror(
                "Database Error",
                str(e)
            )

    ttk.Button(
        root,
        text="Login",
        command=attempt_login,
        width=25
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=show_home,
        width=25
    ).pack()


# =========================================================
# SHIPPER DASHBOARD
# =========================================================

def show_shipper_dashboard(account_id, display_name):
    clear_root()

    create_title(
        f"Welcome, {display_name}",
        "Shipper Dashboard"
    )

    options = [
        (
            "List My Shipments",
            lambda: show_shipper_shipments(
                account_id,
                display_name
            )
        ),
        (
            "Create Shipment",
            lambda: show_create_shipment(
                account_id,
                display_name
            )
        ),
        (
            "Update Shipment",
            lambda: show_update_shipment(
                account_id,
                display_name
            )
        ),
        (
            "Book Shipment",
            lambda: show_book_shipment(
                account_id,
                display_name
            )
        ),
        (
            "Track Shipment",
            lambda: show_track_shipment(
                account_id,
                display_name
            )
        ),
        (
            "Reports",
            lambda: show_shipper_reports(
                account_id,
                display_name
            )
        )
    ]

    for label, command in options:
        ttk.Button(
            root,
            text=label,
            command=command,
            width=32
        ).pack(pady=7)

    ttk.Button(
        root,
        text="Logout",
        command=show_home,
        width=32
    ).pack(pady=20)


# =========================================================
# SHIPPER - LIST
# =========================================================

def show_shipper_shipments(account_id, display_name):
    try:
        _, rows = db.query(
            """
            SELECT
                s.shipment_id,
                s.origin_hub_id,
                s.destination_hub_id,
                s.weight_kg,
                s.promised_delivery_date,
                COALESCE(
                    s.current_status,
                    'NO SCANS'
                ),
                COALESCE(
                    s.delivery_outcome,
                    '-'
                ),
                COALESCE(
                    b.departure_id,
                    '-'
                )
            FROM shipment s
            LEFT JOIN booking b
                ON b.shipment_id = s.shipment_id
            WHERE s.shipper_id = %s
            ORDER BY s.shipment_id
            """,
            (account_id,)
        )

        show_rows(
            "My Shipments",
            (
                "id",
                "origin",
                "destination",
                "weight",
                "promised",
                "status",
                "outcome",
                "departure"
            ),
            (
                "ID",
                "Origin",
                "Destination",
                "Weight",
                "Promised",
                "Status",
                "Outcome",
                "Departure"
            ),
            rows,
            (50, 70, 90, 80, 100, 120, 90, 80),
            lambda: show_shipper_dashboard(
                account_id,
                display_name
            )
        )

    except Exception as e:
        messagebox.showerror(
            "Database Error",
            str(e)
        )


# =========================================================
# SHIPPER - CREATE
# =========================================================

def show_create_shipment(account_id, display_name):
    clear_root()

    create_title("Create Shipment")

    hubs = get_hubs()

    form = ttk.Frame(root)
    form.pack(pady=15)

    ttk.Label(
        form,
        text="Origin Hub"
    ).grid(
        row=0,
        column=0,
        padx=10,
        pady=10
    )

    origin_box = ttk.Combobox(
        form,
        values=hubs,
        state="readonly"
    )
    origin_box.grid(row=0, column=1)

    ttk.Label(
        form,
        text="Destination Hub"
    ).grid(
        row=1,
        column=0,
        padx=10,
        pady=10
    )

    destination_box = ttk.Combobox(
        form,
        values=hubs,
        state="readonly"
    )
    destination_box.grid(row=1, column=1)

    ttk.Label(
        form,
        text="Weight (kg)"
    ).grid(
        row=2,
        column=0,
        padx=10,
        pady=10
    )

    weight_entry = ttk.Entry(form)
    weight_entry.grid(row=2, column=1)

    ttk.Label(
        form,
        text="Promised Date"
    ).grid(
        row=3,
        column=0,
        padx=10,
        pady=10
    )

    date_entry = ttk.Entry(form)
    date_entry.grid(row=3, column=1)

    ttk.Label(
        form,
        text="YYYY-MM-DD"
    ).grid(row=4, column=1)

    def create():
        origin = origin_box.get()
        destination = destination_box.get()
        weight_text = weight_entry.get().strip()
        promised = date_entry.get().strip()

        if not all(
            (
                origin,
                destination,
                weight_text,
                promised
            )
        ):
            messagebox.showwarning(
                "Missing Information",
                "Fill out every field."
            )
            return

        if origin == destination:
            messagebox.showerror(
                "Invalid Shipment",
                "Origin and destination must differ."
            )
            return

        try:
            weight = float(weight_text)

            if weight <= 0:
                raise ValueError(
                    "Weight must be greater than 0."
                )

            promised = valid_date(promised)

            new_id = db.execute(
                """
                INSERT INTO shipment (
                    shipper_id,
                    origin_hub_id,
                    destination_hub_id,
                    weight_kg,
                    promised_delivery_date
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    account_id,
                    origin,
                    destination,
                    weight,
                    promised
                )
            )

            messagebox.showinfo(
                "Shipment Created",
                f"Shipment {new_id} was created."
            )

            show_shipper_shipments(
                account_id,
                display_name
            )

        except Exception as e:
            messagebox.showerror(
                "Create Shipment Failed",
                str(e)
            )

    ttk.Button(
        root,
        text="Create Shipment",
        command=create,
        width=25
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_shipper_dashboard(
            account_id,
            display_name
        ),
        width=25
    ).pack()


# =========================================================
# SHIPPER - UPDATE
# =========================================================

def show_update_shipment(account_id, display_name):
    clear_root()

    create_title("Update Shipment")

    _, rows = db.query(
        """
        SELECT shipment_id
        FROM shipment s
        WHERE shipper_id = %s
          AND NOT EXISTS (
              SELECT 1
              FROM booking b
              WHERE b.shipment_id = s.shipment_id
          )
        ORDER BY shipment_id
        """,
        (account_id,)
    )

    shipment_ids = [
        str(row[0])
        for row in rows
    ]

    if not shipment_ids:
        messagebox.showinfo(
            "No Shipments",
            "No unbooked shipments are available."
        )
        show_shipper_dashboard(
            account_id,
            display_name
        )
        return

    hubs = get_hubs()

    form = ttk.Frame(root)
    form.pack(pady=15)

    labels = [
        "Shipment ID",
        "Origin Hub",
        "Destination Hub",
        "Weight (kg)",
        "Promised Date"
    ]

    for i, label in enumerate(labels):
        ttk.Label(
            form,
            text=label
        ).grid(
            row=i,
            column=0,
            padx=10,
            pady=8
        )

    shipment_box = ttk.Combobox(
        form,
        values=shipment_ids,
        state="readonly"
    )
    shipment_box.grid(row=0, column=1)

    origin_box = ttk.Combobox(
        form,
        values=hubs,
        state="readonly"
    )
    origin_box.grid(row=1, column=1)

    destination_box = ttk.Combobox(
        form,
        values=hubs,
        state="readonly"
    )
    destination_box.grid(row=2, column=1)

    weight_entry = ttk.Entry(form)
    weight_entry.grid(row=3, column=1)

    date_entry = ttk.Entry(form)
    date_entry.grid(row=4, column=1)

    def load(event=None):
        sid = shipment_box.get()

        if not sid:
            return

        _, data = db.query(
            """
            SELECT
                origin_hub_id,
                destination_hub_id,
                weight_kg,
                promised_delivery_date
            FROM shipment
            WHERE shipment_id = %s
              AND shipper_id = %s
            """,
            (sid, account_id)
        )

        if not data:
            return

        row = data[0]

        origin_box.set(row[0])
        destination_box.set(row[1])

        weight_entry.delete(0, tk.END)
        weight_entry.insert(0, row[2])

        date_entry.delete(0, tk.END)
        date_entry.insert(0, row[3])

    shipment_box.bind(
        "<<ComboboxSelected>>",
        load
    )

    def update():
        sid = shipment_box.get()
        origin = origin_box.get()
        destination = destination_box.get()

        if not sid:
            messagebox.showwarning(
                "Select Shipment",
                "Choose a shipment first."
            )
            return

        if origin == destination:
            messagebox.showerror(
                "Invalid Route",
                "Origin and destination must differ."
            )
            return

        try:
            weight = float(
                weight_entry.get().strip()
            )

            if weight <= 0:
                raise ValueError(
                    "Weight must be greater than 0."
                )

            promised = valid_date(
                date_entry.get().strip()
            )

            db.execute(
                """
                UPDATE shipment
                SET origin_hub_id = %s,
                    destination_hub_id = %s,
                    weight_kg = %s,
                    promised_delivery_date = %s
                WHERE shipment_id = %s
                  AND shipper_id = %s
                """,
                (
                    origin,
                    destination,
                    weight,
                    promised,
                    sid,
                    account_id
                )
            )

            messagebox.showinfo(
                "Updated",
                f"Shipment {sid} was updated."
            )

            show_shipper_shipments(
                account_id,
                display_name
            )

        except Exception as e:
            messagebox.showerror(
                "Update Failed",
                str(e)
            )

    ttk.Button(
        root,
        text="Update Shipment",
        command=update,
        width=25
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_shipper_dashboard(
            account_id,
            display_name
        ),
        width=25
    ).pack()


# =========================================================
# SHIPPER - BOOK
# =========================================================

def show_book_shipment(account_id, display_name):
    clear_root()

    create_title("Book Shipment")

    _, rows = db.query(
        """
        SELECT shipment_id
        FROM shipment s
        WHERE shipper_id = %s
          AND NOT EXISTS (
              SELECT 1
              FROM booking b
              WHERE b.shipment_id = s.shipment_id
          )
        ORDER BY shipment_id
        """,
        (account_id,)
    )

    shipment_ids = [
        str(row[0])
        for row in rows
    ]

    if not shipment_ids:
        messagebox.showinfo(
            "No Shipments",
            "You have no unbooked shipments."
        )
        show_shipper_dashboard(
            account_id,
            display_name
        )
        return

    ttk.Label(
        root,
        text="Select Shipment"
    ).pack(pady=5)

    shipment_box = ttk.Combobox(
        root,
        values=shipment_ids,
        state="readonly",
        width=25
    )
    shipment_box.pack()

    status_label = ttk.Label(
        root,
        text=""
    )
    status_label.pack(pady=5)

    frame = ttk.Frame(root)
    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=15
    )

    tree = create_tree(
        frame,
        (
            "id",
            "origin",
            "dest",
            "time",
            "remaining"
        ),
        (
            "Departure",
            "Origin",
            "Destination",
            "Date/Time",
            "Remaining kg"
        ),
        (80, 70, 90, 150, 100)
    )

    def load_departures(event=None):
        for item in tree.get_children():
            tree.delete(item)

        sid = shipment_box.get()

        if not sid:
            return

        _, shipment = db.query(
            """
            SELECT
                origin_hub_id,
                destination_hub_id,
                weight_kg
            FROM shipment
            WHERE shipment_id = %s
              AND shipper_id = %s
            """,
            (sid, account_id)
        )

        if not shipment:
            return

        origin, dest, weight = shipment[0]

        _, departures = db.query(
            """
            SELECT
                departure_id,
                origin_hub_id,
                destination_hub_id,
                departure_datetime,
                remaining_kg
            FROM v_departure_load
            WHERE origin_hub_id = %s
              AND destination_hub_id = %s
              AND remaining_kg >= %s
            ORDER BY departure_datetime
            """,
            (origin, dest, weight)
        )

        for row in departures:
            tree.insert(
                "",
                "end",
                values=row
            )

        if departures:
            status_label.config(
                text=(
                    f"Eligible departures for "
                    f"{origin} → {dest}, {weight} kg"
                )
            )
        else:
            status_label.config(
                text=(
                    "No eligible departures currently "
                    "have the correct lane and capacity."
                )
            )

    shipment_box.bind(
        "<<ComboboxSelected>>",
        load_departures
    )

    def book():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Departure",
                "Choose a departure from the table."
            )
            return

        sid = int(shipment_box.get())

        departure_id = int(
            tree.item(
                selected[0]
            )["values"][0]
        )

        try:
            db.call_proc(
                "book_shipment",
                (sid, departure_id)
            )

            messagebox.showinfo(
                "Booked",
                (
                    f"Shipment {sid} was booked "
                    f"onto departure {departure_id}."
                )
            )

            show_shipper_shipments(
                account_id,
                display_name
            )

        except Exception as e:
            messagebox.showerror(
                "Booking Failed",
                str(e)
            )

    ttk.Button(
        root,
        text="Book Selected Departure",
        command=book,
        width=28
    ).pack(pady=10)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_shipper_dashboard(
            account_id,
            display_name
        ),
        width=25
    ).pack(pady=10)


# =========================================================
# SHIPPER - TRACK
# =========================================================

def show_track_shipment(account_id, display_name):
    clear_root()

    create_title("Track Shipment")

    _, rows = db.query(
        """
        SELECT shipment_id
        FROM shipment
        WHERE shipper_id = %s
        ORDER BY shipment_id
        """,
        (account_id,)
    )

    ids = [
        str(row[0])
        for row in rows
    ]

    shipment_box = ttk.Combobox(
        root,
        values=ids,
        state="readonly",
        width=25
    )
    shipment_box.pack(pady=10)

    info = ttk.Label(
        root,
        text="",
        justify="left"
    )
    info.pack(pady=10)

    frame = ttk.Frame(root)
    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    tree = create_tree(
        frame,
        ("seq", "time", "hub", "status"),
        ("Seq", "Timestamp", "Hub", "Status"),
        (50, 160, 80, 140)
    )

    def track():
        sid = shipment_box.get()

        if not sid:
            messagebox.showwarning(
                "Select Shipment",
                "Choose a shipment."
            )
            return

        _, shipment = db.query(
            """
            SELECT
                origin_hub_id,
                destination_hub_id,
                weight_kg,
                promised_delivery_date,
                COALESCE(
                    current_status,
                    'NO SCANS'
                ),
                COALESCE(
                    delivery_outcome,
                    '-'
                )
            FROM shipment
            WHERE shipment_id = %s
              AND shipper_id = %s
            """,
            (sid, account_id)
        )

        if not shipment:
            return

        row = shipment[0]

        info.config(
            text=(
                f"Route: {row[0]} → {row[1]}\n"
                f"Weight: {row[2]} kg\n"
                f"Promised: {row[3]}\n"
                f"Current Status: {row[4]}\n"
                f"Outcome: {row[5]}"
            )
        )

        for item in tree.get_children():
            tree.delete(item)

        _, scans = db.query(
            """
            SELECT
                scan_sequence_no,
                scan_timestamp,
                hub_id,
                status
            FROM scan_event
            WHERE shipment_id = %s
            ORDER BY scan_sequence_no
            """,
            (sid,)
        )

        for scan in scans:
            tree.insert(
                "",
                "end",
                values=scan
            )

    ttk.Button(
        root,
        text="Track",
        command=track,
        width=25
    ).pack(pady=10)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_shipper_dashboard(
            account_id,
            display_name
        ),
        width=25
    ).pack(pady=10)


# =========================================================
# SHIPPER - REPORTS
# =========================================================

def show_shipper_reports(account_id, display_name):
    clear_root()

    create_title("Shipper Reports")

    _, summary = db.query(
        """
        SELECT
            COUNT(*) AS delivered,
            COALESCE(
                SUM(delivery_outcome = 'ON_TIME'),
                0
            ),
            COALESCE(
                SUM(delivery_outcome = 'LATE'),
                0
            ),
            ROUND(
                100 *
                SUM(delivery_outcome = 'ON_TIME') /
                NULLIF(COUNT(*), 0),
                1
            )
        FROM shipment
        WHERE shipper_id = %s
          AND delivery_outcome IS NOT NULL
        """,
        (account_id,)
    )

    delivered, on_time, late, pct = summary[0]

    ttk.Label(
        root,
        text=(
            f"Delivered: {delivered}     "
            f"On Time: {on_time}     "
            f"Late: {late}     "
            f"On-Time Rate: {pct if pct is not None else '-'}%"
        ),
        font=("Arial", 12, "bold")
    ).pack(pady=15)

    ttk.Label(
        root,
        text="Shipments Currently In Transit",
        font=("Arial", 12)
    ).pack(pady=5)

    _, rows = db.query(
        """
        SELECT
            shipment_id,
            origin_hub_id,
            destination_hub_id,
            current_status,
            promised_delivery_date
        FROM shipment
        WHERE shipper_id = %s
          AND current_status IS NOT NULL
          AND current_status <> 'DELIVERED'
        ORDER BY shipment_id
        """,
        (account_id,)
    )

    frame = ttk.Frame(root)
    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    tree = create_tree(
        frame,
        (
            "id",
            "origin",
            "dest",
            "status",
            "promised"
        ),
        (
            "ID",
            "Origin",
            "Destination",
            "Status",
            "Promised"
        ),
        (70, 80, 100, 150, 110)
    )

    for row in rows:
        tree.insert(
            "",
            "end",
            values=row
        )

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_shipper_dashboard(
            account_id,
            display_name
        ),
        width=25
    ).pack(pady=15)


# =========================================================
# CARRIER DASHBOARD
# =========================================================

def show_carrier_dashboard(account_id, display_name):
    clear_root()

    create_title(
        f"Welcome, {display_name}",
        "Carrier Dashboard"
    )

    options = [
        (
            "List My Vehicles",
            lambda: show_carrier_vehicles(
                account_id,
                display_name
            )
        ),
        (
            "Create Vehicle",
            lambda: show_create_vehicle(
                account_id,
                display_name
            )
        ),
        (
            "Update Vehicle",
            lambda: show_update_vehicle(
                account_id,
                display_name
            )
        ),
        (
            "List Departures",
            lambda: show_carrier_departures(
                account_id,
                display_name
            )
        ),
        (
            "Create Departure",
            lambda: show_create_departure(
                account_id,
                display_name
            )
        ),
        (
            "Update Departure",
            lambda: show_update_departure(
                account_id,
                display_name
            )
        ),
        (
            "Post Scan Event",
            lambda: show_post_scan(
                account_id,
                display_name
            )
        ),
        (
            "Reports",
            lambda: show_carrier_reports(
                account_id,
                display_name
            )
        )
    ]

    for label, command in options:
        ttk.Button(
            root,
            text=label,
            command=command,
            width=30
        ).pack(pady=5)

    ttk.Button(
        root,
        text="Logout",
        command=show_home,
        width=30
    ).pack(pady=18)


# =========================================================
# CARRIER - LIST VEHICLES
# =========================================================

def show_carrier_vehicles(account_id, display_name):
    _, rows = db.query(
        """
        SELECT
            v.vehicle_id,
            v.vehicle_type,
            v.home_hub_id,
            CASE
                WHEN v.vehicle_type = 'BOX_TRUCK'
                    THEN CONCAT(
                        'Volume ',
                        b.cargo_volume_m3,
                        ' m3 | Rating ',
                        b.gross_weight_rating_kg,
                        ' kg'
                    )
                WHEN v.vehicle_type = 'REFRIGERATED_VAN'
                    THEN CONCAT(
                        r.min_temperature_c,
                        ' to ',
                        r.max_temperature_c,
                        ' C | Payload ',
                        r.payload_limit_kg,
                        ' kg'
                    )
                WHEN v.vehicle_type = 'RAIL_CAR'
                    THEN CONCAT(
                        rc.axle_count,
                        ' axles | Gauge ',
                        rc.track_gauge_mm,
                        ' mm'
                    )
            END AS details
        FROM vehicle v
        LEFT JOIN box_truck b
            ON b.vehicle_id = v.vehicle_id
        LEFT JOIN refrigerated_van r
            ON r.vehicle_id = v.vehicle_id
        LEFT JOIN rail_car rc
            ON rc.vehicle_id = v.vehicle_id
        WHERE v.carrier_id = %s
        ORDER BY v.vehicle_id
        """,
        (account_id,)
    )

    show_rows(
        "My Vehicles",
        (
            "id",
            "type",
            "hub",
            "details"
        ),
        (
            "Vehicle ID",
            "Type",
            "Home Hub",
            "Details"
        ),
        rows,
        (100, 170, 100, 350),
        lambda: show_carrier_dashboard(
            account_id,
            display_name
        )
    )


# =========================================================
# CARRIER - CREATE VEHICLE
# =========================================================

def show_create_vehicle(account_id, display_name):
    clear_root()

    create_title("Create Vehicle")

    hubs = get_hubs()

    main_form = ttk.Frame(root)
    main_form.pack(pady=10)

    ttk.Label(
        main_form,
        text="Vehicle Type"
    ).grid(
        row=0,
        column=0,
        padx=10,
        pady=10
    )

    type_box = ttk.Combobox(
        main_form,
        values=[
            "BOX_TRUCK",
            "REFRIGERATED_VAN",
            "RAIL_CAR"
        ],
        state="readonly",
        width=25
    )
    type_box.grid(
        row=0,
        column=1,
        padx=10,
        pady=10
    )

    ttk.Label(
        main_form,
        text="Home Hub"
    ).grid(
        row=1,
        column=0,
        padx=10,
        pady=10
    )

    hub_box = ttk.Combobox(
        main_form,
        values=hubs,
        state="readonly",
        width=25
    )
    hub_box.grid(
        row=1,
        column=1,
        padx=10,
        pady=10
    )

    subtype_frame = ttk.LabelFrame(
        root,
        text="Vehicle Details"
    )
    subtype_frame.pack(
        padx=20,
        pady=15
    )

    subtype_entries = {}

    def rebuild_fields(event=None):
        for widget in subtype_frame.winfo_children():
            widget.destroy()

        subtype_entries.clear()

        vtype = type_box.get()

        if vtype == "BOX_TRUCK":
            fields = [
                (
                    "cargo_volume_m3",
                    "Cargo Volume (m³)"
                ),
                (
                    "gross_weight_rating_kg",
                    "Gross Weight Rating (kg)"
                )
            ]

        elif vtype == "REFRIGERATED_VAN":
            fields = [
                (
                    "min_temperature_c",
                    "Minimum Temperature (°C)"
                ),
                (
                    "max_temperature_c",
                    "Maximum Temperature (°C)"
                ),
                (
                    "payload_limit_kg",
                    "Payload Limit (kg)"
                )
            ]

        elif vtype == "RAIL_CAR":
            fields = [
                (
                    "axle_count",
                    "Axle Count"
                ),
                (
                    "track_gauge_mm",
                    "Track Gauge (mm)"
                )
            ]

        else:
            return

        for row_num, (column, label) in enumerate(fields):
            ttk.Label(
                subtype_frame,
                text=label
            ).grid(
                row=row_num,
                column=0,
                padx=10,
                pady=8,
                sticky="e"
            )

            entry = ttk.Entry(
                subtype_frame,
                width=25
            )
            entry.grid(
                row=row_num,
                column=1,
                padx=10,
                pady=8
            )

            subtype_entries[column] = entry

    type_box.bind(
        "<<ComboboxSelected>>",
        rebuild_fields
    )

    def create():
        vtype = type_box.get()
        hub = hub_box.get()

        if not vtype or not hub:
            messagebox.showwarning(
                "Missing Information",
                "Select a vehicle type and home hub."
            )
            return

        try:
            values = {}

            for column, entry in subtype_entries.items():
                text = entry.get().strip()

                if not text:
                    raise ValueError(
                        "Fill out every vehicle detail."
                    )

                values[column] = float(text)

            if (
                vtype == "REFRIGERATED_VAN"
                and values["min_temperature_c"]
                > values["max_temperature_c"]
            ):
                raise ValueError(
                    "Minimum temperature cannot exceed maximum temperature."
                )

            if vtype == "RAIL_CAR":
                axle_count = values["axle_count"]

                if not axle_count.is_integer():
                    raise ValueError(
                        "Axle count must be a whole number."
                    )

                values["axle_count"] = int(axle_count)

            for value in values.values():
                if (
                    value <= 0
                    and vtype != "REFRIGERATED_VAN"
                ):
                    raise ValueError(
                        "Vehicle values must be greater than 0."
                    )

            with db.transaction() as cur:
                cur.execute(
                    """
                    INSERT INTO vehicle (
                        carrier_id,
                        home_hub_id,
                        vehicle_type
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (
                        account_id,
                        hub,
                        vtype
                    )
                )

                vehicle_id = cur.lastrowid

                if vtype == "BOX_TRUCK":
                    cur.execute(
                        """
                        INSERT INTO box_truck (
                            vehicle_id,
                            cargo_volume_m3,
                            gross_weight_rating_kg
                        )
                        VALUES (%s, %s, %s)
                        """,
                        (
                            vehicle_id,
                            values["cargo_volume_m3"],
                            values[
                                "gross_weight_rating_kg"
                            ]
                        )
                    )

                elif vtype == "REFRIGERATED_VAN":
                    cur.execute(
                        """
                        INSERT INTO refrigerated_van (
                            vehicle_id,
                            min_temperature_c,
                            max_temperature_c,
                            payload_limit_kg
                        )
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            vehicle_id,
                            values[
                                "min_temperature_c"
                            ],
                            values[
                                "max_temperature_c"
                            ],
                            values[
                                "payload_limit_kg"
                            ]
                        )
                    )

                else:
                    cur.execute(
                        """
                        INSERT INTO rail_car (
                            vehicle_id,
                            axle_count,
                            track_gauge_mm
                        )
                        VALUES (%s, %s, %s)
                        """,
                        (
                            vehicle_id,
                            values["axle_count"],
                            values["track_gauge_mm"]
                        )
                    )

            messagebox.showinfo(
                "Vehicle Created",
                f"Vehicle {vehicle_id} was created."
            )

            show_carrier_vehicles(
                account_id,
                display_name
            )

        except Exception as e:
            messagebox.showerror(
                "Create Vehicle Failed",
                str(e)
            )

    ttk.Button(
        root,
        text="Create Vehicle",
        command=create,
        width=25
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_carrier_dashboard(
            account_id,
            display_name
        ),
        width=25
    ).pack()


# =========================================================
# CARRIER - UPDATE VEHICLE
# =========================================================

def show_update_vehicle(account_id, display_name):
    clear_root()

    create_title("Update Vehicle")

    _, rows = db.query(
        """
        SELECT
            vehicle_id,
            vehicle_type
        FROM vehicle
        WHERE carrier_id = %s
        ORDER BY vehicle_id
        """,
        (account_id,)
    )

    if not rows:
        messagebox.showinfo(
            "No Vehicles",
            "This carrier has no vehicles."
        )
        show_carrier_dashboard(
            account_id,
            display_name
        )
        return

    vehicle_map = {
        str(vehicle_id): vehicle_type
        for vehicle_id, vehicle_type in rows
    }

    hubs = get_hubs()

    form = ttk.Frame(root)
    form.pack(pady=10)

    ttk.Label(
        form,
        text="Vehicle ID"
    ).grid(
        row=0,
        column=0,
        padx=10,
        pady=8
    )

    vehicle_box = ttk.Combobox(
        form,
        values=list(vehicle_map.keys()),
        state="readonly",
        width=25
    )
    vehicle_box.grid(
        row=0,
        column=1,
        padx=10,
        pady=8
    )

    ttk.Label(
        form,
        text="Home Hub"
    ).grid(
        row=1,
        column=0,
        padx=10,
        pady=8
    )

    hub_box = ttk.Combobox(
        form,
        values=hubs,
        state="readonly",
        width=25
    )
    hub_box.grid(
        row=1,
        column=1,
        padx=10,
        pady=8
    )

    details_frame = ttk.LabelFrame(
        root,
        text="Vehicle Details"
    )
    details_frame.pack(
        padx=20,
        pady=15
    )

    detail_entries = {}

    def load_vehicle(event=None):
        for widget in details_frame.winfo_children():
            widget.destroy()

        detail_entries.clear()

        vehicle_id = vehicle_box.get()

        if not vehicle_id:
            return

        vtype = vehicle_map[vehicle_id]

        _, base = db.query(
            """
            SELECT home_hub_id
            FROM vehicle
            WHERE vehicle_id = %s
              AND carrier_id = %s
            """,
            (
                vehicle_id,
                account_id
            )
        )

        hub_box.set(base[0][0])

        if vtype == "BOX_TRUCK":
            _, data = db.query(
                """
                SELECT
                    cargo_volume_m3,
                    gross_weight_rating_kg
                FROM box_truck
                WHERE vehicle_id = %s
                """,
                (vehicle_id,)
            )

            fields = [
                (
                    "cargo_volume_m3",
                    "Cargo Volume (m³)",
                    data[0][0]
                ),
                (
                    "gross_weight_rating_kg",
                    "Gross Weight Rating (kg)",
                    data[0][1]
                )
            ]

        elif vtype == "REFRIGERATED_VAN":
            _, data = db.query(
                """
                SELECT
                    min_temperature_c,
                    max_temperature_c,
                    payload_limit_kg
                FROM refrigerated_van
                WHERE vehicle_id = %s
                """,
                (vehicle_id,)
            )

            fields = [
                (
                    "min_temperature_c",
                    "Minimum Temperature (°C)",
                    data[0][0]
                ),
                (
                    "max_temperature_c",
                    "Maximum Temperature (°C)",
                    data[0][1]
                ),
                (
                    "payload_limit_kg",
                    "Payload Limit (kg)",
                    data[0][2]
                )
            ]

        else:
            _, data = db.query(
                """
                SELECT
                    axle_count,
                    track_gauge_mm
                FROM rail_car
                WHERE vehicle_id = %s
                """,
                (vehicle_id,)
            )

            fields = [
                (
                    "axle_count",
                    "Axle Count",
                    data[0][0]
                ),
                (
                    "track_gauge_mm",
                    "Track Gauge (mm)",
                    data[0][1]
                )
            ]

        ttk.Label(
            details_frame,
            text=f"Type: {vtype}",
            font=("Arial", 10, "bold")
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            pady=8
        )

        for row_num, (
            column,
            label,
            value
        ) in enumerate(
            fields,
            start=1
        ):
            ttk.Label(
                details_frame,
                text=label
            ).grid(
                row=row_num,
                column=0,
                padx=10,
                pady=8
            )

            entry = ttk.Entry(
                details_frame,
                width=25
            )
            entry.grid(
                row=row_num,
                column=1,
                padx=10,
                pady=8
            )

            entry.insert(
                0,
                value
            )

            detail_entries[column] = entry

    vehicle_box.bind(
        "<<ComboboxSelected>>",
        load_vehicle
    )

    def update():
        vehicle_id = vehicle_box.get()

        if not vehicle_id:
            messagebox.showwarning(
                "Select Vehicle",
                "Choose a vehicle."
            )
            return

        try:
            vtype = vehicle_map[vehicle_id]

            values = {}

            for column, entry in detail_entries.items():
                values[column] = float(
                    entry.get().strip()
                )

            if (
                vtype == "REFRIGERATED_VAN"
                and values["min_temperature_c"]
                > values["max_temperature_c"]
            ):
                raise ValueError(
                    "Minimum temperature cannot exceed maximum temperature."
                )

            db.execute(
                """
                UPDATE vehicle
                SET home_hub_id = %s
                WHERE vehicle_id = %s
                  AND carrier_id = %s
                """,
                (
                    hub_box.get(),
                    vehicle_id,
                    account_id
                )
            )

            if vtype == "BOX_TRUCK":
                db.execute(
                    """
                    UPDATE box_truck
                    SET cargo_volume_m3 = %s,
                        gross_weight_rating_kg = %s
                    WHERE vehicle_id = %s
                    """,
                    (
                        values["cargo_volume_m3"],
                        values[
                            "gross_weight_rating_kg"
                        ],
                        vehicle_id
                    )
                )

            elif vtype == "REFRIGERATED_VAN":
                db.execute(
                    """
                    UPDATE refrigerated_van
                    SET min_temperature_c = %s,
                        max_temperature_c = %s,
                        payload_limit_kg = %s
                    WHERE vehicle_id = %s
                    """,
                    (
                        values[
                            "min_temperature_c"
                        ],
                        values[
                            "max_temperature_c"
                        ],
                        values[
                            "payload_limit_kg"
                        ],
                        vehicle_id
                    )
                )

            else:
                axle = values["axle_count"]

                if not axle.is_integer():
                    raise ValueError(
                        "Axle count must be a whole number."
                    )

                db.execute(
                    """
                    UPDATE rail_car
                    SET axle_count = %s,
                        track_gauge_mm = %s
                    WHERE vehicle_id = %s
                    """,
                    (
                        int(axle),
                        values["track_gauge_mm"],
                        vehicle_id
                    )
                )

            messagebox.showinfo(
                "Updated",
                f"Vehicle {vehicle_id} was updated."
            )

            show_carrier_vehicles(
                account_id,
                display_name
            )

        except Exception as e:
            messagebox.showerror(
                "Update Vehicle Failed",
                str(e)
            )

    ttk.Button(
        root,
        text="Update Vehicle",
        command=update,
        width=25
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_carrier_dashboard(
            account_id,
            display_name
        ),
        width=25
    ).pack()


# =========================================================
# CARRIER - LIST DEPARTURES
# =========================================================

def show_carrier_departures(account_id, display_name):
    _, rows = db.query(
        """
        SELECT
            l.departure_id,
            l.vehicle_id,
            l.origin_hub_id,
            l.destination_hub_id,
            l.departure_datetime,
            l.booked_weight_kg,
            l.maximum_weight_kg,
            l.utilization_pct
        FROM v_departure_load l
        JOIN vehicle v
            ON v.vehicle_id = l.vehicle_id
        WHERE v.carrier_id = %s
        ORDER BY l.departure_id
        """,
        (account_id,)
    )

    show_rows(
        "My Departures",
        (
            "id",
            "vehicle",
            "origin",
            "dest",
            "time",
            "booked",
            "max",
            "util"
        ),
        (
            "ID",
            "Vehicle",
            "Origin",
            "Destination",
            "Date/Time",
            "Booked kg",
            "Max kg",
            "Utilization %"
        ),
        rows,
        (
            60,
            70,
            70,
            90,
            150,
            80,
            80,
            100
        ),
        lambda: show_carrier_dashboard(
            account_id,
            display_name
        )
    )


# =========================================================
# CARRIER - VEHICLE CAPACITY HELPER
# =========================================================

def vehicle_weight_limit(vehicle_id):
    _, rows = db.query(
        """
        SELECT
            COALESCE(
                b.gross_weight_rating_kg,
                r.payload_limit_kg
            )
        FROM vehicle v
        LEFT JOIN box_truck b
            ON b.vehicle_id = v.vehicle_id
        LEFT JOIN refrigerated_van r
            ON r.vehicle_id = v.vehicle_id
        WHERE v.vehicle_id = %s
        """,
        (vehicle_id,)
    )

    if rows and rows[0][0] is not None:
        return float(rows[0][0])

    return None


# =========================================================
# CARRIER - CREATE DEPARTURE
# =========================================================

def show_create_departure(account_id, display_name):
    clear_root()

    create_title("Create Departure")

    _, vehicles = db.query(
        """
        SELECT vehicle_id
        FROM vehicle
        WHERE carrier_id = %s
        ORDER BY vehicle_id
        """,
        (account_id,)
    )

    vehicle_ids = [
        str(row[0])
        for row in vehicles
    ]

    hubs = get_hubs()

    form = ttk.Frame(root)
    form.pack(pady=10)

    fields = [
        "Vehicle",
        "Origin",
        "Destination",
        "Departure Time",
        "Maximum Weight (kg)"
    ]

    for i, label in enumerate(fields):
        ttk.Label(
            form,
            text=label
        ).grid(
            row=i,
            column=0,
            padx=10,
            pady=8
        )

    vehicle_box = ttk.Combobox(
        form,
        values=vehicle_ids,
        state="readonly"
    )
    vehicle_box.grid(row=0, column=1)

    origin_box = ttk.Combobox(
        form,
        values=hubs,
        state="readonly"
    )
    origin_box.grid(row=1, column=1)

    destination_box = ttk.Combobox(
        form,
        values=hubs,
        state="readonly"
    )
    destination_box.grid(row=2, column=1)

    time_entry = ttk.Entry(form)
    time_entry.grid(row=3, column=1)

    weight_entry = ttk.Entry(form)
    weight_entry.grid(row=4, column=1)

    ttk.Label(
        root,
        text="Date/time format: YYYY-MM-DD HH:MM"
    ).pack()

    def create():
        vehicle_id = vehicle_box.get()
        origin = origin_box.get()
        destination = destination_box.get()

        if not all(
            (
                vehicle_id,
                origin,
                destination,
                time_entry.get().strip(),
                weight_entry.get().strip()
            )
        ):
            messagebox.showwarning(
                "Missing Information",
                "Fill out every field."
            )
            return

        try:
            if origin == destination:
                raise ValueError(
                    "Origin and destination must differ."
                )

            when = valid_datetime(
                time_entry.get().strip()
            )

            maximum = float(
                weight_entry.get().strip()
            )

            if maximum <= 0:
                raise ValueError(
                    "Maximum weight must be greater than 0."
                )

            limit = vehicle_weight_limit(
                vehicle_id
            )

            if (
                limit is not None
                and maximum > limit
            ):
                raise ValueError(
                    f"This vehicle can carry at most {limit} kg."
                )

            new_id = db.execute(
                """
                INSERT INTO departure (
                    vehicle_id,
                    origin_hub_id,
                    destination_hub_id,
                    departure_datetime,
                    maximum_weight_kg
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    vehicle_id,
                    origin,
                    destination,
                    when,
                    maximum
                )
            )

            messagebox.showinfo(
                "Created",
                f"Departure {new_id} was created."
            )

            show_carrier_departures(
                account_id,
                display_name
            )

        except Exception as e:
            messagebox.showerror(
                "Create Departure Failed",
                str(e)
            )

    ttk.Button(
        root,
        text="Create Departure",
        command=create,
        width=25
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_carrier_dashboard(
            account_id,
            display_name
        ),
        width=25
    ).pack()


# =========================================================
# CARRIER - UPDATE DEPARTURE
# =========================================================

def show_update_departure(account_id, display_name):
    clear_root()

    create_title("Update Departure")

    _, rows = db.query(
        """
        SELECT
            l.departure_id,
            l.vehicle_id,
            l.departure_datetime,
            l.maximum_weight_kg,
            l.booked_weight_kg
        FROM v_departure_load l
        JOIN vehicle v
            ON v.vehicle_id = l.vehicle_id
        WHERE v.carrier_id = %s
        ORDER BY l.departure_id
        """,
        (account_id,)
    )

    if not rows:
        messagebox.showinfo(
            "No Departures",
            "This carrier has no departures."
        )
        show_carrier_dashboard(
            account_id,
            display_name
        )
        return

    departure_map = {
        str(row[0]): row
        for row in rows
    }

    form = ttk.Frame(root)
    form.pack(pady=15)

    ttk.Label(
        form,
        text="Departure ID"
    ).grid(
        row=0,
        column=0,
        padx=10,
        pady=8
    )

    departure_box = ttk.Combobox(
        form,
        values=list(
            departure_map.keys()
        ),
        state="readonly",
        width=25
    )
    departure_box.grid(
        row=0,
        column=1,
        padx=10,
        pady=8
    )

    ttk.Label(
        form,
        text="Departure Time"
    ).grid(
        row=1,
        column=0,
        padx=10,
        pady=8
    )

    time_entry = ttk.Entry(
        form,
        width=28
    )
    time_entry.grid(
        row=1,
        column=1,
        padx=10,
        pady=8
    )

    ttk.Label(
        form,
        text="Maximum Weight (kg)"
    ).grid(
        row=2,
        column=0,
        padx=10,
        pady=8
    )

    weight_entry = ttk.Entry(
        form,
        width=28
    )
    weight_entry.grid(
        row=2,
        column=1,
        padx=10,
        pady=8
    )

    booked_label = ttk.Label(
        root,
        text=""
    )
    booked_label.pack(pady=5)

    def load(event=None):
        departure_id = departure_box.get()

        if not departure_id:
            return

        row = departure_map[departure_id]

        time_entry.delete(0, tk.END)
        time_entry.insert(
            0,
            row[2]
        )

        weight_entry.delete(0, tk.END)
        weight_entry.insert(
            0,
            row[3]
        )

        booked_label.config(
            text=(
                f"Currently booked weight: "
                f"{row[4]} kg"
            )
        )

    departure_box.bind(
        "<<ComboboxSelected>>",
        load
    )

    def update():
        departure_id = departure_box.get()

        if not departure_id:
            messagebox.showwarning(
                "Select Departure",
                "Choose a departure."
            )
            return

        try:
            row = departure_map[
                departure_id
            ]

            vehicle_id = row[1]
            booked_weight = float(row[4])

            when = valid_datetime(
                time_entry.get().strip()
            )

            maximum = float(
                weight_entry.get().strip()
            )

            if maximum < booked_weight:
                raise ValueError(
                    (
                        f"Cannot lower capacity below "
                        f"{booked_weight} kg because that "
                        f"amount is already booked."
                    )
                )

            limit = vehicle_weight_limit(
                vehicle_id
            )

            if (
                limit is not None
                and maximum > limit
            ):
                raise ValueError(
                    f"This vehicle can carry at most {limit} kg."
                )

            db.execute(
                """
                UPDATE departure
                SET departure_datetime = %s,
                    maximum_weight_kg = %s
                WHERE departure_id = %s
                """,
                (
                    when,
                    maximum,
                    departure_id
                )
            )

            messagebox.showinfo(
                "Updated",
                (
                    f"Departure {departure_id} "
                    f"was updated."
                )
            )

            show_carrier_departures(
                account_id,
                display_name
            )

        except Exception as e:
            messagebox.showerror(
                "Update Departure Failed",
                str(e)
            )

    ttk.Button(
        root,
        text="Update Departure",
        command=update,
        width=25
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_carrier_dashboard(
            account_id,
            display_name
        ),
        width=25
    ).pack()


# =========================================================
# CARRIER - POST SCAN
# =========================================================

def show_post_scan(account_id, display_name):
    clear_root()

    create_title("Post Scan Event")

    _, shipments = db.query(
        """
        SELECT DISTINCT
            s.shipment_id
        FROM booking b
        JOIN shipment s
            ON s.shipment_id = b.shipment_id
        JOIN departure d
            ON d.departure_id = b.departure_id
        JOIN vehicle v
            ON v.vehicle_id = d.vehicle_id
        WHERE v.carrier_id = %s
        ORDER BY s.shipment_id
        """,
        (account_id,)
    )

    shipment_ids = [
        str(row[0])
        for row in shipments
    ]

    hubs = get_hubs()

    form = ttk.Frame(root)
    form.pack(pady=15)

    ttk.Label(
        form,
        text="Shipment"
    ).grid(
        row=0,
        column=0,
        padx=10,
        pady=8
    )

    shipment_box = ttk.Combobox(
        form,
        values=shipment_ids,
        state="readonly",
        width=25
    )
    shipment_box.grid(row=0, column=1)

    ttk.Label(
        form,
        text="Hub"
    ).grid(
        row=1,
        column=0,
        padx=10,
        pady=8
    )

    hub_box = ttk.Combobox(
        form,
        values=hubs,
        state="readonly",
        width=25
    )
    hub_box.grid(row=1, column=1)

    ttk.Label(
        form,
        text="Status"
    ).grid(
        row=2,
        column=0,
        padx=10,
        pady=8
    )

    status_box = ttk.Combobox(
        form,
        values=[
            "RECEIVED",
            "IN_TRANSIT",
            "ARRIVED_AT_HUB",
            "OUT_FOR_DELIVERY",
            "DELIVERED"
        ],
        state="readonly",
        width=25
    )
    status_box.grid(row=2, column=1)

    ttk.Label(
        form,
        text="Timestamp"
    ).grid(
        row=3,
        column=0,
        padx=10,
        pady=8
    )

    time_entry = ttk.Entry(
        form,
        width=28
    )
    time_entry.grid(row=3, column=1)

    time_entry.insert(
        0,
        datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )
    )

    ttk.Label(
        root,
        text="Format: YYYY-MM-DD HH:MM"
    ).pack()

    def post():
        sid = shipment_box.get()
        hub = hub_box.get()
        status = status_box.get()

        if not all(
            (
                sid,
                hub,
                status,
                time_entry.get().strip()
            )
        ):
            messagebox.showwarning(
                "Missing Information",
                "Fill out every field."
            )
            return

        try:
            when = valid_datetime(
                time_entry.get().strip()
            )

            db.execute(
                """
                INSERT INTO scan_event (
                    shipment_id,
                    scan_sequence_no,
                    scan_timestamp,
                    hub_id,
                    status
                )
                SELECT
                    %s,
                    COALESCE(
                        MAX(scan_sequence_no),
                        0
                    ) + 1,
                    %s,
                    %s,
                    %s
                FROM scan_event
                WHERE shipment_id = %s
                """,
                (
                    sid,
                    when,
                    hub,
                    status,
                    sid
                )
            )

            _, updated = db.query(
                """
                SELECT
                    current_status,
                    COALESCE(
                        delivery_outcome,
                        '-'
                    )
                FROM shipment
                WHERE shipment_id = %s
                """,
                (sid,)
            )

            messagebox.showinfo(
                "Scan Posted",
                (
                    f"Scan added successfully.\n\n"
                    f"Current Status: "
                    f"{updated[0][0]}\n"
                    f"Delivery Outcome: "
                    f"{updated[0][1]}"
                )
            )

        except Exception as e:
            messagebox.showerror(
                "Scan Rejected",
                str(e)
            )

    ttk.Button(
        root,
        text="Post Scan",
        command=post,
        width=25
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_carrier_dashboard(
            account_id,
            display_name
        ),
        width=25
    ).pack()


# =========================================================
# CARRIER - REPORTS
# =========================================================

def show_carrier_reports(account_id, display_name):
    clear_root()

    create_title("Carrier Reports")

    _, summary = db.query(
        """
        SELECT
            COUNT(*) AS delivered,
            COALESCE(
                SUM(
                    s.delivery_outcome = 'ON_TIME'
                ),
                0
            ),
            COALESCE(
                SUM(
                    s.delivery_outcome = 'LATE'
                ),
                0
            ),
            ROUND(
                100 *
                SUM(
                    s.delivery_outcome = 'ON_TIME'
                ) /
                NULLIF(COUNT(*), 0),
                1
            )
        FROM shipment s
        JOIN booking b
            ON b.shipment_id = s.shipment_id
        JOIN departure d
            ON d.departure_id = b.departure_id
        JOIN vehicle v
            ON v.vehicle_id = d.vehicle_id
        WHERE v.carrier_id = %s
          AND s.delivery_outcome IS NOT NULL
        """,
        (account_id,)
    )

    delivered, on_time, late, pct = summary[0]

    ttk.Label(
        root,
        text=(
            f"Delivered: {delivered}     "
            f"On Time: {on_time}     "
            f"Late: {late}     "
            f"On-Time Rate: "
            f"{pct if pct is not None else '-'}%"
        ),
        font=("Arial", 12, "bold")
    ).pack(pady=15)

    _, rows = db.query(
        """
        SELECT
            l.departure_id,
            l.origin_hub_id,
            l.destination_hub_id,
            l.booked_weight_kg,
            l.maximum_weight_kg,
            l.utilization_pct
        FROM v_departure_load l
        JOIN vehicle v
            ON v.vehicle_id = l.vehicle_id
        WHERE v.carrier_id = %s
        ORDER BY l.departure_id
        """,
        (account_id,)
    )

    frame = ttk.Frame(root)
    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    tree = create_tree(
        frame,
        (
            "dep",
            "origin",
            "dest",
            "booked",
            "max",
            "util"
        ),
        (
            "Departure",
            "Origin",
            "Destination",
            "Booked kg",
            "Max kg",
            "Utilization %"
        ),
        (80, 80, 90, 100, 100, 110)
    )

    for row in rows:
        tree.insert(
            "",
            "end",
            values=row
        )

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_carrier_dashboard(
            account_id,
            display_name
        ),
        width=25
    ).pack(pady=15)


# =========================================================
# VIEWER DASHBOARD
# =========================================================

def show_viewer_dashboard(account_id, display_name):
    clear_root()

    create_title(
        f"Welcome, {display_name}",
        "Viewer Dashboard"
    )

    ttk.Button(
        root,
        text="Track Shipment",
        command=lambda: show_viewer_tracking(
            account_id,
            display_name
        ),
        width=30
    ).pack(pady=10)

    ttk.Button(
        root,
        text="Performance Reports",
        command=lambda: show_viewer_reports(
            account_id,
            display_name
        ),
        width=30
    ).pack(pady=10)

    ttk.Button(
        root,
        text="Logout",
        command=show_home,
        width=30
    ).pack(pady=20)


# =========================================================
# VIEWER - TRACK
# =========================================================

def show_viewer_tracking(account_id, display_name):
    clear_root()

    create_title("Track Shipment")

    ttk.Label(
        root,
        text="Shipment ID"
    ).pack(pady=5)

    entry = ttk.Entry(
        root,
        width=25
    )
    entry.pack()

    info_label = ttk.Label(
        root,
        text="",
        justify="left"
    )
    info_label.pack(pady=10)

    frame = ttk.Frame(root)
    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=15
    )

    tree = create_tree(
        frame,
        (
            "seq",
            "time",
            "hub",
            "status"
        ),
        (
            "Seq",
            "Timestamp",
            "Hub",
            "Status"
        ),
        (60, 180, 80, 150)
    )

    def track():
        shipment_id = entry.get().strip()

        if not shipment_id:
            messagebox.showwarning(
                "Shipment ID",
                "Enter a shipment ID."
            )
            return

        try:
            _, shipment = db.query(
                """
                SELECT
                    s.shipment_id,
                    sh.shipper_name,
                    s.origin_hub_id,
                    s.destination_hub_id,
                    s.weight_kg,
                    s.promised_delivery_date,
                    COALESCE(
                        s.current_status,
                        'NO SCANS'
                    ),
                    COALESCE(
                        s.delivery_outcome,
                        '-'
                    )
                FROM shipment s
                JOIN shipper sh
                    ON sh.account_id = s.shipper_id
                WHERE s.shipment_id = %s
                """,
                (shipment_id,)
            )

            if not shipment:
                messagebox.showerror(
                    "Not Found",
                    "No shipment exists with that ID."
                )
                return

            row = shipment[0]

            info_label.config(
                text=(
                    f"Shipment: {row[0]}\n"
                    f"Shipper: {row[1]}\n"
                    f"Route: {row[2]} → {row[3]}\n"
                    f"Weight: {row[4]} kg\n"
                    f"Promised: {row[5]}\n"
                    f"Current Status: {row[6]}\n"
                    f"Outcome: {row[7]}"
                )
            )

            for item in tree.get_children():
                tree.delete(item)

            _, rows = db.query(
                """
                SELECT
                    scan_sequence_no,
                    scan_timestamp,
                    hub_id,
                    status
                FROM scan_event
                WHERE shipment_id = %s
                ORDER BY scan_sequence_no
                """,
                (shipment_id,)
            )

            for row in rows:
                tree.insert(
                    "",
                    "end",
                    values=row
                )

        except Exception as e:
            messagebox.showerror(
                "Tracking Error",
                str(e)
            )

    ttk.Button(
        root,
        text="Track",
        command=track,
        width=25
    ).pack(pady=10)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_viewer_dashboard(
            account_id,
            display_name
        ),
        width=25
    ).pack(pady=10)


# =========================================================
# VIEWER - PERFORMANCE REPORTS
# =========================================================

def show_viewer_reports(account_id, display_name):
    clear_root()

    create_title("Published Performance Reports")

    notebook = ttk.Notebook(root)
    notebook.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    lane_tab = ttk.Frame(notebook)
    carrier_tab = ttk.Frame(notebook)

    notebook.add(
        lane_tab,
        text="By Lane"
    )

    notebook.add(
        carrier_tab,
        text="By Carrier"
    )

    _, lane_rows = db.query(
        """
        SELECT
            origin_hub_id,
            destination_hub_id,
            COUNT(*) AS delivered,
            SUM(
                delivery_outcome = 'ON_TIME'
            ) AS on_time,
            SUM(
                delivery_outcome = 'LATE'
            ) AS late,
            ROUND(
                100 *
                SUM(
                    delivery_outcome = 'ON_TIME'
                ) /
                COUNT(*),
                1
            ) AS on_time_pct
        FROM shipment
        WHERE delivery_outcome IS NOT NULL
        GROUP BY
            origin_hub_id,
            destination_hub_id
        ORDER BY
            origin_hub_id,
            destination_hub_id
        """
    )

    lane_tree = create_tree(
        lane_tab,
        (
            "origin",
            "dest",
            "delivered",
            "ontime",
            "late",
            "pct"
        ),
        (
            "Origin",
            "Destination",
            "Delivered",
            "On Time",
            "Late",
            "On-Time %"
        ),
        (90, 100, 90, 90, 80, 100)
    )

    for row in lane_rows:
        lane_tree.insert(
            "",
            "end",
            values=row
        )

    _, carrier_rows = db.query(
        """
        SELECT
            c.account_id,
            c.carrier_name,
            COUNT(*) AS delivered,
            SUM(
                s.delivery_outcome = 'ON_TIME'
            ) AS on_time,
            SUM(
                s.delivery_outcome = 'LATE'
            ) AS late,
            ROUND(
                100 *
                SUM(
                    s.delivery_outcome = 'ON_TIME'
                ) /
                COUNT(*),
                1
            ) AS on_time_pct
        FROM shipment s
        JOIN booking b
            ON b.shipment_id = s.shipment_id
        JOIN departure d
            ON d.departure_id = b.departure_id
        JOIN vehicle v
            ON v.vehicle_id = d.vehicle_id
        JOIN carrier c
            ON c.account_id = v.carrier_id
        WHERE s.delivery_outcome IS NOT NULL
        GROUP BY
            c.account_id,
            c.carrier_name
        ORDER BY c.account_id
        """
    )

    carrier_tree = create_tree(
        carrier_tab,
        (
            "id",
            "name",
            "delivered",
            "ontime",
            "late",
            "pct"
        ),
        (
            "Carrier ID",
            "Carrier",
            "Delivered",
            "On Time",
            "Late",
            "On-Time %"
        ),
        (90, 190, 90, 90, 80, 100)
    )

    for row in carrier_rows:
        carrier_tree.insert(
            "",
            "end",
            values=row
        )

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_viewer_dashboard(
            account_id,
            display_name
        ),
        width=25
    ).pack(pady=12)


# =========================================================
# REQUIRED ANALYTICAL QUERIES
# =========================================================

def show_queries_menu():
    clear_root()

    create_title(
        "Required Analytical Queries",
        "Select a query to run"
    )

    options = [
        (
            "1. Vehicle counts by carrier/type",
            query1
        ),
        (
            "2. Departure utilization ranking by lane",
            query2_prompt
        ),
        (
            "3. Shipment dwell times",
            query3_prompt
        ),
        (
            "4. Running delivered weight by carrier",
            query4
        ),
        (
            "5. Multi-shipper departures",
            query5
        ),
        (
            "6. Shipments with no scans",
            query6
        )
    ]

    for label, command in options:
        ttk.Button(
            root,
            text=label,
            command=command,
            width=48
        ).pack(pady=8)

    ttk.Button(
        root,
        text="Back",
        command=show_home,
        width=25
    ).pack(pady=20)


def show_query_result(
    title,
    columns,
    headings,
    rows,
    widths=None
):
    show_rows(
        title,
        columns,
        headings,
        rows,
        widths,
        show_queries_menu
    )


# =========================================================
# QUERY 1
# =========================================================

def query1():
    try:
        _, rows = db.query(
            """
            SELECT
                c.account_id,
                c.carrier_name,
                v.vehicle_type,
                COUNT(*) AS vehicle_count
            FROM carrier c
            JOIN vehicle v
                ON v.carrier_id = c.account_id
            GROUP BY
                c.account_id,
                c.carrier_name,
                v.vehicle_type
            ORDER BY
                c.account_id,
                v.vehicle_type
            """
        )

        show_query_result(
            "Query 1 - Vehicle Counts",
            (
                "id",
                "carrier",
                "type",
                "count"
            ),
            (
                "Carrier ID",
                "Carrier",
                "Type",
                "Vehicle Count"
            ),
            rows,
            (90, 220, 180, 110)
        )

    except Exception as e:
        messagebox.showerror(
            "Query Error",
            str(e)
        )


# =========================================================
# QUERY 2
# =========================================================

def query2_prompt():
    clear_root()

    create_title(
        "Query 2",
        "Rank departures by utilization within each lane"
    )

    ttk.Label(
        root,
        text="Top N departures per lane"
    ).pack(pady=10)

    entry = ttk.Entry(
        root,
        width=20
    )
    entry.pack()

    entry.insert(
        0,
        "5"
    )

    def run():
        try:
            n = int(
                entry.get().strip()
            )

            if n <= 0:
                raise ValueError(
                    "N must be greater than 0."
                )

            _, rows = db.query(
                """
                SELECT *
                FROM (
                    SELECT
                        origin_hub_id,
                        destination_hub_id,
                        departure_id,
                        departure_datetime,
                        booked_weight_kg,
                        maximum_weight_kg,
                        utilization_pct,
                        RANK() OVER (
                            PARTITION BY
                                origin_hub_id,
                                destination_hub_id
                            ORDER BY
                                utilization_pct DESC
                        ) AS lane_rank
                    FROM v_departure_load
                ) ranked
                WHERE lane_rank <= %s
                ORDER BY
                    origin_hub_id,
                    destination_hub_id,
                    lane_rank,
                    departure_id
                """,
                (n,)
            )

            show_query_result(
                "Query 2 - Utilization Rankings",
                (
                    "origin",
                    "dest",
                    "dep",
                    "time",
                    "booked",
                    "max",
                    "util",
                    "rank"
                ),
                (
                    "Origin",
                    "Destination",
                    "Departure",
                    "Date/Time",
                    "Booked",
                    "Maximum",
                    "Utilization %",
                    "Rank"
                ),
                rows,
                (
                    70,
                    90,
                    80,
                    150,
                    80,
                    80,
                    100,
                    60
                )
            )

        except Exception as e:
            messagebox.showerror(
                "Query Error",
                str(e)
            )

    ttk.Button(
        root,
        text="Run Query",
        command=run,
        width=25
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=show_queries_menu,
        width=25
    ).pack()


# =========================================================
# QUERY 3
# =========================================================

def query3_prompt():
    clear_root()

    create_title(
        "Query 3",
        "Time between consecutive scan events"
    )

    ttk.Label(
        root,
        text="Shipment ID"
    ).pack(pady=10)

    entry = ttk.Entry(
        root,
        width=20
    )
    entry.pack()

    def run():
        shipment_id = entry.get().strip()

        if not shipment_id:
            messagebox.showwarning(
                "Shipment ID",
                "Enter a shipment ID."
            )
            return

        try:
            _, rows = db.query(
                """
                SELECT
                    shipment_id,
                    scan_sequence_no,
                    status,
                    hub_id,
                    scan_timestamp,
                    LAG(scan_timestamp)
                        OVER w
                        AS previous_scan_time,
                    LAG(hub_id)
                        OVER w
                        AS previous_hub,
                    TIMESTAMPDIFF(
                        MINUTE,
                        LAG(scan_timestamp)
                            OVER w,
                        scan_timestamp
                    )
                        AS minutes_since_previous,
                    ROUND(
                        TIMESTAMPDIFF(
                            MINUTE,
                            LAG(scan_timestamp)
                                OVER w,
                            scan_timestamp
                        ) / 60,
                        2
                    )
                        AS hours_since_previous
                FROM scan_event
                WHERE shipment_id = %s
                WINDOW w AS (
                    PARTITION BY shipment_id
                    ORDER BY scan_sequence_no
                )
                ORDER BY scan_sequence_no
                """,
                (shipment_id,)
            )

            show_query_result(
                "Query 3 - Shipment Dwell Times",
                (
                    "shipment",
                    "seq",
                    "status",
                    "hub",
                    "time",
                    "prevtime",
                    "prevhub",
                    "minutes",
                    "hours"
                ),
                (
                    "Shipment",
                    "Seq",
                    "Status",
                    "Hub",
                    "Timestamp",
                    "Previous Time",
                    "Previous Hub",
                    "Minutes",
                    "Hours"
                ),
                rows,
                (
                    70,
                    50,
                    130,
                    60,
                    150,
                    150,
                    90,
                    80,
                    70
                )
            )

        except Exception as e:
            messagebox.showerror(
                "Query Error",
                str(e)
            )

    ttk.Button(
        root,
        text="Run Query",
        command=run,
        width=25
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=show_queries_menu,
        width=25
    ).pack()


# =========================================================
# QUERY 4
# =========================================================

def query4():
    try:
        _, rows = db.query(
            """
            WITH delivered AS (
                SELECT
                    v.carrier_id,
                    DATE_SUB(
                        DATE(sc.scan_timestamp),
                        INTERVAL
                            WEEKDAY(sc.scan_timestamp)
                            DAY
                    ) AS week_start,
                    s.weight_kg
                FROM scan_event sc
                JOIN shipment s
                    ON s.shipment_id =
                       sc.shipment_id
                JOIN booking b
                    ON b.shipment_id =
                       s.shipment_id
                JOIN departure d
                    ON d.departure_id =
                       b.departure_id
                JOIN vehicle v
                    ON v.vehicle_id =
                       d.vehicle_id
                WHERE sc.status = 'DELIVERED'
            ),
            weekly AS (
                SELECT
                    carrier_id,
                    week_start,
                    SUM(weight_kg)
                        AS delivered_kg
                FROM delivered
                GROUP BY
                    carrier_id,
                    week_start
            )
            SELECT
                w.carrier_id,
                c.carrier_name,
                w.week_start,
                w.delivered_kg,
                SUM(w.delivered_kg)
                    OVER (
                        PARTITION BY w.carrier_id
                        ORDER BY w.week_start
                        ROWS BETWEEN
                            UNBOUNDED PRECEDING
                            AND CURRENT ROW
                    )
                    AS cumulative_delivered_kg
            FROM weekly w
            JOIN carrier c
                ON c.account_id =
                   w.carrier_id
            ORDER BY
                w.carrier_id,
                w.week_start
            """
        )

        show_query_result(
            "Query 4 - Running Delivered Weight",
            (
                "carrier",
                "name",
                "week",
                "weekkg",
                "total"
            ),
            (
                "Carrier ID",
                "Carrier",
                "Week",
                "Delivered kg",
                "Running Total"
            ),
            rows,
            (90, 220, 110, 110, 120)
        )

    except Exception as e:
        messagebox.showerror(
            "Query Error",
            str(e)
        )


# =========================================================
# QUERY 5
# =========================================================

def query5():
    try:
        _, rows = db.query(
            """
            SELECT
                b.departure_id,
                COUNT(
                    DISTINCT s.shipper_id
                ) AS distinct_shippers
            FROM booking b
            JOIN shipment s
                ON s.shipment_id =
                   b.shipment_id
            GROUP BY b.departure_id
            HAVING COUNT(
                DISTINCT s.shipper_id
            ) >= 2
            ORDER BY b.departure_id
            """
        )

        show_query_result(
            "Query 5 - Multi-Shipper Departures",
            (
                "departure",
                "count"
            ),
            (
                "Departure",
                "Distinct Shippers"
            ),
            rows,
            (150, 160)
        )

    except Exception as e:
        messagebox.showerror(
            "Query Error",
            str(e)
        )


# =========================================================
# QUERY 6
# =========================================================

def query6():
    try:
        _, rows = db.query(
            """
            SELECT
                s.shipment_id,
                s.shipper_id,
                sh.shipper_name,
                s.origin_hub_id,
                s.destination_hub_id,
                s.promised_delivery_date
            FROM shipment s
            JOIN shipper sh
                ON sh.account_id =
                   s.shipper_id
            WHERE NOT EXISTS (
                SELECT 1
                FROM scan_event e
                WHERE e.shipment_id =
                      s.shipment_id
            )
            ORDER BY s.shipment_id
            """
        )

        show_query_result(
            "Query 6 - Shipments With No Scans",
            (
                "shipment",
                "shipper",
                "name",
                "origin",
                "dest",
                "promised"
            ),
            (
                "Shipment",
                "Shipper ID",
                "Shipper",
                "Origin",
                "Destination",
                "Promised"
            ),
            rows,
            (90, 90, 220, 80, 100, 110)
        )

    except Exception as e:
        messagebox.showerror(
            "Query Error",
            str(e)
        )


# =========================================================
# START APPLICATION
# =========================================================

root = tk.Tk()

root.title(
    "Freight Tracking and Delivery Management"
)

root.geometry(
    "1100x750"
)

root.minsize(
    900,
    650
)

show_home()

root.mainloop()
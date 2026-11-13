import tkinter as tk
from tkinter import ttk, messagebox

from app import db


# =========================================================
# HELPERS
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


def show_rows(title, columns, headings, rows, widths=None, back_command=None):
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


# =========================================================
# HOME
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

    ttk.Label(form, text="Username").grid(
        row=0, column=0, padx=10, pady=10
    )

    username_entry = ttk.Entry(form, width=30)
    username_entry.grid(
        row=0, column=1, padx=10, pady=10
    )

    ttk.Label(form, text="Password").grid(
        row=1, column=0, padx=10, pady=10
    )

    password_entry = ttk.Entry(
        form,
        width=30,
        show="*"
    )
    password_entry.grid(
        row=1, column=1, padx=10, pady=10
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
                show_shipper_dashboard(account_id, display_name)

            elif role == "Carrier":
                show_carrier_dashboard(account_id, display_name)

            elif role == "Viewer":
                show_viewer_dashboard(account_id, display_name)

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

    ttk.Button(
        root,
        text="List My Shipments",
        command=lambda: show_shipper_shipments(
            account_id,
            display_name
        ),
        width=32
    ).pack(pady=7)

    ttk.Button(
        root,
        text="Create Shipment",
        command=lambda: show_create_shipment(
            account_id,
            display_name
        ),
        width=32
    ).pack(pady=7)

    ttk.Button(
        root,
        text="Update Shipment",
        command=lambda: show_update_shipment(
            account_id,
            display_name
        ),
        width=32
    ).pack(pady=7)

    ttk.Button(
        root,
        text="Book Shipment",
        command=lambda: show_book_shipment(
            account_id,
            display_name
        ),
        width=32
    ).pack(pady=7)

    ttk.Button(
        root,
        text="Track Shipment",
        command=lambda: show_track_shipment(
            account_id,
            display_name
        ),
        width=32
    ).pack(pady=7)

    ttk.Button(
        root,
        text="Reports",
        command=lambda: show_shipper_reports(
            account_id,
            display_name
        ),
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
                COALESCE(s.current_status, 'NO SCANS'),
                COALESCE(s.delivery_outcome, '-'),
                COALESCE(b.departure_id, '-')
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
        messagebox.showerror("Database Error", str(e))


# =========================================================
# SHIPPER - CREATE
# =========================================================

def show_create_shipment(account_id, display_name):
    clear_root()

    create_title("Create Shipment")

    _, hub_rows = db.query(
        "SELECT hub_id FROM hub ORDER BY hub_id"
    )

    hubs = [row[0] for row in hub_rows]

    form = ttk.Frame(root)
    form.pack(pady=15)

    ttk.Label(form, text="Origin Hub").grid(
        row=0, column=0, padx=10, pady=10
    )

    origin_box = ttk.Combobox(
        form,
        values=hubs,
        state="readonly"
    )
    origin_box.grid(row=0, column=1)

    ttk.Label(form, text="Destination Hub").grid(
        row=1, column=0, padx=10, pady=10
    )

    destination_box = ttk.Combobox(
        form,
        values=hubs,
        state="readonly"
    )
    destination_box.grid(row=1, column=1)

    ttk.Label(form, text="Weight (kg)").grid(
        row=2, column=0, padx=10, pady=10
    )

    weight_entry = ttk.Entry(form)
    weight_entry.grid(row=2, column=1)

    ttk.Label(form, text="Promised Date").grid(
        row=3, column=0, padx=10, pady=10
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
        weight = weight_entry.get().strip()
        promised = date_entry.get().strip()

        if not all((origin, destination, weight, promised)):
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
            weight = float(weight)

            if weight <= 0:
                raise ValueError

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
                "Created",
                f"Shipment {new_id} created."
            )

            show_shipper_shipments(
                account_id,
                display_name
            )

        except ValueError:
            messagebox.showerror(
                "Invalid Weight",
                "Weight must be greater than 0."
            )

        except Exception as e:
            messagebox.showerror(
                "Database Error",
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

    shipment_ids = [str(row[0]) for row in rows]

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

    _, hub_rows = db.query(
        "SELECT hub_id FROM hub ORDER BY hub_id"
    )

    hubs = [row[0] for row in hub_rows]

    form = ttk.Frame(root)
    form.pack(pady=15)

    labels = [
        "Shipment ID",
        "Origin Hub",
        "Destination Hub",
        "Weight",
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

        if not sid:
            messagebox.showwarning(
                "Select Shipment",
                "Choose a shipment."
            )
            return

        origin = origin_box.get()
        destination = destination_box.get()

        if origin == destination:
            messagebox.showerror(
                "Invalid Route",
                "Origin and destination must differ."
            )
            return

        try:
            weight = float(weight_entry.get())

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
                    date_entry.get(),
                    sid,
                    account_id
                )
            )

            messagebox.showinfo(
                "Updated",
                f"Shipment {sid} updated."
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

    ids = [str(row[0]) for row in rows]

    ttk.Label(
        root,
        text="Select Shipment"
    ).pack(pady=5)

    shipment_box = ttk.Combobox(
        root,
        values=ids,
        state="readonly"
    )
    shipment_box.pack()

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
            """,
            (sid,)
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
            tree.insert("", "end", values=row)

    shipment_box.bind(
        "<<ComboboxSelected>>",
        load_departures
    )

    def book():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Departure",
                "Choose a departure."
            )
            return

        sid = int(shipment_box.get())

        departure_id = int(
            tree.item(selected[0])["values"][0]
        )

        try:
            db.call_proc(
                "book_shipment",
                (sid, departure_id)
            )

            messagebox.showinfo(
                "Booked",
                f"Shipment {sid} booked onto departure {departure_id}."
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
        command=book
    ).pack(pady=10)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_shipper_dashboard(
            account_id,
            display_name
        )
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

    ids = [str(row[0]) for row in rows]

    shipment_box = ttk.Combobox(
        root,
        values=ids,
        state="readonly"
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
            return

        _, s = db.query(
            """
            SELECT
                origin_hub_id,
                destination_hub_id,
                weight_kg,
                promised_delivery_date,
                COALESCE(current_status, 'NO SCANS'),
                COALESCE(delivery_outcome, '-')
            FROM shipment
            WHERE shipment_id = %s
              AND shipper_id = %s
            """,
            (sid, account_id)
        )

        if not s:
            return

        row = s[0]

        info.config(
            text=(
                f"Route: {row[0]} → {row[1]}\n"
                f"Weight: {row[2]} kg\n"
                f"Promised: {row[3]}\n"
                f"Status: {row[4]}\n"
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
            tree.insert("", "end", values=scan)

    ttk.Button(
        root,
        text="Track",
        command=track
    ).pack(pady=10)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_shipper_dashboard(
            account_id,
            display_name
        )
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
            COUNT(*),
            COALESCE(SUM(delivery_outcome='ON_TIME'), 0),
            COALESCE(SUM(delivery_outcome='LATE'), 0)
        FROM shipment
        WHERE shipper_id = %s
          AND delivery_outcome IS NOT NULL
        """,
        (account_id,)
    )

    delivered, on_time, late = summary[0]

    ttk.Label(
        root,
        text=(
            f"Delivered: {delivered}     "
            f"On Time: {on_time}     "
            f"Late: {late}"
        ),
        font=("Arial", 12, "bold")
    ).pack(pady=15)

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
        )
    )

    for row in rows:
        tree.insert("", "end", values=row)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_shipper_dashboard(
            account_id,
            display_name
        )
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

    ttk.Button(
        root,
        text="List My Vehicles",
        command=lambda: show_carrier_vehicles(
            account_id,
            display_name
        ),
        width=30
    ).pack(pady=7)

    ttk.Button(
        root,
        text="Create Vehicle",
        command=lambda: show_create_vehicle(
            account_id,
            display_name
        ),
        width=30
    ).pack(pady=7)

    ttk.Button(
        root,
        text="List Departures",
        command=lambda: show_carrier_departures(
            account_id,
            display_name
        ),
        width=30
    ).pack(pady=7)

    ttk.Button(
        root,
        text="Create Departure",
        command=lambda: show_create_departure(
            account_id,
            display_name
        ),
        width=30
    ).pack(pady=7)

    ttk.Button(
        root,
        text="Post Scan Event",
        command=lambda: show_post_scan(
            account_id,
            display_name
        ),
        width=30
    ).pack(pady=7)

    ttk.Button(
        root,
        text="Reports",
        command=lambda: show_carrier_reports(
            account_id,
            display_name
        ),
        width=30
    ).pack(pady=7)

    ttk.Button(
        root,
        text="Logout",
        command=show_home,
        width=30
    ).pack(pady=20)


# =========================================================
# CARRIER - LIST VEHICLES
# =========================================================

def show_carrier_vehicles(account_id, display_name):
    _, rows = db.query(
        """
        SELECT
            vehicle_id,
            vehicle_type,
            home_hub_id
        FROM vehicle
        WHERE carrier_id = %s
        ORDER BY vehicle_id
        """,
        (account_id,)
    )

    show_rows(
        "My Vehicles",
        ("id", "type", "hub"),
        ("Vehicle ID", "Type", "Home Hub"),
        rows,
        (100, 200, 100),
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

    _, hub_rows = db.query(
        "SELECT hub_id FROM hub ORDER BY hub_id"
    )

    hubs = [r[0] for r in hub_rows]

    form = ttk.Frame(root)
    form.pack(pady=15)

    ttk.Label(form, text="Vehicle Type").grid(
        row=0, column=0, padx=10, pady=10
    )

    type_box = ttk.Combobox(
        form,
        values=[
            "BOX_TRUCK",
            "REFRIGERATED_VAN",
            "RAIL_CAR"
        ],
        state="readonly"
    )
    type_box.grid(row=0, column=1)

    ttk.Label(form, text="Home Hub").grid(
        row=1, column=0, padx=10, pady=10
    )

    hub_box = ttk.Combobox(
        form,
        values=hubs,
        state="readonly"
    )
    hub_box.grid(row=1, column=1)

    ttk.Label(
        root,
        text=(
            "Enter subtype values separated by commas.\n"
            "Box truck: cargo volume, gross weight rating\n"
            "Refrigerated van: min temp, max temp, payload limit\n"
            "Rail car: axle count, track gauge"
        ),
        justify="center"
    ).pack(pady=10)

    values_entry = ttk.Entry(
        root,
        width=45
    )
    values_entry.pack()

    def create():
        vtype = type_box.get()
        hub = hub_box.get()

        try:
            values = [
                x.strip()
                for x in values_entry.get().split(",")
            ]

            table_map = {
                "BOX_TRUCK": (
                    "box_truck",
                    [
                        "cargo_volume_m3",
                        "gross_weight_rating_kg"
                    ]
                ),
                "REFRIGERATED_VAN": (
                    "refrigerated_van",
                    [
                        "min_temperature_c",
                        "max_temperature_c",
                        "payload_limit_kg"
                    ]
                ),
                "RAIL_CAR": (
                    "rail_car",
                    [
                        "axle_count",
                        "track_gauge_mm"
                    ]
                )
            }

            table, columns = table_map[vtype]

            if len(values) != len(columns):
                raise ValueError(
                    "Incorrect number of subtype values."
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
                    (account_id, hub, vtype)
                )

                vid = cur.lastrowid

                column_sql = ", ".join(columns)
                placeholders = ", ".join(
                    ["%s"] * len(columns)
                )

                cur.execute(
                    f"""
                    INSERT INTO {table}
                    (vehicle_id, {column_sql})
                    VALUES (%s, {placeholders})
                    """,
                    [vid] + values
                )

            messagebox.showinfo(
                "Created",
                f"Vehicle {vid} created."
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
        command=create
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_carrier_dashboard(
            account_id,
            display_name
        )
    ).pack()


# =========================================================
# CARRIER - DEPARTURES
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
            l.maximum_weight_kg
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
            "max"
        ),
        (
            "ID",
            "Vehicle",
            "Origin",
            "Destination",
            "Date/Time",
            "Booked kg",
            "Max kg"
        ),
        rows,
        (60, 70, 70, 90, 150, 80, 80),
        lambda: show_carrier_dashboard(
            account_id,
            display_name
        )
    )


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

    _, hubs = db.query(
        "SELECT hub_id FROM hub ORDER BY hub_id"
    )

    vehicle_ids = [str(r[0]) for r in vehicles]
    hub_ids = [r[0] for r in hubs]

    form = ttk.Frame(root)
    form.pack(pady=10)

    fields = [
        "Vehicle",
        "Origin",
        "Destination",
        "Departure Time",
        "Maximum Weight"
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
        values=hub_ids,
        state="readonly"
    )
    origin_box.grid(row=1, column=1)

    dest_box = ttk.Combobox(
        form,
        values=hub_ids,
        state="readonly"
    )
    dest_box.grid(row=2, column=1)

    time_entry = ttk.Entry(form)
    time_entry.grid(row=3, column=1)

    weight_entry = ttk.Entry(form)
    weight_entry.grid(row=4, column=1)

    ttk.Label(
        root,
        text="Date/time format: YYYY-MM-DD HH:MM"
    ).pack()

    def create():
        try:
            if origin_box.get() == dest_box.get():
                raise ValueError(
                    "Origin and destination must differ."
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
                    vehicle_box.get(),
                    origin_box.get(),
                    dest_box.get(),
                    time_entry.get(),
                    weight_entry.get()
                )
            )

            messagebox.showinfo(
                "Created",
                f"Departure {new_id} created."
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
        command=create
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_carrier_dashboard(
            account_id,
            display_name
        )
    ).pack()


# =========================================================
# CARRIER - POST SCAN
# =========================================================

def show_post_scan(account_id, display_name):
    clear_root()

    create_title("Post Scan Event")

    _, shipments = db.query(
        """
        SELECT s.shipment_id
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

    _, hubs = db.query(
        "SELECT hub_id FROM hub ORDER BY hub_id"
    )

    shipment_ids = [str(r[0]) for r in shipments]
    hub_ids = [r[0] for r in hubs]

    form = ttk.Frame(root)
    form.pack(pady=15)

    ttk.Label(form, text="Shipment").grid(
        row=0, column=0, padx=10, pady=8
    )

    shipment_box = ttk.Combobox(
        form,
        values=shipment_ids,
        state="readonly"
    )
    shipment_box.grid(row=0, column=1)

    ttk.Label(form, text="Hub").grid(
        row=1, column=0, padx=10, pady=8
    )

    hub_box = ttk.Combobox(
        form,
        values=hub_ids,
        state="readonly"
    )
    hub_box.grid(row=1, column=1)

    ttk.Label(form, text="Status").grid(
        row=2, column=0, padx=10, pady=8
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
        state="readonly"
    )
    status_box.grid(row=2, column=1)

    ttk.Label(form, text="Timestamp").grid(
        row=3, column=0, padx=10, pady=8
    )

    time_entry = ttk.Entry(form)
    time_entry.grid(row=3, column=1)

    ttk.Label(
        root,
        text="Format: YYYY-MM-DD HH:MM"
    ).pack()

    def post():
        sid = shipment_box.get()

        try:
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
                    time_entry.get(),
                    hub_box.get(),
                    status_box.get(),
                    sid
                )
            )

            messagebox.showinfo(
                "Scan Posted",
                "Scan event successfully added."
            )

        except Exception as e:
            messagebox.showerror(
                "Scan Rejected",
                str(e)
            )

    ttk.Button(
        root,
        text="Post Scan",
        command=post
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_carrier_dashboard(
            account_id,
            display_name
        )
    ).pack()


# =========================================================
# CARRIER REPORTS
# =========================================================

def show_carrier_reports(account_id, display_name):
    _, rows = db.query(
        """
        SELECT
            l.departure_id,
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
        "Carrier Reports",
        ("dep", "booked", "max", "util"),
        (
            "Departure",
            "Booked kg",
            "Max kg",
            "Utilization %"
        ),
        rows,
        (100, 100, 100, 120),
        lambda: show_carrier_dashboard(
            account_id,
            display_name
        )
    )


# =========================================================
# VIEWER
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


def show_viewer_tracking(account_id, display_name):
    clear_root()

    create_title("Track Shipment")

    ttk.Label(
        root,
        text="Shipment ID"
    ).pack(pady=5)

    entry = ttk.Entry(root)
    entry.pack()

    frame = ttk.Frame(root)
    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=15
    )

    tree = create_tree(
        frame,
        ("seq", "time", "hub", "status"),
        ("Seq", "Timestamp", "Hub", "Status")
    )

    def track():
        for item in tree.get_children():
            tree.delete(item)

        try:
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
                (entry.get(),)
            )

            for row in rows:
                tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror(
                "Tracking Error",
                str(e)
            )

    ttk.Button(
        root,
        text="Track",
        command=track
    ).pack(pady=10)

    ttk.Button(
        root,
        text="Back",
        command=lambda: show_viewer_dashboard(
            account_id,
            display_name
        )
    ).pack(pady=10)


def show_viewer_reports(account_id, display_name):
    _, rows = db.query(
        """
        SELECT
            origin_hub_id,
            destination_hub_id,
            COUNT(*) AS delivered,
            SUM(delivery_outcome='ON_TIME'),
            SUM(delivery_outcome='LATE'),
            ROUND(
                100 *
                SUM(delivery_outcome='ON_TIME')
                / COUNT(*),
                1
            )
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

    show_rows(
        "On-Time Performance by Lane",
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
        rows,
        back_command=lambda: show_viewer_dashboard(
            account_id,
            display_name
        )
    )


# =========================================================
# SIX REQUIRED QUERIES
# =========================================================

def show_queries_menu():
    clear_root()

    create_title(
        "Required Analytical Queries"
    )

    buttons = [
        (
            "1. Vehicle counts by carrier/type",
            query1
        ),
        (
            "2. Departure utilization ranking",
            query2
        ),
        (
            "3. Shipment dwell times",
            query3_prompt
        ),
        (
            "4. Running delivered weight",
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

    for label, command in buttons:
        ttk.Button(
            root,
            text=label,
            command=command,
            width=45
        ).pack(pady=8)

    ttk.Button(
        root,
        text="Back",
        command=show_home,
        width=25
    ).pack(pady=20)


def show_query_result(title, columns, headings, rows):
    show_rows(
        title,
        columns,
        headings,
        rows,
        back_command=show_queries_menu
    )


def query1():
    _, rows = db.query(
        """
        SELECT
            c.account_id,
            c.carrier_name,
            v.vehicle_type,
            COUNT(*)
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
        "Query 1",
        ("id", "carrier", "type", "count"),
        ("Carrier ID", "Carrier", "Type", "Count"),
        rows
    )


def query2():
    _, rows = db.query(
        """
        SELECT
            origin_hub_id,
            destination_hub_id,
            departure_id,
            utilization_pct,
            RANK() OVER (
                PARTITION BY
                    origin_hub_id,
                    destination_hub_id
                ORDER BY utilization_pct DESC
            )
        FROM v_departure_load
        ORDER BY
            origin_hub_id,
            destination_hub_id,
            utilization_pct DESC
        """
    )

    show_query_result(
        "Query 2",
        ("origin", "dest", "dep", "util", "rank"),
        (
            "Origin",
            "Destination",
            "Departure",
            "Utilization %",
            "Rank"
        ),
        rows
    )


def query3_prompt():
    clear_root()

    create_title("Query 3 - Dwell Time")

    ttk.Label(
        root,
        text="Shipment ID"
    ).pack(pady=10)

    entry = ttk.Entry(root)
    entry.pack()

    def run():
        _, rows = db.query(
            """
            SELECT
                shipment_id,
                scan_sequence_no,
                status,
                hub_id,
                scan_timestamp,
                TIMESTAMPDIFF(
                    MINUTE,
                    LAG(scan_timestamp) OVER (
                        PARTITION BY shipment_id
                        ORDER BY scan_sequence_no
                    ),
                    scan_timestamp
                )
            FROM scan_event
            WHERE shipment_id = %s
            ORDER BY scan_sequence_no
            """,
            (entry.get(),)
        )

        show_query_result(
            "Query 3",
            (
                "id",
                "seq",
                "status",
                "hub",
                "time",
                "minutes"
            ),
            (
                "Shipment",
                "Seq",
                "Status",
                "Hub",
                "Timestamp",
                "Minutes Since Previous"
            ),
            rows
        )

    ttk.Button(
        root,
        text="Run Query",
        command=run
    ).pack(pady=15)

    ttk.Button(
        root,
        text="Back",
        command=show_queries_menu
    ).pack()


def query4():
    _, rows = db.query(
        """
        WITH delivered AS (
            SELECT
                v.carrier_id,
                DATE_SUB(
                    DATE(sc.scan_timestamp),
                    INTERVAL WEEKDAY(sc.scan_timestamp) DAY
                ) AS week_start,
                s.weight_kg
            FROM scan_event sc
            JOIN shipment s
                ON s.shipment_id = sc.shipment_id
            JOIN booking b
                ON b.shipment_id = s.shipment_id
            JOIN departure d
                ON d.departure_id = b.departure_id
            JOIN vehicle v
                ON v.vehicle_id = d.vehicle_id
            WHERE sc.status = 'DELIVERED'
        ),
        weekly AS (
            SELECT
                carrier_id,
                week_start,
                SUM(weight_kg) AS delivered_kg
            FROM delivered
            GROUP BY carrier_id, week_start
        )
        SELECT
            carrier_id,
            week_start,
            delivered_kg,
            SUM(delivered_kg) OVER (
                PARTITION BY carrier_id
                ORDER BY week_start
            )
        FROM weekly
        ORDER BY carrier_id, week_start
        """
    )

    show_query_result(
        "Query 4",
        ("carrier", "week", "weekkg", "total"),
        (
            "Carrier",
            "Week",
            "Delivered kg",
            "Running Total"
        ),
        rows
    )


def query5():
    _, rows = db.query(
        """
        SELECT
            b.departure_id,
            COUNT(DISTINCT s.shipper_id)
        FROM booking b
        JOIN shipment s
            ON s.shipment_id = b.shipment_id
        GROUP BY b.departure_id
        HAVING COUNT(DISTINCT s.shipper_id) >= 2
        ORDER BY b.departure_id
        """
    )

    show_query_result(
        "Query 5",
        ("dep", "count"),
        ("Departure", "Distinct Shippers"),
        rows
    )


def query6():
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
            ON sh.account_id = s.shipper_id
        WHERE NOT EXISTS (
            SELECT 1
            FROM scan_event e
            WHERE e.shipment_id = s.shipment_id
        )
        ORDER BY s.shipment_id
        """
    )

    show_query_result(
        "Query 6",
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
        rows
    )


# =========================================================
# START
# =========================================================

root = tk.Tk()

root.title(
    "Freight Tracking and Delivery Management"
)

root.geometry("1000x700")

root.minsize(850, 600)

show_home()

root.mainloop()
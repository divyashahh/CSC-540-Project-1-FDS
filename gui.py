import tkinter as tk
from tkinter import ttk, messagebox

from app import db


# =========================================================
# BASIC WINDOW HELPERS
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

        width = 120
        if widths:
            width = widths[i]

        tree.column(
            column,
            width=width,
            anchor="center"
        )

    scrollbar = ttk.Scrollbar(
        parent,
        orient="vertical",
        command=tree.yview
    )

    tree.configure(
        yscrollcommand=scrollbar.set
    )

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
        command=open_queries,
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

    create_title(
        f"{role} Login"
    )

    form = ttk.Frame(root)
    form.pack(pady=10)

    ttk.Label(
        form,
        text="Username"
    ).grid(
        row=0,
        column=0,
        padx=10,
        pady=10,
        sticky="e"
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
        pady=10,
        sticky="e"
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
                (
                    username,
                    password,
                    role
                )
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

            elif role == "Viewer":
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
    ).pack(pady=5)


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
# SHIPPER - LIST SHIPMENTS
# =========================================================

def show_shipper_shipments(account_id, display_name):
    clear_root()

    create_title(
        "My Shipments"
    )

    frame = ttk.Frame(root)
    frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    columns = (
        "id",
        "origin",
        "destination",
        "weight",
        "promised",
        "status",
        "outcome",
        "departure"
    )

    headings = (
        "ID",
        "Origin",
        "Destination",
        "Weight",
        "Promised",
        "Status",
        "Outcome",
        "Departure"
    )

    widths = (
        50,
        70,
        90,
        80,
        100,
        120,
        90,
        80
    )

    tree = create_tree(
        frame,
        columns,
        headings,
        widths
    )

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

        for row in rows:
            tree.insert(
                "",
                "end",
                values=row
            )

    except Exception as e:
        messagebox.showerror(
            "Database Error",
            str(e)
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
# SHIPPER - CREATE
# =========================================================

def show_create_shipment(account_id, display_name):
    clear_root()

    create_title(
        "Create Shipment"
    )

    form = ttk.Frame(root)
    form.pack(pady=15)

    try:
        _, hub_rows = db.query(
            """
            SELECT hub_id
            FROM hub
            ORDER BY hub_id
            """
        )

        hubs = [
            row[0]
            for row in hub_rows
        ]

    except Exception as e:
        messagebox.showerror(
            "Database Error",
            str(e)
        )
        return

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
        state="readonly",
        width=25
    )
    origin_box.grid(
        row=0,
        column=1,
        padx=10,
        pady=10
    )

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
        state="readonly",
        width=25
    )
    destination_box.grid(
        row=1,
        column=1,
        padx=10,
        pady=10
    )

    ttk.Label(
        form,
        text="Weight (kg)"
    ).grid(
        row=2,
        column=0,
        padx=10,
        pady=10
    )

    weight_entry = ttk.Entry(
        form,
        width=28
    )
    weight_entry.grid(
        row=2,
        column=1,
        padx=10,
        pady=10
    )

    ttk.Label(
        form,
        text="Promised Date"
    ).grid(
        row=3,
        column=0,
        padx=10,
        pady=10
    )

    date_entry = ttk.Entry(
        form,
        width=28
    )
    date_entry.grid(
        row=3,
        column=1,
        padx=10,
        pady=10
    )

    ttk.Label(
        form,
        text="YYYY-MM-DD"
    ).grid(
        row=4,
        column=1
    )

    def create():
        origin = origin_box.get()
        destination = destination_box.get()
        weight = weight_entry.get().strip()
        promised = date_entry.get().strip()

        if (
            not origin
            or not destination
            or not weight
            or not promised
        ):
            messagebox.showwarning(
                "Missing Information",
                "Fill out every field."
            )
            return

        if origin == destination:
            messagebox.showerror(
                "Invalid Shipment",
                "Origin and destination must be different."
            )
            return

        try:
            weight_num = float(weight)

            if weight_num <= 0:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Invalid Weight",
                "Weight must be greater than 0."
            )
            return

        try:
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
                    weight_num,
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

    create_title(
        "Update Shipment"
    )

    try:
        _, rows = db.query(
            """
            SELECT shipment_id
            FROM shipment
            WHERE shipper_id = %s
              AND NOT EXISTS (
                  SELECT 1
                  FROM booking b
                  WHERE b.shipment_id = shipment.shipment_id
              )
            ORDER BY shipment_id
            """,
            (account_id,)
        )

        shipment_ids = [
            str(row[0])
            for row in rows
        ]

        _, hub_rows = db.query(
            """
            SELECT hub_id
            FROM hub
            ORDER BY hub_id
            """
        )

        hubs = [
            row[0]
            for row in hub_rows
        ]

    except Exception as e:
        messagebox.showerror(
            "Database Error",
            str(e)
        )
        return

    if not shipment_ids:
        messagebox.showinfo(
            "No Shipments",
            "You do not have any unbooked shipments to update."
        )

        show_shipper_dashboard(
            account_id,
            display_name
        )
        return

    form = ttk.Frame(root)
    form.pack(pady=15)

    ttk.Label(
        form,
        text="Shipment ID"
    ).grid(
        row=0,
        column=0,
        padx=10,
        pady=10
    )

    shipment_box = ttk.Combobox(
        form,
        values=shipment_ids,
        state="readonly",
        width=25
    )
    shipment_box.grid(
        row=0,
        column=1,
        padx=10,
        pady=10
    )

    ttk.Label(
        form,
        text="Origin Hub"
    ).grid(
        row=1,
        column=0,
        padx=10,
        pady=10
    )

    origin_box = ttk.Combobox(
        form,
        values=hubs,
        state="readonly",
        width=25
    )
    origin_box.grid(
        row=1,
        column=1,
        padx=10,
        pady=10
    )

    ttk.Label(
        form,
        text="Destination Hub"
    ).grid(
        row=2,
        column=0,
        padx=10,
        pady=10
    )

    destination_box = ttk.Combobox(
        form,
        values=hubs,
        state="readonly",
        width=25
    )
    destination_box.grid(
        row=2,
        column=1,
        padx=10,
        pady=10
    )

    ttk.Label(
        form,
        text="Weight (kg)"
    ).grid(
        row=3,
        column=0,
        padx=10,
        pady=10
    )

    weight_entry = ttk.Entry(
        form,
        width=28
    )
    weight_entry.grid(
        row=3,
        column=1,
        padx=10,
        pady=10
    )

    ttk.Label(
        form,
        text="Promised Date"
    ).grid(
        row=4,
        column=0,
        padx=10,
        pady=10
    )

    date_entry = ttk.Entry(
        form,
        width=28
    )
    date_entry.grid(
        row=4,
        column=1,
        padx=10,
        pady=10
    )

    def load_shipment(event=None):
        sid = shipment_box.get()

        if not sid:
            return

        try:
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
                (
                    sid,
                    account_id
                )
            )

            if data:
                row = data[0]

                origin_box.set(row[0])
                destination_box.set(row[1])

                weight_entry.delete(
                    0,
                    tk.END
                )
                weight_entry.insert(
                    0,
                    row[2]
                )

                date_entry.delete(
                    0,
                    tk.END
                )
                date_entry.insert(
                    0,
                    row[3]
                )

        except Exception as e:
            messagebox.showerror(
                "Database Error",
                str(e)
            )

    shipment_box.bind(
        "<<ComboboxSelected>>",
        load_shipment
    )

    def update():
        sid = shipment_box.get()
        origin = origin_box.get()
        destination = destination_box.get()
        weight = weight_entry.get().strip()
        promised = date_entry.get().strip()

        if not sid:
            messagebox.showwarning(
                "Select Shipment",
                "Choose a shipment first."
            )
            return

        if origin == destination:
            messagebox.showerror(
                "Invalid Shipment",
                "Origin and destination must differ."
            )
            return

        try:
            weight_num = float(weight)

            if weight_num <= 0:
                raise ValueError

        except ValueError:
            messagebox.showerror(
                "Invalid Weight",
                "Weight must be greater than 0."
            )
            return

        try:
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
                    weight_num,
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
                "Database Error",
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

    create_title(
        "Book Shipment"
    )

    try:
        _, rows = db.query(
            """
            SELECT shipment_id
            FROM shipment s
            WHERE s.shipper_id = %s
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

    except Exception as e:
        messagebox.showerror(
            "Database Error",
            str(e)
        )
        return

    if not shipment_ids:
        messagebox.showinfo(
            "No Shipments",
            "You do not have any unbooked shipments."
        )

        show_shipper_dashboard(
            account_id,
            display_name
        )
        return

    ttk.Label(
        root,
        text="Select Shipment"
    ).pack(pady=(10, 5))

    shipment_box = ttk.Combobox(
        root,
        values=shipment_ids,
        state="readonly",
        width=25
    )
    shipment_box.pack(pady=5)

    departures_frame = ttk.Frame(root)
    departures_frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=15
    )

    columns = (
        "id",
        "origin",
        "destination",
        "datetime",
        "remaining"
    )

    headings = (
        "Departure",
        "Origin",
        "Destination",
        "Date/Time",
        "Remaining kg"
    )

    tree = create_tree(
        departures_frame,
        columns,
        headings,
        (
            80,
            70,
            90,
            150,
            100
        )
    )

    def load_departures(event=None):
        for item in tree.get_children():
            tree.delete(item)

        sid = shipment_box.get()

        if not sid:
            return

        try:
            _, shipment_data = db.query(
                """
                SELECT
                    origin_hub_id,
                    destination_hub_id,
                    weight_kg
                FROM shipment
                WHERE shipment_id = %s
                  AND shipper_id = %s
                """,
                (
                    sid,
                    account_id
                )
            )

            if not shipment_data:
                return

            origin, destination, weight = shipment_data[0]

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
                (
                    origin,
                    destination,
                    weight
                )
            )

            for row in departures:
                tree.insert(
                    "",
                    "end",
                    values=row
                )

        except Exception as e:
            messagebox.showerror(
                "Database Error",
                str(e)
            )

    shipment_box.bind(
        "<<ComboboxSelected>>",
        load_departures
    )

    def book():
        sid = shipment_box.get()

        selected = tree.selection()

        if not sid:
            messagebox.showwarning(
                "Select Shipment",
                "Choose a shipment."
            )
            return

        if not selected:
            messagebox.showwarning(
                "Select Departure",
                "Choose a departure from the table."
            )
            return

        departure_id = tree.item(
            selected[0]
        )["values"][0]

        try:
            db.call_proc(
                "book_shipment",
                (
                    int(sid),
                    int(departure_id)
                )
            )

            messagebox.showinfo(
                "Booked",
                f"Shipment {sid} was booked onto departure {departure_id}."
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

    create_title(
        "Track Shipment"
    )

    try:
        _, rows = db.query(
            """
            SELECT shipment_id
            FROM shipment
            WHERE shipper_id = %s
            ORDER BY shipment_id
            """,
            (account_id,)
        )

        shipment_ids = [
            str(row[0])
            for row in rows
        ]

    except Exception as e:
        messagebox.showerror(
            "Database Error",
            str(e)
        )
        return

    ttk.Label(
        root,
        text="Shipment ID"
    ).pack(pady=(5, 5))

    shipment_box = ttk.Combobox(
        root,
        values=shipment_ids,
        state="readonly",
        width=25
    )
    shipment_box.pack(pady=5)

    info_label = ttk.Label(
        root,
        text="",
        justify="left"
    )
    info_label.pack(
        pady=15
    )

    history_frame = ttk.Frame(root)
    history_frame.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    columns = (
        "seq",
        "time",
        "hub",
        "status"
    )

    headings = (
        "Seq",
        "Timestamp",
        "Hub",
        "Status"
    )

    tree = create_tree(
        history_frame,
        columns,
        headings,
        (
            50,
            160,
            70,
            130
        )
    )

    def track():
        sid = shipment_box.get()

        if not sid:
            messagebox.showwarning(
                "Select Shipment",
                "Choose a shipment."
            )
            return

        try:
            _, shipment = db.query(
                """
                SELECT
                    shipment_id,
                    origin_hub_id,
                    destination_hub_id,
                    weight_kg,
                    promised_delivery_date,
                    COALESCE(
                        current_status,
                        'NO SCANS YET'
                    ),
                    COALESCE(
                        delivery_outcome,
                        '-'
                    )
                FROM shipment
                WHERE shipment_id = %s
                  AND shipper_id = %s
                """,
                (
                    sid,
                    account_id
                )
            )

            if not shipment:
                return

            row = shipment[0]

            info_label.config(
                text=(
                    f"Shipment: {row[0]}\n"
                    f"Route: {row[1]} → {row[2]}\n"
                    f"Weight: {row[3]} kg\n"
                    f"Promised: {row[4]}\n"
                    f"Current Status: {row[5]}\n"
                    f"Outcome: {row[6]}"
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

        except Exception as e:
            messagebox.showerror(
                "Database Error",
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

    create_title(
        "Shipper Reports"
    )

    try:
        _, summary = db.query(
            """
            SELECT
                COUNT(*) AS delivered,
                COALESCE(
                    SUM(
                        delivery_outcome = 'ON_TIME'
                    ),
                    0
                ) AS on_time,
                COALESCE(
                    SUM(
                        delivery_outcome = 'LATE'
                    ),
                    0
                ) AS late
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

        ttk.Label(
            root,
            text="Shipments Currently In Transit",
            font=("Arial", 12)
        ).pack(pady=10)

        frame = ttk.Frame(root)
        frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        columns = (
            "id",
            "origin",
            "destination",
            "status",
            "promised"
        )

        headings = (
            "ID",
            "Origin",
            "Destination",
            "Status",
            "Promised"
        )

        tree = create_tree(
            frame,
            columns,
            headings,
            (
                50,
                70,
                90,
                130,
                100
            )
        )

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

        for row in rows:
            tree.insert(
                "",
                "end",
                values=row
            )

    except Exception as e:
        messagebox.showerror(
            "Database Error",
            str(e)
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
# PLACEHOLDERS FOR NEXT BIG CHUNK
# =========================================================

def show_carrier_dashboard(account_id, display_name):
    clear_root()

    create_title(
        f"Welcome, {display_name}",
        "Carrier Dashboard"
    )

    ttk.Label(
        root,
        text="Carrier GUI will be added next."
    ).pack(pady=25)

    ttk.Button(
        root,
        text="Logout",
        command=show_home,
        width=25
    ).pack(pady=20)


def show_viewer_dashboard(account_id, display_name):
    clear_root()

    create_title(
        f"Welcome, {display_name}",
        "Viewer Dashboard"
    )

    ttk.Label(
        root,
        text="Viewer GUI will be added next."
    ).pack(pady=25)

    ttk.Button(
        root,
        text="Logout",
        command=show_home,
        width=25
    ).pack(pady=20)


def open_queries():
    messagebox.showinfo(
        "View Queries",
        "The six analytical queries will be added in the next GUI update."
    )


# =========================================================
# START APPLICATION
# =========================================================

root = tk.Tk()

root.title(
    "Freight Tracking and Delivery Management"
)

root.geometry(
    "900x650"
)

root.minsize(
    800,
    600
)

show_home()

root.mainloop()
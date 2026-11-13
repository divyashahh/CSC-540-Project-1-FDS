import tkinter as tk
from tkinter import ttk


def open_shipper():
    login_window = tk.Toplevel(root)
    login_window.title("Shipper Login")
    login_window.geometry("400x300")
    login_window.resizable(False, False)

    title = ttk.Label(
        login_window,
        text="Shipper Login",
        font=("Arial", 16, "bold")
    )
    title.pack(pady=25)

    username_label = ttk.Label(
        login_window,
        text="Username"
    )
    username_label.pack()

    username_entry = ttk.Entry(
        login_window,
        width=30
    )
    username_entry.pack(pady=5)

    password_label = ttk.Label(
        login_window,
        text="Password"
    )
    password_label.pack(pady=(10, 0))

    password_entry = ttk.Entry(
        login_window,
        width=30,
        show="*"
    )
    password_entry.pack(pady=5)

    login_button = ttk.Button(
        login_window,
        text="Login"
    )
    login_button.pack(pady=20)

    back_button = ttk.Button(
        login_window,
        text="Back",
        command=login_window.destroy
    )
    back_button.pack()


def open_carrier():
    print("Carrier clicked")


def open_viewer():
    print("Viewer clicked")


def open_queries():
    print("View Queries clicked")


root = tk.Tk()

root.title("Freight Tracking and Delivery Management")

root.geometry("600x450")

root.resizable(False, False)


title = ttk.Label(
    root,
    text="Freight Tracking and Delivery Management",
    font=("Arial", 18, "bold")
)
title.pack(pady=40)


subtitle = ttk.Label(
    root,
    text="Select a role",
    font=("Arial", 12)
)
subtitle.pack(pady=10)


shipper_button = ttk.Button(
    root,
    text="Shipper",
    command=open_shipper,
    width=30
)
shipper_button.pack(pady=10)


carrier_button = ttk.Button(
    root,
    text="Carrier",
    command=open_carrier,
    width=30
)
carrier_button.pack(pady=10)


viewer_button = ttk.Button(
    root,
    text="Viewer",
    command=open_viewer,
    width=30
)
viewer_button.pack(pady=10)


queries_button = ttk.Button(
    root,
    text="View Queries",
    command=open_queries,
    width=30
)
queries_button.pack(pady=10)


exit_button = ttk.Button(
    root,
    text="Exit",
    command=root.destroy,
    width=30
)
exit_button.pack(pady=25)


root.mainloop()
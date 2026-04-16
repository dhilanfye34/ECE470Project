from tkinter import ttk


def apply_theme(app):
    app.app_name = "The Hurricane Grill"

    app.bg_color = "#f8f5f0"
    app.card_color = "#fffdf9"
    app.green = "#0b6b4b"
    app.orange = "#f47c20"
    app.cream = "#f3e6d0"
    app.button_dark = "#222222"
    app.text_dark = "#222222"
    app.text_muted = "#6b6b6b"
    app.border_color = "#ddd6c8"
    app.soft_green = "#e7f4ee"

    app.root.configure(bg=app.bg_color)


def setup_table_style(app):
    style = ttk.Style()
    style.theme_use("default")

    style.configure(
        "Treeview",
        background="white",
        foreground=app.text_dark,
        rowheight=30,
        fieldbackground="white",
        borderwidth=0,
        font=("Arial", 10)
    )

    style.configure(
        "Treeview.Heading",
        background=app.green,
        foreground="white",
        font=("Arial", 11, "bold"),
        relief="flat"
    )

    style.map("Treeview.Heading", background=[("active", app.green)])
    style.map(
        "Treeview",
        background=[("selected", app.soft_green)],
        foreground=[("selected", app.text_dark)]
    )

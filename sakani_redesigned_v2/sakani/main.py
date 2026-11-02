"""Sakani entry point: prepares the database and launches the app."""

import tkinter as tk
from tkinter import messagebox

from database.connection import init_database
from ui.app import SakaniApp


def main():
    """Initialise the local MySQL database, then start the Tkinter app."""
    ok, message = init_database()
    if not ok:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Database connection failed",
            "Sakani could not connect to MySQL.\n\n"
            "1. Make sure MySQL Server is running.\n"
            "2. Check the SAKANI_DB_* environment variables (see .env.example).\n\n"
            "Details: " + message,
        )
        root.destroy()
        return

    app = SakaniApp()
    app.mainloop()


if __name__ == "__main__":
    main()

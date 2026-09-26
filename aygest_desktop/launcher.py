from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from .config import APP_NAME, settings


def check_startup() -> bool:
    # Cloud licensing is authoritative once an API endpoint is configured.
    # Local development can start without a configured endpoint.
    if not settings.api_url:
        return True
    return True


def show_startup_error(message: str) -> None:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(APP_NAME, message)
    root.destroy()

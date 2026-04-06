from datetime import datetime
import ctypes
from ctypes import wintypes
import tkinter as tk

import pytz

# -----------------------------
# User-configurable settings
# -----------------------------
TIMEZONE_NAME = "Asia/Shanghai"
TIME_FORMAT = "%m/%d %a %H:%M"

# Distance from bottom-right corner of the usable desktop (outside taskbar).
MARGIN_X = 6
MARGIN_Y = 6

# Internal padding around the text inside the mini window.
PADDING_X = 6
PADDING_Y = 4

# Simple theme values used across widgets.
BG_COLOR = "#1b1b1b"
FG_COLOR = "#ffffff"
CITY_FONT = ("Segoe UI", 11, "bold")
TIME_FONT = ("Segoe UI", 11)


def get_city_name(timezone_name):
    """Convert timezone string into a readable city label."""
    return timezone_name.split("/")[-1].replace("_", " ")


def get_work_area():
    """Return the desktop work area rectangle, excluding taskbar space."""
    rect = wintypes.RECT()
    spi_get_work_area = 48
    ctypes.windll.user32.SystemParametersInfoW(spi_get_work_area, 0, ctypes.byref(rect), 0)
    return rect


def position_window(root):
    """Pin the window near the taskbar clock using measured content size."""
    root.update_idletasks()
    width = root.winfo_reqwidth()
    height = root.winfo_reqheight()

    work_area = get_work_area()
    x = work_area.right - width - MARGIN_X
    y = work_area.bottom - height - MARGIN_Y
    root.geometry(f"+{x}+{y}")


def build_clock_ui(root):
    """Create labels and return references needed by the update loop."""
    content = tk.Frame(root, bg=BG_COLOR)
    content.pack(padx=PADDING_X, pady=PADDING_Y)

    city_label = tk.Label(
        content,
        font=CITY_FONT,
        fg=FG_COLOR,
        bg=BG_COLOR,
        anchor="e",
    )
    city_label.pack(side="left", padx=(0, 4))

    time_label = tk.Label(
        content,
        font=TIME_FONT,
        fg=FG_COLOR,
        bg=BG_COLOR,
        anchor="w",
    )
    time_label.pack(side="left")
    return city_label, time_label


def setup_exit_actions(root):
    """Add right-click menu and keyboard shortcut to close the app."""
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="Quit", command=root.destroy)

    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    root.bind("<Button-3>", show_menu)
    root.bind("<Escape>", lambda _event: root.destroy())


def main():
    """Start the always-on-top world clock window."""
    tz = pytz.timezone(TIMEZONE_NAME)
    city_name = get_city_name(TIMEZONE_NAME)

    # Create a borderless mini window that floats above other windows.
    root = tk.Tk()
    root.title("World Clock")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg=BG_COLOR)

    city_label, time_label = build_clock_ui(root)
    setup_exit_actions(root)

    def refresh_time():
        """Update text every second and keep the window pinned in place."""
        now = datetime.now(tz).strftime(TIME_FORMAT)
        city_label.config(text=city_name)
        time_label.config(text=now)
        position_window(root)
        root.after(1000, refresh_time)

    refresh_time()
    root.mainloop()


if __name__ == "__main__":
    main()
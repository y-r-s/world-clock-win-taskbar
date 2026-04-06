from datetime import datetime, timezone
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

# -----------------------------
# User-configurable settings
# -----------------------------
TIMEZONE_NAME = "Asia/Shanghai"
TIME_FORMAT = "%m/%d %a %H:%M"
APP_DIR_NAME = "WorldClock"
CONFIG_FILE_NAME = "config.json"
ALL_TIMEZONES = available_timezones()
TIMEZONE_CHOICES = sorted(
    tz_name for tz_name in ALL_TIMEZONES if "/" in tz_name and not tz_name.startswith("Etc/")
)

# Distance from bottom-right corner of the usable desktop (outside taskbar).
MARGIN_X = 6
MARGIN_Y = 6

# Internal padding around the text inside the mini window.
PADDING_X = 6
PADDING_Y = 4

# Simple theme values used across widgets.
BG_COLOR = "#1b1b1b"
FG_COLOR = "#ffffff"
HEADER_BG = "#2a2a2a"
HEADER_HOVER_BG = "#3a3a3a"
CITY_FONT = ("Segoe UI", 11, "bold")
TIME_FONT = ("Segoe UI", 11)


def get_city_name(timezone_name):
    """Convert timezone string into a readable city label."""
    return timezone_name.split("/")[-1].replace("_", " ")


def get_config_path():
    """Store settings in AppData so they persist across app updates."""
    appdata_value = os.environ.get("APPDATA")
    appdata_dir = Path(appdata_value) if appdata_value else Path.home()

    config_dir = appdata_dir / APP_DIR_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / CONFIG_FILE_NAME


def load_settings():
    """Read saved user settings, or fall back to defaults."""
    default_settings = {
        "timezone": TIMEZONE_NAME,
        "city": get_city_name(TIMEZONE_NAME),
    }
    config_path = get_config_path()
    if not config_path.exists():
        return default_settings

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default_settings

    timezone_name = data.get("timezone", TIMEZONE_NAME)
    if timezone_name not in ALL_TIMEZONES:
        timezone_name = TIMEZONE_NAME

    city_name = data.get("city", get_city_name(timezone_name)).strip()
    if not city_name:
        city_name = get_city_name(timezone_name)

    return {"timezone": timezone_name, "city": city_name}


def save_settings(timezone_name, city_name):
    """Persist selected timezone/city for the next launch."""
    config_path = get_config_path()
    payload = {"timezone": timezone_name, "city": city_name}
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_timezone(timezone_name):
    """Return a timezone object, with robust fallback."""
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        try:
            return ZoneInfo("UTC")
        except ZoneInfoNotFoundError:
            return timezone.utc


def apply_timezone_state(state, timezone_name, city_name=None):
    """Update timezone/city state in one place to avoid duplicated logic."""
    city = city_name or get_city_name(timezone_name)
    state["timezone"] = timezone_name
    state["city"] = city
    state["tz"] = build_timezone(timezone_name)


def place_popup_near_clock(clock_root, popup):
    """Spawn popup near clock widget (prefer above it, keep on screen)."""
    clock_root.update_idletasks()
    popup.update_idletasks()

    popup_width = popup.winfo_reqwidth()
    popup_height = popup.winfo_reqheight()
    clock_x = clock_root.winfo_x()
    clock_y = clock_root.winfo_y()
    clock_width = clock_root.winfo_width()
    clock_height = clock_root.winfo_height()

    x = clock_x + clock_width - popup_width
    y = clock_y - popup_height - 8

    work_area = get_work_area()
    x = max(work_area.left + 8, min(x, work_area.right - popup_width - 8))
    if y < work_area.top + 8:
        y = clock_y + clock_height + 8
    y = min(y, work_area.bottom - popup_height - 8)

    popup.geometry(f"+{x}+{y}")


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


def setup_menu_actions(root, open_settings):
    """Add right-click menu for settings and app exit."""
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="Settings", command=open_settings)
    menu.add_separator()
    menu.add_command(label="Quit", command=root.destroy)

    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    root.bind("<Button-3>", show_menu)
    root.bind("<Escape>", lambda _event: root.destroy())


def main():
    """Start the always-on-top world clock window."""
    state = load_settings()
    apply_timezone_state(state, state["timezone"], state["city"])

    # Create a borderless mini window that floats above other windows.
    root = tk.Tk()
    root.title("World Clock")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg=BG_COLOR)

    city_label, time_label = build_clock_ui(root)

    def open_settings():
        """Open a small settings window to choose timezone and city label."""
        settings_window = tk.Toplevel(root)
        settings_window.title("Clock Settings")
        settings_window.overrideredirect(True)
        settings_window.resizable(False, False)
        settings_window.configure(bg=BG_COLOR)
        settings_window.transient(root)
        settings_window.attributes("-topmost", True)
        settings_window.grab_set()
        settings_window.lift()

        header = tk.Frame(settings_window, bg=HEADER_BG, padx=8, pady=4)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Clock Settings",
            fg=FG_COLOR,
            bg=HEADER_BG,
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")
        tk.Button(
            header,
            text="X",
            command=settings_window.destroy,
            fg=FG_COLOR,
            bg=HEADER_BG,
            activeforeground=FG_COLOR,
            activebackground=HEADER_HOVER_BG,
            bd=0,
            padx=8,
            pady=1,
        ).pack(side="right")

        frame = tk.Frame(settings_window, bg=BG_COLOR, padx=12, pady=10)
        frame.pack(fill="both", expand=True)

        timezone_var = tk.StringVar(value=state["timezone"])
        city_var = tk.StringVar(value=state["city"])

        tk.Label(frame, text="Timezone", fg=FG_COLOR, bg=BG_COLOR).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        timezone_combo = ttk.Combobox(
            frame,
            textvariable=timezone_var,
            values=TIMEZONE_CHOICES,
            state="readonly",
            width=34,
        )
        timezone_combo.grid(row=1, column=0, sticky="ew")

        tk.Label(frame, text="City label", fg=FG_COLOR, bg=BG_COLOR).grid(
            row=2, column=0, sticky="w", pady=(10, 4)
        )
        city_entry = tk.Entry(frame, textvariable=city_var, width=36)
        city_entry.grid(row=3, column=0, sticky="ew")

        def use_timezone_city():
            city_var.set(get_city_name(timezone_var.get()))

        def save_and_close():
            timezone_name = timezone_var.get().strip()
            if timezone_name not in ALL_TIMEZONES:
                messagebox.showerror("Invalid timezone", "Please select a valid timezone.")
                return

            city_name = city_var.get().strip() or get_city_name(timezone_name)
            apply_timezone_state(state, timezone_name, city_name)

            try:
                save_settings(timezone_name, city_name)
            except OSError:
                messagebox.showwarning("Save failed", "Could not save settings to disk.")

            settings_window.destroy()

        buttons = tk.Frame(frame, bg=BG_COLOR)
        buttons.grid(row=4, column=0, sticky="e", pady=(12, 0))

        tk.Button(buttons, text="Use timezone city", command=use_timezone_city).pack(
            side="left", padx=(0, 6)
        )
        tk.Button(buttons, text="Save", command=save_and_close).pack(side="left")

        place_popup_near_clock(root, settings_window)
        settings_window.lift()
        settings_window.focus_force()
        settings_window.after(50, lambda: settings_window.lift())
        settings_window.bind("<Escape>", lambda _event: settings_window.destroy())
        city_entry.focus_set()

    setup_menu_actions(root, open_settings)

    def refresh_time():
        """Update text every second and keep the window pinned in place."""
        now = datetime.now(state["tz"]).strftime(TIME_FORMAT)
        city_label.config(text=state["city"])
        time_label.config(text=now)
        position_window(root)
        root.after(1000, refresh_time)

    refresh_time()
    root.mainloop()


if __name__ == "__main__":
    main()
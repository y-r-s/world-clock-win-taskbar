# World Clock (Windows taskbar area)

Tiny always-on-top clock window for Windows that stays near the taskbar clock and shows another timezone.

Timezone handling uses Python `zoneinfo` with `tzdata` for reliable IANA timezone data on Windows.

## Features

- Shows city + date + time (example: `Shanghai Tue 04-07 09:30`)
- Auto-pins near the bottom-right corner by the Windows clock
- Borderless mini UI
- Right-click menu with `Quit`
- `Esc` key to exit

## Local run (developer)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Configure timezone

Edit `TIMEZONE_NAME` in `main.py`:

```python
TIMEZONE_NAME = "Asia/Shanghai"
```

Use any valid IANA timezone (for example `Europe/London`, `America/New_York`, `Asia/Tokyo`).
Users can also change timezone and city label at runtime from the right-click `Settings` menu.

## Run without terminal window

```powershell
.\.venv\Scripts\pythonw.exe .\main.py
```

## Build a single `.exe`

```powershell
.\.venv\Scripts\Activate.ps1
pip install pyinstaller
.\scripts\build-exe.ps1
```

Build output:

- `dist\WorldClock.exe`
- Build includes `tzdata`, so end users do not need to install timezone packages.

## Auto-start on Windows login

Use Task Scheduler:

- Trigger: `At log on`
- Program/script: path to `pythonw.exe` (or `WorldClock.exe`)
- Arguments: path to `main.py` (if using Python)
- Start in: project directory

## Public release flow

1. Tag a version:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

2. GitHub Actions workflow builds the app and uploads:
   - `WorldClock-vX.Y.Z-windows.zip`
   - `WorldClock.exe`

3. Publish a GitHub Release from that tag and attach artifacts (or let `gh` do it).

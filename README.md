# TimeSheet Automation

Automated timesheet filling for PeopleHub using Playwright with session persistence and per-day time configuration.

## Features

- ✅ **Session Persistence**: Login once, reuse authentication across runs
- ✅ **Per-Day Configuration**: Customize working hours for each weekday individually
- ✅ **Any Week**: Fill this week, a previous week, or any week by date
- ✅ **Smart Holiday Detection**: Automatically skips public holidays and approved absences
- ✅ **Half-Day Support**: Handles morning-only or afternoon-only time entries
- ✅ **Custom Angular Components**: Works with PeopleHub's custom time-input elements
- ✅ **Auto-Save Integration**: Waits for timesheet auto-save after completion
- ✅ **VS Code Integration**: Launch configurations and task runner support
- ✅ **Visible Browser Mode**: Monitor the automation in real-time

## Quick Start

### Prerequisites

- Python 3.11+
- uv (Python package manager)

### Setup

```bash
# Install dependencies
uv sync

# Install Playwright browser
uv run playwright install chromium

# Run the automation
uv run python main.py
```

### First Run

1. Browser opens and waits 60 seconds for manual login
2. Log in to peoplehub.{company}.com
3. Session automatically saves to `playwright/.auth/state.json`
4. Automation proceeds and fills timesheet

### Subsequent Runs

- Fully automated using saved session
- No manual login required
- Browser closes automatically after completion

## Choosing the Week

By default the script fills the week opened by PeopleHub's **"Current"** button, which is the **oldest timesheet that is not yet submitted or locked** (not necessarily this calendar week). If you skipped a few weeks, run it, submit, and run it again to work through them in order.

To fill a specific week instead:

```bash
# Default: the oldest unsubmitted week
uv run python main.py

# Calendar week before this one (2 = two weeks ago, etc.)
uv run python main.py --weeks-back 1

# The week containing a given date (any day of the week works)
uv run python main.py --week 2026-09-14

# Check that a week can be reached and edited, without filling anything
uv run python main.py --week 2026-09-14 --dry-run
```

`--week` and `--weeks-back` cannot be combined.

### Safety Checks

The script never fills a week other than the one requested and never prompts for manual action, so it is safe to run unattended (e.g. by an AI agent or a scheduler):

- **Verified navigation**: when a specific week is requested, the script reads the week label after clicking "Current" (which may be many weeks before the requested one), then steps with the ◄ / ► arrows in either direction (up to 104 weeks), checking after each click that the label moved exactly one week. The displayed week is always logged.
- **Locked weeks**: Submitted or approved timesheets cannot be edited. The script stops before touching them.

When a check fails, the script logs the reason and exits with code `1` without filling anything.

## Configuration

Edit `.env` to customize time entries per day:

```env
# Base URL
TIMESHEET_URL=https://peoplehub.contoso.com

# Per-day time entries (HH:MM format)
MONDAY_START_TIME_1=08:30
MONDAY_END_TIME_1=14:00
MONDAY_START_TIME_2=14:45
MONDAY_END_TIME_2=17:00

# Customize individual days
FRIDAY_START_TIME_1=09:00
FRIDAY_END_TIME_1=13:00
FRIDAY_START_TIME_2=14:00
FRIDAY_END_TIME_2=16:00

# Debug logging (optional)
LOG_LEVEL=DEBUG
```

**Default**: All weekdays use 08:30-14:00 and 14:45-17:00 unless customized.

### Special Days & Half-Days

Configure CSS indicators and half-day blocks via `.env` if your tenant uses different classes or times:

```env
# Special day indicators (CSS classes)
SPECIAL_DAY_INDICATOR_HOLIDAY=wx-timesheet-day__indicator-holiday
SPECIAL_DAY_INDICATOR_VACATION_APPROVED=wx-timesheet-day__indicator-vacation-approved
SPECIAL_DAY_INDICATOR_ABSENCE_APPROVED=wx-timesheet-day__indicator-absence-approved

# Half-day defaults
MORNING_ONLY_START_TIME_1=08:30
MORNING_ONLY_END_TIME_1=12:30
AFTERNOON_ONLY_START_TIME_1=13:00
AFTERNOON_ONLY_END_TIME_1=17:00
```

If unset, the defaults shown above are used (defined in `config.py`).

## How It Works

### Automation Flow

1. Loads saved browser session (or prompts for manual login)
2. Navigates to timesheet page
3. Clicks "Current" button, navigates to the requested week (if any) and checks it is editable
4. For each weekday (Monday-Friday):
   - Checks for holidays/absences (skips if detected)
   - Expands day dropdown
   - Fills first time block with configured times
   - Adds second time block using '+' button
   - Fills second time block
   - Collapses dropdown
5. Waits 10 seconds for auto-save
6. Displays clickable review URL in the terminal
7. Closes browser

## VS Code Integration

### Launch Configurations (Press F5)

- **Run Timesheet Automation**: Normal execution
- **Run Timesheet Automation (Debug)**: With DEBUG logging

### Tasks (Ctrl+Shift+P → Tasks: Run Task)

- **Run Timesheet Automation**: Execute the script
- **Clear Saved Session**: Delete authentication state
- **Install Dependencies**: Run `uv sync`
- **Install Playwright Browsers**: Install Chromium

## Project Structure

```text
TimeSheetAutomation/
├── main.py                 # Main automation script
├── auth.py                 # Session persistence
├── config.py               # Configuration loader
├── .env                    # User settings (git-ignored)
├── .env.example            # Settings template
├── .vscode/                # VS Code integration
│   ├── launch.json         # Debug configurations
│   ├── tasks.json          # Task definitions
│   └── settings.json       # Python settings
├── playwright/
│   └── .auth/
│       └── state.json      # Saved session (git-ignored)
├── pyproject.toml          # Dependencies (uv)
└── README.md               # This file
```

## Troubleshooting

### Application Fails to Start on First Run

The application usually fails to start the first time you run it after opening it in VS Code. The reason is unknown, but the workaround is to simply run it again and it will work as expected. It doesn't happen if you use the VS Code task runner.

### Session Expired or Login Required

```bash
# Delete saved session and re-authenticate
rm playwright/.auth/state.json
uv run python main.py
```

### "Current button not found"

- Ensure you're logged in successfully during first run
- Script expects access to timesheet page

### Element Not Found Errors

- Website structure may have changed
- Enable debug logging: `LOG_LEVEL=DEBUG` in `.env`
- Check browser DevTools to verify element selectors

### Modify Time Entries

Edit `.env` to customize times for specific days:

```env
# Make Friday shorter
FRIDAY_START_TIME_1=09:00
FRIDAY_END_TIME_1=13:00
FRIDAY_START_TIME_2=13:45
FRIDAY_END_TIME_2=16:00
```

Changes take effect on next run (no code changes needed).

## Tips

- ✅ Browser runs in visible mode for monitoring
- ✅ Detailed logging to console (set `LOG_LEVEL=DEBUG` for verbose output)
- ✅ Session state automatically updated after each run
- ✅ Terminal URLs are clickable (Ctrl+Click) for review
- ✅ All days default to same times but individually customizable
- ✅ All special-day selectors and half-day defaults are centralized in `config.py`
- ✅ Script handles PeopleHub's auto-save mechanism
- ✅ Skips holidays and approved absences automatically

## Security

- 🔒 Never commit `.env` or `playwright/.auth/` directory
- 🔒 Authentication cookies stored locally in `state.json`
- 🔒 Keep session state secure and private
- 🔒 `.gitignore` configured to exclude sensitive files

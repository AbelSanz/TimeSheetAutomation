# TimeSheet Automation

Automated timesheet filling for PeopleHub using Playwright.

## Description

This Python application automates the process of filling timesheets on peoplehub.languagewire.com. It navigates to the timesheet page, fills in time entries for Monday through Friday with configurable start and end times.

## Features

- **Session Persistence**: Saves browser authentication state to avoid repeated logins
- **Configurable Time Entries**: Easily customize working hours
- **Error Handling**: Robust error handling with detailed logging
- **Visible Browser Mode**: Run with browser UI visible for monitoring

## Prerequisites

- Python 3.11 or higher
- uv (Python package manager)

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd TimeSheetAutomation
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Install Playwright browsers:
   ```bash
   uv run playwright install chromium
   ```

4. Create a `.env` file (optional):
   ```bash
   cp .env.example .env
   ```

## Configuration

Edit `.env` to configure the application. You can set different times for each day:

```env
# Base URL for the timesheet application
TIMESHEET_URL=https://peoplehub.languagewire.com

# Time entries per day (HH:MM format)
# Customize times for each day individually

# Monday
MONDAY_START_TIME_1=08:30
MONDAY_END_TIME_1=14:00
MONDAY_START_TIME_2=14:45
MONDAY_END_TIME_2=17:00

# Tuesday
TUESDAY_START_TIME_1=08:30
TUESDAY_END_TIME_1=14:00
TUESDAY_START_TIME_2=14:45
TUESDAY_END_TIME_2=17:00

# ... and so on for Wednesday, Thursday, Friday
```

**Note**: All days use the same default times (08:30-14:00, 14:45-17:00), but you can customize individual days as needed.

## Usage

Run the automation script:

```bash
uv run python main.py
```

### First Run

On the first run, the browser will open and you'll need to manually:
1. Log in to the timesheet application
2. The script will save your session for future runs

### Subsequent Runs

The script will automatically use your saved session to fill timesheets without requiring login.

## Project Structure

```
TimeSheetAutomation/
├── main.py                 # Main entry point
├── auth.py                 # Authentication and session management
├── config.py               # Configuration and settings
├── playwright/
│   └── .auth/              # Stored authentication state (git-ignored)
│       └── state.json      # Browser session state
├── pyproject.toml          # Project dependencies
├── .env                    # Environment variables (git-ignored)
├── .env.example            # Environment variables template
└── README.md               # This file
```

## How It Works

1. **Authentication**: Checks for saved session state. If not found, opens browser for manual login.
2. **Navigation**: Navigates to the timesheet page.
3. **Automation**: 
   - Clicks the "Current" button to access current week's timesheet
   - For each weekday (Monday-Friday):
     - Fills first time block with configured times for that day
     - Adds second time block using the "+" button
     - Fills second time block with configured times for that day
     - Collapses the dropdown
4. **Auto-Save**: Waits for the timesheet to auto-save after all days are collapsed
5. **Session Saving**: Saves authentication state for future runs.

## Troubleshooting

### Session Expired

If you get authentication errors, delete the session state:

```bash
rm playwright/.auth/state.json
```

Then run the script again to re-authenticate.

### Element Not Found Errors

The website structure may have changed. Check the logs for specific element selector issues.

## Security Notes

- Never commit `.env` or `playwright/.auth/` directory
- The `.auth/` directory contains sensitive authentication cookies
- Keep your authentication state secure

## License

MIT License

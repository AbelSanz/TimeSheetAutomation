# Quick Start Guide

## First Time Setup

1. **Install dependencies** (if not done):
   ```bash
   uv sync
   uv run playwright install chromium
   ```

2. **Configure settings** (optional):
   - Edit `.env` to customize time entries per day
   - Default times for all days: 8:30-14:00, 14:45-17:00
   - Can customize individual days (see below)

3. **Run the automation**:
   ```bash
   uv run python main.py
   ```

## First Run Behavior

- Browser will open (visible, not headless)
- You must **manually log in** to peoplehub.languagewire.com
- Navigate to the timesheet page
- Wait 60 seconds for the script to continue
- Your session will be saved in `playwright/.auth/state.json`

## Subsequent Runs

- Script automatically loads your saved session
- No manual login required
- Navigates directly to timesheet automation

## What the Script Does

1. Opens browser and loads your session
2. Navigates to the timesheet page automatically
3. Clicks the "Current" button
4. For each weekday (Monday-Friday):
   - Expands the day dropdown (checks aria-expanded attribute)
   - Fills first time entry with configured times for that day
   - Clicks '+' to add second entry
   - Fills second time entry with configured times for that day
   - Collapses the day dropdown
5. Waits 10 seconds for auto-save to complete
6. Displays clickable URL for review and submission
7. Saves updated session
8. Closes browser

## Troubleshooting

### "Current button not found"
- Manually navigate to the timesheet page before the script continues
- The script expects you to be on or near the timesheet page

### Session expired
```bash
# Delete saved session and re-login
rm playwright/.auth/state.json
uv run python main.py
```

### Element not found errors
- The website structure may have changed
- Check the selectors in `main.py`
- Use browser DevTools to inspect element structure

### Modify time entries
Edit `.env` to customize times for each day:
```env
# Customize times for individual days
MONDAY_START_TIME_1=08:30
MONDAY_END_TIME_1=14:00
MONDAY_START_TIME_2=14:45
MONDAY_END_TIME_2=17:00

# Different times for Friday
FRIDAY_START_TIME_1=09:00
FRIDAY_END_TIME_1=13:00
FRIDAY_START_TIME_2=14:00
FRIDAY_END_TIME_2=16:00

# ... and so on for other days
```

## File Structure

```
TimeSheetAutomation/
├── main.py           # Main automation script
├── auth.py           # Session management
├── config.py         # Configuration loader
├── .env              # Your settings (git-ignored)
├── .env.example      # Template settings
├── .vscode/          # VS Code integration
│   ├── launch.json   # Debug configurations
│   ├── tasks.json    # Task runner configurations
│   └── settings.json # Python settings
├── playwright/
│   └── .auth/
│       └── state.json  # Saved session (git-ignored)
└── README.md         # Full documentation
```

## Tips

- Keep the browser window visible during first run
- The script logs detailed information to console
- Use `LOG_LEVEL=DEBUG` in `.env` for verbose output
- Session state is automatically updated after each run
- **VS Code users**: Press `F5` to run with debugger
- **VS Code users**: Use Command Palette → "Tasks: Run Task" for quick actions
- The URL displayed at the end is clickable (Ctrl+Click in terminal)
- All days default to same times but can be customized individually

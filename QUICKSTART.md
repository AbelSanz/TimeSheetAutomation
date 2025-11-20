# Quick Start Guide

## First Time Setup

1. **Install dependencies** (if not done):
   ```bash
   uv sync
   uv run playwright install chromium
   ```

2. **Configure settings** (optional):
   - Edit `.env` to customize time entries
   - Default times: 8:30-14:00, 14:45-17:00

3. **Run the automation**:
   ```bash
   uv run python main.py
   ```

## First Run Behavior

- Browser will open (visible, not headless)
- You must **manually log in** to plehub.languagewire.com
- Navigate to the timesheet page
- Wait 60 seconds for the script to continue
- Your session will be saved in `playwright/.auth/state.json`

## Subsequent Runs

- Script automatically loads your saved session
- No manual login required
- Navigates directly to timesheet automation

## What the Script Does

1. Opens browser and loads your session
2. Navigates to the timesheet URL
3. Clicks the "Current" button
4. For each weekday (Monday-Friday):
   - Expands the day dropdown
   - Fills first time entry (8:30-14:00)
   - Clicks '+' to add second entry
   - Fills second time entry (14:45-17:00)
   - Collapses the day dropdown
5. Saves updated session
6. Waits 5 seconds then closes

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
Edit `.env`:
```env
START_TIME_1=09:00
END_TIME_1=13:00
START_TIME_2=14:00
END_TIME_2=18:00
```

## File Structure

```
TimeSheetAutomation/
├── main.py           # Main automation script
├── auth.py           # Session management
├── config.py         # Configuration loader
├── .env              # Your settings (git-ignored)
├── .env.example      # Template settings
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

"""
Configuration module for TimeSheet Automation.

Loads environment variables and provides configuration settings
for the timesheet automation application.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""

    # Base directory
    BASE_DIR = Path(__file__).parent
    
    # Playwright authentication directory
    AUTH_DIR = BASE_DIR / "playwright" / ".auth"
    AUTH_STATE_FILE = AUTH_DIR / "state.json"
    
    # Application URL
    TIMESHEET_URL = os.getenv("TIMESHEET_URL", "https://peoplehub.languagewire.com")
    
    # Time entries configuration
    # Each day can have different time entries configured via environment variables
    TIME_ENTRIES = {
        "monday": [
            {"start": os.getenv("MONDAY_START_TIME_1", "08:30"), "end": os.getenv("MONDAY_END_TIME_1", "14:00")},
            {"start": os.getenv("MONDAY_START_TIME_2", "14:45"), "end": os.getenv("MONDAY_END_TIME_2", "17:00")},
        ],
        "tuesday": [
            {"start": os.getenv("TUESDAY_START_TIME_1", "08:30"), "end": os.getenv("TUESDAY_END_TIME_1", "14:00")},
            {"start": os.getenv("TUESDAY_START_TIME_2", "14:45"), "end": os.getenv("TUESDAY_END_TIME_2", "17:00")},
        ],
        "wednesday": [
            {"start": os.getenv("WEDNESDAY_START_TIME_1", "08:30"), "end": os.getenv("WEDNESDAY_END_TIME_1", "14:00")},
            {"start": os.getenv("WEDNESDAY_START_TIME_2", "14:45"), "end": os.getenv("WEDNESDAY_END_TIME_2", "17:00")},
        ],
        "thursday": [
            {"start": os.getenv("THURSDAY_START_TIME_1", "08:30"), "end": os.getenv("THURSDAY_END_TIME_1", "14:00")},
            {"start": os.getenv("THURSDAY_START_TIME_2", "14:45"), "end": os.getenv("THURSDAY_END_TIME_2", "17:00")},
        ],
        "friday": [
            {"start": os.getenv("FRIDAY_START_TIME_1", "08:30"), "end": os.getenv("FRIDAY_END_TIME_1", "14:00")},
            {"start": os.getenv("FRIDAY_START_TIME_2", "14:45"), "end": os.getenv("FRIDAY_END_TIME_2", "17:00")},
        ],
    }

    # CSS classes indicating days that should be skipped
    SPECIAL_DAY_INDICATORS = [
        os.getenv("SPECIAL_DAY_INDICATOR_HOLIDAY", "wx-timesheet-day__indicator-holiday"),
        os.getenv("SPECIAL_DAY_INDICATOR_VACATION_APPROVED", "wx-timesheet-day__indicator-vacation-approved"),
        os.getenv("SPECIAL_DAY_INDICATOR_ABSENCE_APPROVED", "wx-timesheet-day__indicator-absence-approved"),
    ]

    # Time entries used for half-day holidays
    MORNING_ONLY_ENTRIES = [
        {
            "start": os.getenv("MORNING_ONLY_START_TIME_1", "08:30"),
            "end": os.getenv("MORNING_ONLY_END_TIME_1", "12:30"),
        },
    ]
    AFTERNOON_ONLY_ENTRIES = [
        {
            "start": os.getenv("AFTERNOON_ONLY_START_TIME_1", "13:00"),
            "end": os.getenv("AFTERNOON_ONLY_END_TIME_1", "17:00"),
        },
    ]
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def setup_logging(cls) -> logging.Logger:
        """
        Set up logging configuration.
        
        Returns:
            logging.Logger: Configured logger instance
        """
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        return logging.getLogger("timesheetautomation")
    
    @classmethod
    def ensure_auth_dir(cls) -> None:
        """Ensure the authentication directory exists."""
        cls.AUTH_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def has_saved_session(cls) -> bool:
        """
        Check if a saved session exists.
        
        Returns:
            bool: True if saved session exists, False otherwise
        """
        return cls.AUTH_STATE_FILE.exists()
    
    @classmethod
    def get_weekdays(cls) -> list[str]:
        """
        Get list of weekdays to process.
        
        Returns:
            list[str]: List of weekday names
        """
        return list(cls.TIME_ENTRIES.keys())


# Initialize configuration
Config.ensure_auth_dir()
logger = Config.setup_logging()

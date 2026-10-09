"""
TimeSheet Automation - Main Entry Point

Automates timesheet filling on PeopleHub using Playwright.
"""

import argparse
import re
from datetime import date, datetime, timedelta

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from auth import AuthManager
from config import Config, logger


class TimesheetAutomation:
    """Main automation class for timesheet filling."""
    
    def __init__(self):
        """Initialize the automation."""
        self.config = Config
    
    def get_tooltip_text(self, page: Page, element) -> str:
        """
        Get the tooltip text for an element by reading the aria-describedby reference.
        
        The tooltip text is stored in a hidden div container at the bottom of the body.
        The element has an aria-describedby attribute pointing to the tooltip's ID.
        
        Args:
            page: Playwright page instance
            element: The element with the aria-describedby attribute
            
        Returns:
            str: The tooltip text, or empty string if not found
        """
        try:
            describedby_id = element.get_attribute("aria-describedby")
            logger.debug(f"aria-describedby attribute: {describedby_id}")
            
            if describedby_id:
                # The tooltip text is in a div with the referenced ID
                # Use text_content() instead of inner_text() because the tooltip
                # container is hidden with visibility: hidden
                tooltip_element = page.locator(f"#{describedby_id}")
                if tooltip_element.count() > 0:
                    text = tooltip_element.text_content()
                    logger.debug(f"Found tooltip text: {text}")
                    return text or ""
                else:
                    logger.debug(f"No element found with ID: {describedby_id}")
            else:
                logger.debug("No aria-describedby attribute found on element")
            return ""
        except Exception as e:
            logger.debug(f"Could not get tooltip text: {e}")
            return ""
    
    def is_special_day(self, page: Page, day_name: str) -> tuple[bool, str, str]:
        """
        Check if a day is a special day (holiday, vacation, or absence).
        
        Special days have indicator spans with specific CSS classes that indicate
        the day should not have time entries filled. Also detects half-day holidays
        by checking the tooltip text.
        
        Args:
            page: Playwright page instance
            day_name: Name of the day (e.g., "Monday")
            
        Returns:
            tuple[bool, str, str]: (is_special, reason, tooltip_text) - True if day is special, 
                                   with reason and tooltip text for half-day detection
        """
        try:
            # Find the day header
            day_header = page.locator(
                f"div.wx-timesheet-day__header-weekday:has-text('{day_name}')"
            ).first

            # Indicators live in the day card, not inside the header itself.
            # The day card is the outermost ancestor containing only this day's header.
            day_card = day_header.locator(
                "xpath=ancestor::*[count(.//div[contains(@class,'wx-timesheet-day__header-weekday')])=1][last()]"
            )

            # Check for each special indicator class
            for indicator_class in self.config.SPECIAL_DAY_INDICATORS:
                indicator = day_card.locator(f".{indicator_class}")
                indicator_count = indicator.count()
                logger.debug(f"{day_name}: Checking for {indicator_class}, found {indicator_count}")
                
                if indicator_count > 0:
                    # Get the tooltip text for this indicator
                    tooltip_text = self.get_tooltip_text(page, indicator.first)
                    logger.info(f"{day_name}: Found indicator '{indicator_class}', tooltip: '{tooltip_text}'")
                    
                    # Determine the reason based on the class
                    if "holiday" in indicator_class:
                        reason = "Public Holiday"
                    elif "vacation" in indicator_class:
                        reason = "Approved Vacation"
                    elif "absence" in indicator_class:
                        reason = "Approved Absence"
                    else:
                        reason = "Special Day"
                    
                    return True, reason, tooltip_text
            
            return False, "", ""
            
        except Exception as e:
            logger.warning(f"Could not check special day status for {day_name}: {e}")
            return False, "", ""
        
    def fill_time_entry(self, page: Page, day_name: str, entry_index: int, 
                       start_time: str, end_time: str) -> None:
        """
        Fill a single time entry for a specific day.
        
        Args:
            page: Playwright page instance
            day_name: Name of the day (e.g., "Monday")
            entry_index: Index of the time entry (0 for first, 1 for second)
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
        """
        try:
            logger.info(f"Filling {day_name} entry {entry_index + 1}: {start_time} - {end_time}")
            
            # Find the expanded day section by looking for the day header and then the content
            day_header = page.locator(f"div.wx-timesheet-day__header-weekday:has-text('{day_name}')").first
            
            # Get the aria-controls attribute to find the content div
            content_id = day_header.get_attribute("aria-controls")
            day_section = page.locator(f"#{content_id}")
            
            # If this is the second entry (index 1), click the '+' button first
            if entry_index == 1:
                logger.info(f"Clicking '+' button to add second time block for {day_name}")
                # Find all start-end editors and get the add button from the first one
                add_button = day_section.locator("button.test-add:has-text('+')").first
                add_button.click()
                page.wait_for_timeout(500)  # Brief wait for new fields to appear
            
            # Find all start-end editor rows
            editor_rows = day_section.locator("timesheet-start-end-editor")
            editor_row = editor_rows.nth(entry_index)
            
            # Fill start time
            start_time_input = editor_row.locator("time-input-wrapper.wx-test-start time-input").first
            self._fill_custom_time_input(page, start_time_input, start_time)
            logger.debug(f"Filled start time: {start_time}")
            
            # Fill end time
            end_time_input = editor_row.locator("time-input-wrapper.wx-test-end time-input").first
            self._fill_custom_time_input(page, end_time_input, end_time)
            logger.debug(f"Filled end time: {end_time}")
            
        except Exception as e:
            logger.error(f"Failed to fill time entry for {day_name}: {e}")
            raise
    
    def _fill_custom_time_input(self, page: Page, time_input_locator, time_value: str) -> None:
        """
        Fill a custom time-input component with hours and minutes.
        
        The custom time-input has separate spans for hours and minutes that need to be clicked
        and filled individually.
        
        Args:
            page: Playwright page instance
            time_input_locator: Locator for the time-input element
            time_value: Time in HH:MM format
        """
        hours, minutes = time_value.split(":")
        
        # Click on the time input to focus it
        time_input_locator.click()
        page.wait_for_timeout(100)
        
        # Click on the hours span and type hours
        hours_span = time_input_locator.locator("span.wx-time-input__hours")
        hours_span.click()
        page.wait_for_timeout(100)
        
        # Select all and type new hours
        page.keyboard.press("Control+A")
        page.keyboard.type(hours)
        page.wait_for_timeout(100)
        
        # Click on the minutes span and type minutes
        minutes_span = time_input_locator.locator("span.wx-time-input__minutes")
        minutes_span.click()
        page.wait_for_timeout(100)
        
        # Select all and type new minutes
        page.keyboard.press("Control+A")
        page.keyboard.type(minutes)
        page.wait_for_timeout(100)
    
    def process_day(self, page: Page, day_name: str) -> None:
        """
        Process all time entries for a single day.
        
        Skips processing for special days (holidays, approved vacations, approved absences),
        but handles half-day holidays by filling only morning or afternoon entries.
        
        Args:
            page: Playwright page instance
            day_name: Name of the day to process
        """
        try:
            logger.info(f"Processing {day_name}")
            
            # Check if this is a special day that should be skipped
            is_special, reason, tooltip_text = self.is_special_day(page, day_name)
            
            if is_special:
                tooltip_lower = tooltip_text.lower()
                
                # Check for half-day holidays
                if "afternoon off" in tooltip_lower:
                    logger.info(f"🌅 {day_name}: {reason} - Afternoon off ('{tooltip_text}')")
                    logger.info("   → Filling morning hours only (8:30-12:30)")
                    entries = self.config.MORNING_ONLY_ENTRIES
                elif "morning off" in tooltip_lower:
                    logger.info(f"🌆 {day_name}: {reason} - Morning off ('{tooltip_text}')")
                    logger.info("   → Filling afternoon hours only (13:00-17:00)")
                    entries = self.config.AFTERNOON_ONLY_ENTRIES
                else:
                    # Full day off - skip entirely
                    logger.info(f"⏭️  Skipping {day_name}: {reason}")
                    if tooltip_text:
                        logger.info(f"   Tooltip: {tooltip_text}")
                    return
            else:
                # Regular day - get normal time entries
                entries = self.config.TIME_ENTRIES.get(day_name.lower(), [])
            
            if not entries:
                logger.warning(f"No time entries configured for {day_name}")
                return
            
            # Find the day header using the specific HTML structure
            # The header is a div with class wx-timesheet-day__header-weekday
            # and contains a span with the day name
            day_header = page.locator(
                f"div.wx-timesheet-day__header-weekday:has-text('{day_name}')"
            ).first
            
            # Check if it's collapsed (aria-expanded="false")
            is_expanded = day_header.get_attribute("aria-expanded")
            if is_expanded == "false":
                logger.info(f"Expanding {day_name} dropdown")
                day_header.click()
                page.wait_for_timeout(500)  # Wait for expansion animation
            else:
                logger.info(f"{day_name} already expanded")
            
            # Fill each time entry
            for index, entry in enumerate(entries):
                self.fill_time_entry(
                    page, 
                    day_name, 
                    index, 
                    entry["start"], 
                    entry["end"]
                )
                page.wait_for_timeout(300)  # Brief pause between entries
            
            # Collapse the dropdown after filling
            is_expanded = day_header.get_attribute("aria-expanded")
            if is_expanded == "true":
                logger.info(f"Collapsing {day_name} dropdown")
                day_header.click()
                page.wait_for_timeout(300)
            
            logger.info(f"Completed {day_name}")
            
        except Exception as e:
            logger.error(f"Failed to process {day_name}: {e}")
            raise
    
    def collapse_all_days(self, page: Page) -> None:
        """
        Collapse all expanded days to trigger auto-save.
        
        Args:
            page: Playwright page instance
        """
        try:
            logger.info("Collapsing all days to trigger auto-save...")
            
            # Find all expanded day headers
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            for day_name in weekdays:
                day_header = page.locator(
                    f"div.wx-timesheet-day__header-weekday:has-text('{day_name}')"
                ).first
                
                # Check if it's expanded
                is_expanded = day_header.get_attribute("aria-expanded")
                if is_expanded == "true":
                    logger.info(f"Collapsing {day_name}")
                    day_header.click()
                    page.wait_for_timeout(300)  # Wait for collapse animation
            
            logger.info("All days collapsed")
            
        except Exception as e:
            logger.warning(f"Failed to collapse all days: {e}")
            # Don't raise - this is not critical
    
    def navigate_to_timesheet_page(self, page: Page) -> None:
        """
        Navigate from main page to the timesheet page.
        
        Args:
            page: Playwright page instance
        """
        try:
            logger.info("Looking for Timesheet navigation link")
            
            # Wait for page to be ready
            page.wait_for_load_state("domcontentloaded")
            
            # Try to find the timesheet link/menu item
            # Common patterns for timesheet navigation
            timesheet_link = page.locator(
                "a:has-text('Timesheet'), "
                "a:has-text('Time sheet'), "
                "button:has-text('Timesheet'), "
                "[href*='timesheet'], "
                "[data-testid*='timesheet']"
            ).first
            
            logger.info("Clicking Timesheet link")
            timesheet_link.click()
            
            # Wait for navigation
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1000)
            logger.info("Navigated to timesheet page")
            
        except Exception as e:
            logger.warning(f"Could not find timesheet link automatically: {e}")
            logger.info("Assuming already on timesheet page or manual navigation needed")
    
    def click_current_button(self, page: Page) -> None:
        """
        Find and click the 'Current' button on the timesheet page.
        
        Args:
            page: Playwright page instance
        """
        try:
            logger.info("Looking for 'Current' button")
            
            # Look for the "Current" button with specific class attributes
            current_button = page.locator(
                "button.btn.btn-primary:has-text('Current'), "
                "button.button:has-text('Current'), "
                "button:has-text('Current')"
            ).first
            
            # Wait for button to be visible and clickable
            current_button.wait_for(state="visible", timeout=15000)
            logger.info("Clicking 'Current' button")
            current_button.click()
            
            # Wait for timesheet form to load
            page.wait_for_timeout(2000)
            logger.info("Timesheet form loaded")
            
        except PlaywrightTimeoutError:
            logger.error("Timeout waiting for 'Current' button. Make sure you're on the timesheet page.")
            raise
        except Exception as e:
            logger.error(f"Failed to click 'Current' button: {e}")
            raise
    
    @staticmethod
    def parse_week_label(label: str) -> date:
        """
        Parse the week label shown in the navigation bar into the week's start date.

        Handles labels like "5 October - 11 October 2026" and year-crossing
        labels like "28 December - 3 January 2027".

        Args:
            label: Text of the week navigation label

        Returns:
            date: First day of the displayed week
        """
        match = re.match(r"\s*(\d{1,2})\s+(\w+)\s*-\s*(\d{1,2})\s+(\w+)\s+(\d{4})", label)
        if not match:
            raise ValueError(f"Unrecognised week label: '{label.strip()}'")
        start_day, start_month, _, end_month, year = match.groups()
        year = int(year)
        start_month_num = datetime.strptime(start_month, "%B").month
        end_month_num = datetime.strptime(end_month, "%B").month
        if start_month_num > end_month_num:
            year -= 1
        return date(year, start_month_num, int(start_day))

    def get_displayed_week_start(self, page: Page) -> date:
        """
        Read the start date of the week currently displayed.

        Args:
            page: Playwright page instance

        Returns:
            date: First day of the displayed week
        """
        label = page.locator(".wx-timesheet-navigation-control__label").first
        label.wait_for(state="visible", timeout=15000)
        return self.parse_week_label(label.inner_text())

    def navigate_to_week(self, page: Page, target_start: date, max_steps: int = 104) -> None:
        """
        Navigate to the week starting on target_start using the arrow buttons.

        The 'Current' button opens the next open timesheet, which is not necessarily
        this calendar week, so the displayed week is read from the label and every
        click is verified to move exactly one week. Raises instead of continuing on
        an unexpected week, so the automation never fills the wrong timesheet.

        Args:
            page: Playwright page instance
            target_start: Monday of the week to open
            max_steps: Maximum number of arrow clicks before giving up
        """
        displayed = self.get_displayed_week_start(page)
        logger.info(f"Displayed week starts {displayed}, target week starts {target_start}")

        for _ in range(max_steps):
            if displayed == target_start:
                logger.info(f"On target week starting {target_start}")
                return

            direction = "previous" if target_start < displayed else "next"
            previous_start = displayed
            expected = displayed + timedelta(days=-7 if direction == "previous" else 7)
            page.locator(f"#timesheet-navigation-button-{direction}").click()

            # Wait (up to 10 seconds) for the label to change
            for _ in range(20):
                page.wait_for_timeout(500)
                displayed = self.get_displayed_week_start(page)
                if displayed != previous_start:
                    break
            if displayed != expected:
                raise RuntimeError(
                    f"Week navigation failed: expected week starting {expected}, "
                    f"but the page shows week starting {displayed}"
                )
            logger.info(f"Moved to week starting {displayed}")

        raise RuntimeError(f"Could not reach week starting {target_start} within {max_steps} steps")

    def ensure_week_editable(self, page: Page) -> None:
        """
        Fail if the displayed timesheet cannot be edited (e.g. submitted or approved).

        Args:
            page: Playwright page instance
        """
        state = page.locator(".wx-timesheet-action-buttons__save-state")
        state_text = state.first.inner_text().strip() if state.count() > 0 else "unknown"
        submit_visible = page.locator("#timesheet-action-button-submit").is_visible()
        if not submit_visible:
            raise RuntimeError(
                f"Timesheet is not editable (status: '{state_text}'). "
                "It is probably already submitted or approved."
            )
        logger.info(f"Timesheet is editable (status: '{state_text}')")

    def run(self, target_start: date, dry_run: bool = False) -> None:
        """
        Run the timesheet automation.

        Args:
            target_start: Monday of the week to fill
            dry_run: Only navigate and validate the week, do not fill anything
        """
        logger.info("Starting timesheet automation")
        
        with sync_playwright() as p:
            try:
                # Launch browser in headed mode (visible)
                logger.info("Launching browser")
                browser = p.chromium.launch(headless=False)
                
                # Create context with saved session if available
                context = AuthManager.create_context_with_session(browser)
                page = context.new_page()
                
                # Navigate to the application
                AuthManager.ensure_authenticated(page, self.config.TIMESHEET_URL)
                
                # If first run, wait for manual login
                if not AuthManager.has_saved_session():
                    logger.info("Waiting 60 seconds for you to log in and navigate to timesheet page...")
                    logger.info("Please complete login and go to the timesheet page")
                    page.wait_for_timeout(60000)  # Wait 60 seconds
                    
                    # Save session after login
                    AuthManager.save_session(context)
                else:
                    # If we have a saved session, navigate to timesheet page
                    logger.info("Session found, navigating to timesheet page")
                    self.navigate_to_timesheet_page(page)
                
                # Click 'Current' button to open current week
                self.click_current_button(page)

                # Move to the requested week and make sure it can be edited
                self.navigate_to_week(page, target_start)
                self.ensure_week_editable(page)

                if dry_run:
                    logger.info(f"Dry run: week starting {target_start} is reachable and editable, nothing filled")
                    return
                
                # Process each weekday
                weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                for day in weekdays:
                    self.process_day(page, day)
                    page.wait_for_timeout(500)  # Brief pause between days
                
                # Wait for auto-save to complete after Friday is collapsed
                logger.info("Waiting for auto-save to complete...")
                page.wait_for_timeout(10000)
                
                logger.info("=" * 60)
                logger.info("Timesheet automation completed successfully!")
                logger.info("=" * 60)
                
                # Get and display the current URL for review
                current_url = page.url
                logger.info("Review and submit your timesheet at:")
                logger.info(f"{current_url}")
                logger.info("=" * 60)
                
                # Save session state at the end
                if AuthManager.has_saved_session():
                    AuthManager.save_session(context)
                    logger.info("Session state updated")
                
            except KeyboardInterrupt:
                logger.info("Automation interrupted by user")
            except Exception as e:
                logger.error(f"Automation failed: {e}")
                logger.exception("Full traceback:")
                raise
            finally:
                logger.info("Closing browser")
                browser.close()


def main():
    """Main entry point."""
    try:
        parser = argparse.ArgumentParser(description="Fill the PeopleHub timesheet")
        week_group = parser.add_mutually_exclusive_group()
        week_group.add_argument(
            "--week", type=date.fromisoformat,
            help="Any date (YYYY-MM-DD) within the week to fill",
        )
        week_group.add_argument(
            "--weeks-back", type=int, default=0,
            help="Number of weeks before this week to fill (e.g. 1 = previous week)",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Only navigate to the week and check it is editable, do not fill anything",
        )
        args = parser.parse_args()

        if args.weeks_back < 0:
            parser.error("--weeks-back must be 0 or greater")
        reference = args.week or date.today() - timedelta(weeks=args.weeks_back)
        target_start = reference - timedelta(days=reference.weekday())

        automation = TimesheetAutomation()
        automation.run(target_start, dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Application error: {e}")
        exit(1)


if __name__ == "__main__":
    main()


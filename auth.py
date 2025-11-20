"""
Authentication module for TimeSheet Automation.

Handles browser session management, including saving and loading
authentication state to avoid repeated logins.
"""

from pathlib import Path
from playwright.sync_api import Browser, BrowserContext, Page

from config import Config, logger


class AuthManager:
    """Manages authentication and session persistence."""
    
    @staticmethod
    def has_saved_session() -> bool:
        """
        Check if a saved authentication session exists.
        
        Returns:
            bool: True if saved session file exists
        """
        return Config.has_saved_session()
    
    @staticmethod
    def create_context_with_session(browser: Browser) -> BrowserContext:
        """
        Create a browser context with saved session state.
        
        Args:
            browser: Playwright browser instance
            
        Returns:
            BrowserContext: Browser context with loaded session state
        """
        if AuthManager.has_saved_session():
            logger.info(f"Loading saved session from {Config.AUTH_STATE_FILE}")
            return browser.new_context(storage_state=str(Config.AUTH_STATE_FILE))
        else:
            logger.info("No saved session found, creating new context")
            return browser.new_context()
    
    @staticmethod
    def save_session(context: BrowserContext) -> None:
        """
        Save the current browser session state.
        
        Args:
            context: Browser context to save
        """
        try:
            # Ensure directory exists
            Config.ensure_auth_dir()
            
            # Save storage state (cookies, localStorage, etc.)
            context.storage_state(path=str(Config.AUTH_STATE_FILE))
            logger.info(f"Session saved to {Config.AUTH_STATE_FILE}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            raise
    
    @staticmethod
    def clear_saved_session() -> None:
        """Delete the saved session file if it exists."""
        if Config.AUTH_STATE_FILE.exists():
            Config.AUTH_STATE_FILE.unlink()
            logger.info("Saved session cleared")
    
    @staticmethod
    def ensure_authenticated(page: Page, url: str, timeout: int = 30000) -> None:
        """
        Ensure the user is authenticated by navigating to URL.
        
        If no saved session exists, this will allow manual login.
        
        Args:
            page: Playwright page instance
            url: URL to navigate to
            timeout: Navigation timeout in milliseconds
        """
        try:
            logger.info(f"Navigating to {url}")
            page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            
            # If this is first run without saved session, give user time to login
            if not AuthManager.has_saved_session():
                logger.info("=" * 60)
                logger.info("FIRST RUN: Please log in manually in the browser window")
                logger.info("The session will be saved for future runs")
                logger.info("After logging in, navigate to the timesheet page")
                logger.info("=" * 60)
                
                # Wait for user to manually navigate after login
                # We'll detect when they're on a page that looks authenticated
                page.wait_for_timeout(3000)  # Give page time to load
                
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            raise
    
    @staticmethod
    def wait_for_manual_login(page: Page, expected_url_pattern: str = None, 
                             timeout: int = 120000) -> None:
        """
        Wait for user to complete manual login.
        
        Args:
            page: Playwright page instance
            expected_url_pattern: URL pattern to wait for (optional)
            timeout: Maximum time to wait in milliseconds
        """
        logger.info("Waiting for manual login to complete...")
        logger.info("Please log in and navigate to the timesheet page")
        
        try:
            # Wait for navigation to complete
            if expected_url_pattern:
                page.wait_for_url(f"**/{expected_url_pattern}**", timeout=timeout)
            else:
                # Just wait a reasonable time for user to login
                page.wait_for_timeout(timeout)
                
            logger.info("Login appears to be complete")
        except Exception as e:
            logger.warning(f"Timeout waiting for login: {e}")
            logger.info("Continuing anyway, session will be saved")

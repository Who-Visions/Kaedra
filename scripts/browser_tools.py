"""
Browser Tools - Puppeteer & Playwright automation for Kaedra Orchestrator

Provides browser automation capabilities using Playwright (Python version).
Similar capabilities to Puppeteer but with Python integration.
"""

import asyncio
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class BrowserTools:
    """Browser automation tools using Playwright."""

    def __init__(self, headless: bool = True):
        """
        Initialize browser tools.

        Args:
            headless: Run browser in headless mode (no GUI)
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.browser_context = None

    async def start_browser(self, browser_type: str = "chromium") -> Dict[str, Any]:
        """
        Start browser instance.

        Args:
            browser_type: chromium, firefox, or webkit

        Returns:
            Status dict
        """
        if not PLAYWRIGHT_AVAILABLE:
            return {
                "status": "error",
                "error": "Playwright not installed. Run: pip install playwright && playwright install"
            }

        try:
            self.playwright = await async_playwright().start()

            if browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
            elif browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.headless)
            elif browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=self.headless)
            else:
                raise ValueError(f"Unknown browser type: {browser_type}")

            self.browser_context = await self.browser.new_context()
            self.page = await self.browser_context.new_page()

            return {
                "status": "success",
                "browser": browser_type,
                "headless": self.headless
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def stop_browser(self) -> Dict[str, Any]:
        """Stop browser instance."""
        try:
            if self.page:
                await self.page.close()
            if self.browser_context:
                await self.browser_context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            self.page = None
            self.browser_context = None
            self.browser = None
            self.playwright = None

            return {"status": "success"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to URL.

        Args:
            url: URL to navigate to

        Returns:
            Navigation result
        """
        if not self.page:
            return {"status": "error", "error": "Browser not started"}

        try:
            response = await self.page.goto(url)

            return {
                "status": "success",
                "url": url,
                "response_status": response.status,
                "title": await self.page.title()
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def click(self, selector: str) -> Dict[str, Any]:
        """
        Click element by selector.

        Args:
            selector: CSS selector or XPath

        Returns:
            Click result
        """
        if not self.page:
            return {"status": "error", "error": "Browser not started"}

        try:
            await self.page.click(selector)
            return {"status": "success", "selector": selector}

        except Exception as e:
            return {"status": "error", "error": str(e), "selector": selector}

    async def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        """
        Type text into element.

        Args:
            selector: CSS selector
            text: Text to type

        Returns:
            Type result
        """
        if not self.page:
            return {"status": "error", "error": "Browser not started"}

        try:
            await self.page.fill(selector, text)
            return {"status": "success", "selector": selector}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def screenshot(self, filepath: str = None, full_page: bool = False) -> Dict[str, Any]:
        """
        Take screenshot.

        Args:
            filepath: Path to save screenshot (default: auto-generated)
            full_page: Capture full scrollable page

        Returns:
            Screenshot result with filepath
        """
        if not self.page:
            return {"status": "error", "error": "Browser not started"}

        try:
            if not filepath:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = f"screenshot_{timestamp}.png"

            await self.page.screenshot(path=filepath, full_page=full_page)

            return {
                "status": "success",
                "filepath": filepath,
                "full_page": full_page
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_text(self, selector: str) -> Dict[str, Any]:
        """
        Get text content from element.

        Args:
            selector: CSS selector

        Returns:
            Text content
        """
        if not self.page:
            return {"status": "error", "error": "Browser not started"}

        try:
            element = await self.page.query_selector(selector)
            if element:
                text = await element.text_content()
                return {"status": "success", "text": text, "selector": selector}
            else:
                return {"status": "error", "error": "Element not found", "selector": selector}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def execute_script(self, script: str) -> Dict[str, Any]:
        """
        Execute JavaScript in page.

        Args:
            script: JavaScript code to execute

        Returns:
            Script result
        """
        if not self.page:
            return {"status": "error", "error": "Browser not started"}

        try:
            result = await self.page.evaluate(script)
            return {"status": "success", "result": result}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> Dict[str, Any]:
        """
        Wait for element to appear.

        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds

        Returns:
            Wait result
        """
        if not self.page:
            return {"status": "error", "error": "Browser not started"}

        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return {"status": "success", "selector": selector}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_page_info(self) -> Dict[str, Any]:
        """Get current page information."""
        if not self.page:
            return {"status": "error", "error": "Browser not started"}

        try:
            return {
                "status": "success",
                "url": self.page.url,
                "title": await self.page.title(),
                "viewport": self.page.viewport_size
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}


# Synchronous wrapper for orchestrator use
class BrowserToolsSync:
    """Synchronous wrapper for browser tools."""

    def __init__(self, headless: bool = True):
        self.tools = BrowserTools(headless=headless)
        self.loop = None

    def _run_async(self, coro):
        """Run async coroutine synchronously."""
        if self.loop is None:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        return self.loop.run_until_complete(coro)

    def start_browser(self, browser_type: str = "chromium") -> Dict[str, Any]:
        """Start browser."""
        return self._run_async(self.tools.start_browser(browser_type))

    def stop_browser(self) -> Dict[str, Any]:
        """Stop browser."""
        return self._run_async(self.tools.stop_browser())

    def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL."""
        return self._run_async(self.tools.navigate(url))

    def click(self, selector: str) -> Dict[str, Any]:
        """Click element."""
        return self._run_async(self.tools.click(selector))

    def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        """Type text."""
        return self._run_async(self.tools.type_text(selector, text))

    def screenshot(self, filepath: str = None, full_page: bool = False) -> Dict[str, Any]:
        """Take screenshot."""
        return self._run_async(self.tools.screenshot(filepath, full_page))

    def get_text(self, selector: str) -> Dict[str, Any]:
        """Get element text."""
        return self._run_async(self.tools.get_text(selector))

    def execute_script(self, script: str) -> Dict[str, Any]:
        """Execute JavaScript."""
        return self._run_async(self.tools.execute_script(script))

    def wait_for_selector(self, selector: str, timeout: int = 30000) -> Dict[str, Any]:
        """Wait for element."""
        return self._run_async(self.tools.wait_for_selector(selector, timeout))

    def get_page_info(self) -> Dict[str, Any]:
        """Get page info."""
        return self._run_async(self.tools.get_page_info())


# Singleton for orchestrator use
browser_tools = BrowserToolsSync(headless=True)


if __name__ == "__main__":
    # Test browser tools
    print("🌐 Browser Tools Test\n")

    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not installed")
        print("Install with: pip install playwright && playwright install")
    else:
        tools = BrowserToolsSync(headless=False)

        print("Starting browser...")
        result = tools.start_browser()
        print(f"  Status: {result['status']}")

        if result['status'] == 'success':
            print("\nNavigating to example.com...")
            result = tools.navigate("https://example.com")
            print(f"  Status: {result['status']}")
            print(f"  Title: {result.get('title', 'N/A')}")

            print("\nTaking screenshot...")
            result = tools.screenshot("test_screenshot.png")
            print(f"  Status: {result['status']}")
            print(f"  Saved: {result.get('filepath', 'N/A')}")

            print("\nStopping browser...")
            tools.stop_browser()
            print("  Done!")

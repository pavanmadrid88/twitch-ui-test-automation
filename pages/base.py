from typing import Optional
from playwright.sync_api import Page
import time

class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def goto(self, url: str):
        """Navigate and wait for network to settle."""
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")

    def dismiss_overlays(self, wait_time: float = 1.0):
        """
        Try to dismiss common overlays / cookie banners / modals on any page.

        Args:
            wait_time (float): max seconds to wait for an overlay to vanish after clicking.
                               Default = 1.0 second.

        Returns:
            tuple[str|None, str|None]: (clicked_selector_or_text, phase) or (None, None) if nothing clicked.
        """
        page = self.page
        max_wait = max(0.2, wait_time)  # ensure at least 0.2s wait
        poll_interval = 0.25  # seconds

        def _click_and_wait_locator(locator):
            try:
                if locator.count() and locator.is_visible():
                    try:
                        locator.click()
                    except Exception:
                        # try JavaScript click as fallback
                        try:
                            handle = locator.element_handle()
                            if handle:
                                page.evaluate("(el) => el.click()", handle)
                        except Exception:
                            pass
                    # Wait until locator is not visible
                    vanished = self.custom_wait(
                        condition=lambda: not locator.is_visible(),
                        max_wait=max_wait,
                        poll_interval=poll_interval,
                    )
                    return vanished
            except Exception:
                return False
            return False

        # known overlay selectors
        known_selectors = [
            'button[aria-label="Close"]',
            'button:has-text("Close")',
            'button:has-text("No thanks")',
            'button:has-text("Not now")',
            'button:has-text("Got it")',
            'button:has-text("I Accept")',
            'button:has-text("Accept")',
            'div[role="dialog"] button',
            'button[aria-label*="close" i]',
            'button[aria-label*="dismiss" i]',
        ]

        for sel in known_selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() and loc.is_visible():
                    ok = _click_and_wait_locator(loc)
                    return (sel, "known")
            except Exception:
                continue

        # generic dynamic buttons
        try:
            keywords = ["close", "dismiss", "no", "deny", "reject", "cancel", "got it", "ok", "accept"]
            btns = page.locator("button, [role='button']")
            for i in range(btns.count()):
                btn = btns.nth(i)
                if not btn.is_visible():
                    continue
                try:
                    txt = (btn.inner_text() or "").strip().lower()
                    if any(k in txt for k in keywords):
                        _click_and_wait_locator(btn)
                        return (txt, "dynamic")
                except Exception:
                    continue
        except Exception:
            pass

        # generic wildcard attributes
        generic_attrs = [
            '*[aria-label*="close" i]',
            '*[aria-label*="accept" i]',
            '*[aria-label*="dismiss" i]',
            '*[title*="close" i]',
            '*[title*="dismiss" i]',
            '*[alt*="close" i]',
        ]
        for sel in generic_attrs:
            try:
                el = page.locator(sel).first
                if el.count() and el.is_visible():
                    _click_and_wait_locator(el)
                    return (sel, "generic")
            except Exception:
                continue

        # Escape key fallback
        try:
            page.keyboard.press("Escape")
            self.custom_wait(condition=lambda: True, max_wait=0.1)
            return ("Escape", "escape")
        except Exception:
            return (None, None)

    def get_text(self, selector: str, timeout: float = 5.0) -> Optional[str]:
        """Wait for selector to be visible, return its text or None."""
        if not self.custom_wait(element=selector, max_wait=timeout, check_type="visible"):
            return None

        loc = self.page.locator(selector).first
        try:
            text = loc.inner_text()
        except Exception:
            try:
                text = loc.text_content()
            except Exception:
                return None
        return text.strip()

    def safe_click(self, selector: str, timeout: float = 10):
        """
        Dismiss overlays, wait for element visibility, then click.
        Args:
            selector (str): CSS or XPath locator for the element to click.
            timeout (float): maximum wait time in seconds (default = 10s).
        """
        # clear any popups or modals first
        self.dismiss_overlays()

        # wait for element to become visible using custom_wait
        element_visible = self.custom_wait(element=selector, max_wait=timeout, check_type="visible")
        if not element_visible:
            raise TimeoutError(f"Element '{selector}' not visible after {timeout} seconds")

        # click once visible
        locator = self.page.locator(selector)
        locator.click()

    def safe_fill(self, selector: str, text: str, timeout: float = 10):
        """
        Dismiss overlays, wait for input field to be visible, then fill it.

        Args:
            selector (str): locator for the input element
            text (str): text to fill into the element
            timeout (float): maximum wait time in seconds (default: 10s)
        """
        # Try clearing any popups that might block the element
        self.dismiss_overlays()

        # Wait for the element to be visible using custom_wait
        element_visible = self.custom_wait(element=selector, max_wait=timeout, check_type="visible")

        if not element_visible:
            raise TimeoutError(f"Element '{selector}' not visible after {timeout} seconds")

        # Fill the input once visible
        locator = self.page.locator(selector)
        locator.fill(text)

    def scroll_down(self, times: int = 1, wait_time: float = 0.8):
        """
        Scroll down the page by one viewport height `times` times.
        Args:
            times (int): number of times to scroll (default = 1)
            wait_time (float): seconds to wait between scrolls (default = 0.8s)
        """
        for _ in range(times):
            try:
                self.page.evaluate("window.scrollBy(0, window.innerHeight);")
            except Exception:
                pass

            # Wait a short while for page content to load after each scroll
            self.custom_wait(condition=lambda: True, max_wait=wait_time)

            # wait briefly for network to stabilize
            try:
                self.custom_wait(
                    condition=lambda: self.page.evaluate("document.readyState === 'complete'"),
                    max_wait=3
                )
            except Exception:
                pass

    def custom_wait(
            self,
            element: str = None,
            max_wait: float = 5,
            poll_interval: float = 0.5,
            condition=None,
            check_type: str = "visible",
    ) -> bool:
        """
        Waits until the element becomes visible (default) or a custom condition returns True.

        Args:
            element (str): locator string (CSS/XPath/etc.) for the element to wait on.
            max_wait (float): maximum wait time in seconds. Default = 5.
            poll_interval (float): how often to check (in seconds). Default = 0.5.
            condition (callable): optional custom callable returning True when condition is met.
            check_type (str): "visible" | "hidden" | "attached" — defaults to "visible".

        Returns:
            bool: True if condition met or element visible within timeout, else False.
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                # 1️Custom condition check
                if condition and condition():
                    return True

                # 2️Element visibility check
                if element:
                    locator = self.page.locator(element)
                    if check_type == "visible" and locator.first.is_visible():
                        return True
                    elif check_type == "hidden" and not locator.first.is_visible():
                        return True
                    elif check_type == "attached" and locator.count() > 0:
                        return True

            except Exception:
                pass

            time.sleep(poll_interval)

        return False


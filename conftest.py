"""
Conftest that launches the installed Google Chrome and applies Playwright device emulation.

Usage examples:
  # headed Pixel 5 (default)
  pytest -q tests/ -s --device="Pixel 5"

  # headless Pixel 5
  pytest -q tests/ -s --device="Pixel 5" --headless

Notes:
- Requires Google Chrome to be installed on the machine.
- Playwright must be installed and browsers tooling available (python -m playwright install).
- This intentionally uses the real Chrome binary (channel="chrome").
"""

import os
import base64
import warnings
import traceback
import datetime
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page
import data.constants
from utils.ui_test_utils import get_logger

try:
    from pytest_html import extras  # pytest-html >= 2.0
    _HAVE_PYTEST_HTML = True
except Exception:
    extras = None
    _HAVE_PYTEST_HTML = False

# Default timeout and Mobile Emulator device
DEFAULT_TIMEOUT_MS = data.constants.Config.DEFAULT_TIMEOUT_MS
DEFAULT_DEVICE = data.constants.MobileEmulatorDevice.PIXEL_5


def pytest_addoption(parser):
    parser.addoption(
        "--device",
        action="store",
        default=os.getenv("PLAYWRIGHT_DEVICE", DEFAULT_DEVICE),
        help='Playwright device descriptor to emulate (e.g. "Pixel 5", "iPhone 12").',
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run Chrome in headless mode.",
    )


@pytest.fixture(scope="session")
def pw() -> Playwright:
    """Start Playwright once per session."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(pw: Playwright, request) -> Browser:
    """
    Launch the installed Google Chrome (channel="chrome").
    Adds a chrome arg to relax autoplay policy so video playback is more likely.
    """
    headless = request.config.getoption("--headless")
    try:
        # Use the installed Google Chrome
        browser = pw.chromium.launch(
            channel="chrome",
            headless=headless,
            args=["--autoplay-policy=no-user-gesture-required"],
        )
    except Exception as e:
        # Helpful error if Chrome/channel not available
        raise RuntimeError(
            "Failed to launch Google Chrome via Playwright. Ensure Google Chrome is installed "
            "and Playwright is set up correctly (run: python -m playwright install). "
            f"Original error: {e}"
        )
    yield browser
    try:
        browser.close()
    except Exception:
        pass


@pytest.fixture(scope="function")
def context(request, pw: Playwright, browser: Browser) -> BrowserContext:
    """
    Create a browser context using the selected Playwright device descriptor (mobile emulation).
    The CLI --device option controls which device to emulate.
    """
    device_name = request.config.getoption("--device")
    device = None
    try:
        device = pw.devices.get(device_name)
    except Exception:
        warnings.warn(f"Playwright device '{device_name}' not found — running without device emulation.")

    context_args = {}
    if device:
        context_args.update(device)

    # create context with device emulation (e.g., Pixel 5)
    ctx = browser.new_context(**context_args)
    yield ctx
    try:
        ctx.close()
    except Exception:
        pass


@pytest.fixture(scope="function")
def page(request, context: BrowserContext) -> Page:
    """New page per test. Attach page to pytest node for hooks to access."""
    page = context.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)
    # attach to node for failure hooks
    request.node._page = page  # type: ignore[attr-defined]
    yield page
    try:
        page.close()
    except Exception:
        pass

@pytest.fixture
def logger(request):
    test_name = request.node.name
    return get_logger(test_name)


def _resolve_screenshot_dir():
    """
    Resolve the screenshot directory from data.constants.Config.SCREENSHOT_DIRECTORY if present,
    otherwise fallback to ./artifacts/screenshots
    """
    out_dir = None
    try:
        out_dir = getattr(data.constants.Config, "SCREENSHOT_DIRECTORY", None)
    except Exception:
        out_dir = None

    if out_dir:
        out_dir = Path(out_dir)
    else:
        out_dir = Path("artifacts/screenshots")

    # Ensure it's a folder path
    if out_dir.is_file():
        # if a file was accidentally provided, fallback to artifacts/screenshots
        out_dir = Path("artifacts/screenshots")

    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    On test failure (setup/call/teardown) take a best-effort screenshot and embed into pytest-html if available.
    This implementation:
      - handles setup/call/teardown
      - writes a timestamped file to screenshots dir
      - prefers attaching the saved file path (most compatible)
      - falls back to embedding as data URI (for --self-contained-html)
      - final fallback: add a clickable HTML link to the saved file
      - surfaces errors as pytest warnings (not silent)
    """
    outcome = yield
    rep = outcome.get_result()

    # handle setup, call and teardown failures
    if rep.when not in ("setup", "call", "teardown"):
        return

    page = getattr(item, "_page", None)
    if not page:
        return

    if not rep.failed:
        return

    try:
        # get screenshot bytes (returns bytes if no path)
        img_bytes = page.screenshot(full_page=True)

        # resolve / create screenshot directory
        out_dir = _resolve_screenshot_dir()

        # create unique name to avoid overwrite
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        safe_name = item.name.replace(" ", "_").replace("/", "_")
        out_path = out_dir / f"{safe_name}_{timestamp}.png"

        # write file to disk for manual review
        with open(out_path, "wb") as fh:
            fh.write(img_bytes)

        # attach to pytest-html if available (preferred: file path, fallback: data URI)
        if _HAVE_PYTEST_HTML and extras is not None:
            extra = getattr(rep, "extra", [])

            attached = False
            # Attempt 1: attach file path (most compatible)
            try:
                extra.append(extras.image(str(out_path)))
                rep.extra = extra
                attached = True
            except Exception:
                attached = False

            # Attempt 2: fallback to data URI (if file-path attach failed)
            if not attached:
                try:
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                    data_uri = f"data:image/png;base64,{img_b64}"
                    try:
                        extra.append(extras.image(data_uri, mime_type="image/png"))
                    except TypeError:
                        extra.append(extras.image(data_uri))
                    rep.extra = extra
                    attached = True
                except Exception:
                    attached = False

            # Attempt 3: final fallback, clickable link to saved file
            if not attached:
                try:
                    html = f'<div>Screenshot saved to <a href="{out_path}">{out_path.name}</a></div>'
                    extra.append(extras.html(html))
                    rep.extra = extra
                except Exception:
                    # If even this fails, continue to warning below
                    pass

    except Exception as e:
        # surface the error into pytest warnings so you can see it in test output instead of silence
        tb = traceback.format_exc()
        warning_msg = f"Failed to capture/attach screenshot for {item.name}: {e}\n{tb}"
        # Try to use pytest's warning system; if that fails, print it (CI logs)
        try:
            item.warn(pytest.PytestWarning(warning_msg))
        except Exception:
            print(warning_msg)

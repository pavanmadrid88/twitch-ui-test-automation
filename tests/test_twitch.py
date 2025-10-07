# tests/test_twitch_pause.py
import pytest

import data.constants
from pages.home_page import HomePage

@pytest.mark.pavan
def test_open_twitch_and_validate_streamer(page,get_logger_fix):
    """
    Minimal run: opens Twitch in mobile emulation and pauses Playwright inspector.
    Use the inspector to find stable selectors for the search icon and input.
    Steps:
      1. Run with: pytest -q tests/test_twitch_pause.py -s --device="Pixel 5"
      2. When Playwright inspector opens, hover/click elements to copy selectors.
      3. Update pages/home_page.py placeholders and proceed with full flow.
    """
    # Launch Twitch
    home = HomePage(page)
    home.open()

    # navigate to Directory/search view
    browse_directory_page = home.open_search()

    # search for StarCraft II
    search_results_page = browse_directory_page.search_for(data.constants.SearchText.STARCRAFT_II)

    # scroll twice on Search view
    search_results_page.scroll_down_twice()

    # click first streamer
    streamer_page = search_results_page.select_random_streamer()

    # assert that the video stream is playing
    assert streamer_page is not False , "Streamer page error - cards not displayed"
    assert streamer_page.is_video_playing(40),"FAIL! Video is not streaming"

    # capture video streamer channel info & the screenshot
    streamer_channel = streamer_page.get_streamer_video_channel_name()
    get_logger_fix.info(f"Streamer Channel: {streamer_channel}")
    screenshot_path =  streamer_page.take_screenshot(data.constants.ScreenshotFileNames.STREAMER_PAGE)
    get_logger_fix.info(f"screenshot path:{screenshot_path}")





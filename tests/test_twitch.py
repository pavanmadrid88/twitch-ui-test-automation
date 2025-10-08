import pytest
import data.constants
from pages.home_page import HomePage


@pytest.mark.sanity
def test_open_twitch_and_validate_streamer(page, logger):
    """
    Opens Twitch in Chrome browser (mobile emulation) and validates the Streamer video view.
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
    assert streamer_page is not False, "Streamer page error - cards not displayed"
    assert streamer_page.is_video_playing(30), "FAIL! Video is not streaming"

    # capture video streamer channel info & the screenshot
    streamer_channel = streamer_page.get_streamer_video_channel_name()
    logger.info(f"Streamer Channel: {streamer_channel}")
    screenshot_path = streamer_page.take_screenshot(data.constants.ScreenshotFileNames.STREAMER_PAGE)
    logger.info(f"Streamer view screenshot stored in:{screenshot_path}")

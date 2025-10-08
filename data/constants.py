class Config:
    SCREENSHOT_DIRECTORY = "./artifacts/screenshots/"
    DEFAULT_TIMEOUT_MS = 15000  # 15 seconds default timeout for all waits

class MobileEmulatorDevice:
    """Supported mobile devices for Playwright emulation."""
    PIXEL_5 = "Pixel 5"
    IPHONE_12 = "iPhone 12"


class URL:
    TWITCH_HOME = "https://www.twitch.tv"


class SearchText:
    STARCRAFT_II = "StarCraft II"
    CHESS = "Chess"


class ScreenshotFileNames:
    STREAMER_PAGE = "streamer_page.png"

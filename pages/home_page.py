import data.constants
from pages.base import BasePage
from pages.browse_directory_page import BrowseDirectoryPage

class HomePage(BasePage):
    search_icon = "a[class*='ScInteractableBase'][href*='directory']"

    def open(self):
        self.goto(data.constants.URL.TWITCH_HOME)

    def open_search(self):
        """Click search icon """
        self.safe_click(self.search_icon)
        return BrowseDirectoryPage(self.page)
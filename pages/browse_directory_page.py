import utils.ui_test_utils
from pages.base import BasePage
from pages.search_results_page import SearchResultsPage
from utils.ui_test_utils import get_logger

class BrowseDirectoryPage(BasePage):
    streamer_card = 'a[data-a-target="preview-card-image-link"]'
    search_input = 'input[type="search"]'
    star_craft_ii_search_image_icon = "img[alt = 'StarCraft II']"

    def search_for(self, query: str) -> SearchResultsPage:
        """Fill the query, click search image and return a SearchResultsPage object."""
        self.safe_fill(self.search_input, query)
        self.page.click(self.star_craft_ii_search_image_icon)
        # wait for results page load
        try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            get_logger().warn("Exception while checking the page load state for SearchResults page")
        return SearchResultsPage(self.page)

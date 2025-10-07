import utils.ui_test_utils
from pages.base import BasePage
from pages.search_results_page import SearchResultsPage
from utils.ui_test_utils import get_logger

class BrowseDirectoryPage(BasePage):
    streamer_card = 'a[data-a-target="preview-card-image-link"]'
    search_input = 'input[type="search"]'

    def search_for(self, query: str) -> "SearchResultsPage":
        """Fill the query, click matching game image (case-insensitive), and return a SearchResultsPage."""
        get_logger().info(f"Searching for : {query}")
        self.safe_fill(self.search_input, query)

        # build case-insensitive selector for img[alt]
        locator = self.page.locator(f"img[alt~='{query}'], img[alt='{query}']")
        # fallback: use JS case-insensitive matching
        matching_img = self.page.locator(
            f"xpath=//img[translate(@alt, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')="
            f"'{query.lower()}']"
        )

        try:
            if locator.count() > 0:
                locator.first.click()
            else:
                matching_img.first.click()
        except Exception:
            get_logger().warn(f"No image found matching alt='{query}' (case-insensitive)")

        return SearchResultsPage(self.page)

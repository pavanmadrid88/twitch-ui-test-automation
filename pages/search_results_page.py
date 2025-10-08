import random
from pages.base import BasePage
from pages.streamer_page import StreamerPage


class SearchResultsPage(BasePage):
    streamer_card = "img[class='tw-image']"

    def scroll_down_twice(self):
        """Scroll down two times to load more streamers."""
        self.scroll_down(times=2)

    def select_random_streamer(self):
        """Click a random streamer card from the visible results and returns StreamerPage object.
        If no cards are found , returns False."""
        self.custom_wait(self.streamer_card,10)
        cards = self.page.locator(self.streamer_card)
        count = cards.count()
        if count >= 1:
            index = random.randint(0, count - 1)
            cards.nth(index).click()
            return StreamerPage(self.page)
        else:
            return False
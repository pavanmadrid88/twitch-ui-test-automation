import os
from pages.base import BasePage


class StreamerPage(BasePage):
    VIDEO_PLAYER = 'video'   # Twitch uses a <video> element for the stream
    streamer_channel_name = "div[id*='channel'] h1"
    consent_start_watching_button = "//div[text()='Start Watching']"


    def is_video_playing(self, max_wait: int = 8) -> bool:
        """
        Checks if the Twitch <video> element starts playing.
        Returns True if playing within max_wait seconds, False otherwise.
        """
        self.handle_video_consent()
        def video_check():
            return self.page.evaluate("""
                () => {
                    const v = document.querySelector('video');
                    return !!(v && !v.paused && !v.ended && v.readyState > 2);
                }
            """)

        return self.custom_wait(condition=video_check, max_wait=max_wait)

    def take_screenshot(self, filename="streamer.png"):
        """Take a screenshot of the streamer page."""
        out_path = os.path.join("artifacts", "screenshots", filename)
        self.page.screenshot(path=out_path, full_page=False)
        return out_path

    def handle_video_consent(self):
        video_consent_message = self.custom_wait(element=self.consent_start_watching_button,
                                                 max_wait=5, check_type="visible")
        if video_consent_message:
            self.safe_click(self.consent_start_watching_button)

    def get_streamer_video_channel_name(self):
        return self.get_text(self.streamer_channel_name)

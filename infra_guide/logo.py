"""
Terminal logo rendering helpers for infra-guide.
"""

from contextlib import contextmanager
from importlib import resources
from typing import Iterator, Optional

from rich.text import Text


class LogoRenderer:
    """Render the packaged infra-guide PNG as terminal block art."""

    def __init__(self, no_color: bool = False):
        self.no_color = no_color

    def render(self, max_width: int = 18) -> Optional[Text]:
        """Render the logo to Rich text, or return None when unavailable."""
        if self.no_color:
            return None

        try:
            from PIL import Image
        except Exception:
            return None

        try:
            with self._logo_path() as logo_path:
                image = Image.open(logo_path).convert("RGBA")
        except Exception:
            return None

        alpha = image.getchannel("A")
        bbox = alpha.getbbox()
        if bbox:
            image = image.crop(bbox)

        width, height = image.size
        if width <= 0 or height <= 0:
            return None

        target_width = max(8, min(max_width, width))
        target_height = max(4, round((height / width) * target_width))
        if target_height % 2 != 0:
            target_height += 1

        resampling = getattr(Image, "Resampling", Image)
        image = image.resize((target_width, target_height), resampling.LANCZOS)

        text = Text(no_wrap=True, overflow="ignore")
        for y in range(0, target_height, 2):
            for x in range(target_width):
                top = image.getpixel((x, y))
                bottom = image.getpixel((x, y + 1))
                text.append(self._pixel_char(top, bottom))
            if y + 2 < target_height:
                text.append("\n")
        return text

    @contextmanager
    def _logo_path(self) -> Iterator[str]:
        with resources.path("infra_guide.assets", "infra-guide.png") as path:
            yield str(path)

    def _pixel_char(self, top, bottom) -> Text:
        if top[3] == 0 and bottom[3] == 0:
            return Text(" ")

        if top[3] == 0 and bottom[3] > 0:
            style = f"rgb({bottom[0]},{bottom[1]},{bottom[2]})"
            return Text("▄", style=style)

        if top[3] > 0 and bottom[3] == 0:
            style = f"rgb({top[0]},{top[1]},{top[2]})"
            return Text("▀", style=style)

        style = f"rgb({top[0]},{top[1]},{top[2]}) on " f"rgb({bottom[0]},{bottom[1]},{bottom[2]})"
        return Text("▀", style=style)

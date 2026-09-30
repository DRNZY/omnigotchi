"""Mock & Desktop Simulator Driver for OmniGotchi."""

import os
import sys
import tempfile
from typing import Optional
from PIL import Image


class MockEPaperDriver:
    def __init__(self, width: int = 250, height: int = 122, preview_path: Optional[str] = None):
        self.width = width
        self.height = height
        self.preview_path = preview_path or os.path.join(tempfile.gettempdir(), "omnigotchi_preview.png")
        self.last_image: Optional[Image.Image] = None
        self.refresh_count = 0

    def init(self):
        pass

    def display(self, image: Image.Image, partial: bool = False):
        """Saves preview PNG and updates last_image cache."""
        self.last_image = image.copy()
        self.refresh_count += 1
        try:
            self.last_image.save(self.preview_path, format="PNG")
        except Exception:
            pass

    def render_ascii_terminal(self, image: Optional[Image.Image] = None) -> str:
        """Renders the 1-bit canvas directly in terminal using Unicode half-blocks (▀ ▄ █)."""
        if image is None:
            image = self.last_image
        if image is None:
            return ""

        # Scale image down for terminal preview (e.g. 100 cols by 50 rows)
        term_w = 80
        term_h = 32
        small = image.convert("L").resize((term_w, term_h), Image.Resampling.NEAREST)
        
        output_lines = []
        border_top = "┌" + ("─" * term_w) + "┐"
        border_bot = "└" + ("─" * term_w) + "┘"
        output_lines.append(border_top)

        # 2 vertical pixels per terminal character cell using Unicode half-block (▀)
        for y in range(0, term_h, 2):
            line_chars = ["│"]
            for x in range(term_w):
                top_pixel = small.getpixel((x, y)) < 128  # True = black
                bot_pixel = small.getpixel((x, y + 1)) < 128 if (y + 1 < term_h) else False

                if top_pixel and bot_pixel:
                    line_chars.append("█")
                elif top_pixel and not bot_pixel:
                    line_chars.append("▀")
                elif not top_pixel and bot_pixel:
                    line_chars.append("▄")
                else:
                    line_chars.append(" ")
            line_chars.append("│")
            output_lines.append("".join(line_chars))

        output_lines.append(border_bot)
        return "\n".join(output_lines)

    def clear(self):
        pass

    def sleep(self):
        pass

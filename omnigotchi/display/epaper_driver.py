"""Hardware E-Paper Driver for Waveshare 2.13inch V2/V3/V4 on Raspberry Pi."""

import logging
import time
from typing import Optional
from PIL import Image

logger = logging.getLogger("omnigotchi.epd")


class EPaperHardwareDriver:
    """Hardware abstraction layer for Waveshare 2.13/2.14 e-Paper HATs."""
    
    def __init__(self, model: str = "2in13_V4", width: int = 250, height: int = 122):
        self.model = model
        self.width = width
        self.height = height
        self.epd = None
        self._init_hardware()

    def _init_hardware(self):
        """Attempts to dynamically load waveshare_epd driver modules."""
        try:
            try:
                from omnigotchi.display.waveshare_epd import epd2in13_V4, epd2in13_V3, epd2in13_V2, epd2in13
            except ImportError:
                from waveshare_epd import epd2in13_V4, epd2in13_V3, epd2in13_V2, epd2in13

            if "v4" in self.model.lower():
                self.epd = epd2in13_V4.EPD()
            elif "v3" in self.model.lower():
                self.epd = epd2in13_V3.EPD()
            elif "v2" in self.model.lower():
                self.epd = epd2in13_V2.EPD()
            else:
                self.epd = epd2in13_V4.EPD()

            self.epd.init()
            logger.info(f"Initialized Waveshare e-Paper driver ({self.model})")
        except ImportError as e:
            logger.warning(f"e-Paper dependencies missing (spidev/RPi.GPIO): {e}")
            self.epd = None
        except Exception as e:
            logger.error(f"Failed to initialize EPD hardware: {e}")
            self.epd = None

    def display(self, image: Image.Image, partial: bool = False):
        if self.epd is None:
            return

        try:
            # Rotate / format buffer for hardware orientation
            buf = self.epd.getbuffer(image)
            if partial and hasattr(self.epd, "displayPartial"):
                self.epd.displayPartial(buf)
            else:
                self.epd.display(buf)
        except Exception as e:
            logger.error(f"Hardware display write failed: {e}")

    def clear(self):
        if self.epd:
            try:
                self.epd.Clear(0xFF)
            except Exception:
                pass

    def sleep(self):
        if self.epd:
            try:
                self.epd.sleep()
            except Exception:
                pass

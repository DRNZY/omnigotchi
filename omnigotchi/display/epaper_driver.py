"""Hardware E-Paper Driver for Waveshare 2.13inch V2/V3/V4 on Raspberry Pi."""

import logging
import threading
import time
from typing import Optional
from PIL import Image

logger = logging.getLogger("omnigotchi.epd")


class EPaperHardwareDriver:
    """Hardware abstraction layer for Waveshare 2.13/2.14 e-Paper HATs with thread safety."""

    def __init__(self, model: str = "2in13_V4", width: int = 250, height: int = 122):
        self.model = model
        self.width = width
        self.height = height
        self.epd = None
        self.lock = threading.Lock()
        self.is_in_partial_mode = False
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
            self.is_in_partial_mode = False
            logger.info(f"Initialized Waveshare e-Paper driver ({self.model})")
        except ImportError as e:
            logger.warning(f"e-Paper dependencies missing (spidev/RPi.GPIO): {e}")
            self.epd = None
        except Exception as e:
            logger.error(f"Failed to initialize EPD hardware: {e}")
            self.epd = None

    def display(self, image: Image.Image, partial: bool = False):
        """Serializes writes to the physical EPD display via thread lock."""
        if self.epd is None:
            return

        with self.lock:
            try:
                buf = self.epd.getbuffer(image)
                if partial and hasattr(self.epd, "displayPartial"):
                    self.epd.displayPartial(buf)
                    self.is_in_partial_mode = True
                else:
                    # When switching from partial to full or doing full refresh, re-init full waveform
                    if self.is_in_partial_mode or not partial:
                        try:
                            self.epd.init()
                        except Exception:
                            pass
                    self.epd.display(buf)
                    self.is_in_partial_mode = False
            except Exception as e:
                logger.error(f"Hardware display write failed: {e}")
                self.recover()

    def recover(self):
        """Performs a full hardware reset & clears registers to unfreeze display."""
        if not self.epd:
            return
        logger.warning("Attempting hardware EPD recovery...")
        try:
            self.epd.init()
            self.epd.Clear(0xFF)
            self.is_in_partial_mode = False
            logger.info("EPD hardware recovery succeeded.")
        except Exception as e:
            logger.error(f"EPD recovery failed: {e}")

    def clear(self):
        if self.epd:
            with self.lock:
                try:
                    self.epd.init()
                    self.epd.Clear(0xFF)
                    self.is_in_partial_mode = False
                except Exception:
                    pass

    def sleep(self):
        if self.epd:
            with self.lock:
                try:
                    self.epd.sleep()
                except Exception:
                    pass

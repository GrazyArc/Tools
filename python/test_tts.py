"""Copyright © 2025 Crazygiscool  
""""""All rights reserved.
""""""Unauthorized use is subject to copyright and intellectual property laws."""

"""TTS smoke script.

This file used to run at import time and was picked up by pytest (causing
collection errors on machines without `pyttsx3`). Move runtime code under a
`__main__` guard so test runners don't execute it during collection.
"""

import logging


def main():
    # Import here so running pytest won't fail if pyttsx3 is missing.
    try:
        import pyttsx3
    except Exception as e:
        logging.getLogger().warning('pyttsx3 not available: %s', e)
        return

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        logger.info("Found %d voices: %s", len(voices), [v.id for v in voices])
        engine.setProperty("voice", voices[0].id)
        engine.say("Hello, this is a T T S test.")
        engine.runAndWait()
        logger.info("✅ TTS worked!")
    except Exception:
        logger.exception("❌ TTS failed:")


if __name__ == '__main__':
    main()
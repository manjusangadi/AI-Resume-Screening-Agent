import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.parser import clean_text

def test_clean_text():
    raw_text = "Hello    World! \n\r\n This is a   test. \n\n\n\n Done."
    cleaned = clean_text(raw_text)
    assert "Hello World!" in cleaned
    assert "  " not in cleaned  # Double spaces collapsed
    assert "\n\n\n" not in cleaned  # Excessive newlines collapsed
    assert cleaned.endswith("Done.")

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.groq_service import parse_json_safely, GroqService

def test_parse_json_safely_clean():
    raw = '{"name": "John Doe", "skills": ["Python", "SQL"]}'
    parsed = parse_json_safely(raw)
    assert parsed["name"] == "John Doe"
    assert parsed["skills"] == ["Python", "SQL"]

def test_parse_json_safely_markdown():
    raw = """Here is your JSON response:
```json
{
  "name": "Jane Doe",
  "skills": ["C++", "Docker"]
}
```
Have a good day!"""
    parsed = parse_json_safely(raw)
    assert parsed["name"] == "Jane Doe"
    assert parsed["skills"] == ["C++", "Docker"]

def test_parse_json_safely_invalid():
    raw = '{"name": "John", invalid JSON here}'
    with pytest.raises(ValueError):
        parse_json_safely(raw)

def test_groq_service_availability():
    # If no key is set, it should return False
    service = GroqService(api_key=None)
    # Clear env key temporarily to test detection
    original_key = os.environ.get("GROQ_API_KEY")
    try:
        if "GROQ_API_KEY" in os.environ:
            del os.environ["GROQ_API_KEY"]
        assert GroqService().is_available() is False
    finally:
        if original_key:
            os.environ["GROQ_API_KEY"] = original_key

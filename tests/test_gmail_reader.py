"""Tests for wafle-gmail-reader."""
import pytest
from waflegmailreader.gmail_reader import _extract_code, _HAS_CREDENTIALS


class TestExtractCode:
    def test_english_pattern(self):
        assert _extract_code("Your Meta confirmation code is 123456") == "123456"

    def test_spanish_pattern(self):
        assert _extract_code("código de verificación: 987654") == "987654"

    def test_code_before_label(self):
        assert _extract_code("999731 is your Meta confirmation code") == "999731"

    def test_meta_code_colon(self):
        assert _extract_code("Meta code: 445566") == "445566"

    def test_spanish_codigo_colon(self):
        assert _extract_code("código: 778899") == "778899"

    def test_session_pattern(self):
        assert _extract_code("código de inicio de sesión 112233") == "112233"

    def test_fallback_six_digit(self):
        assert _extract_code("Your code is 554433 and it expires soon") == "554433"

    def test_no_code_returns_none(self):
        assert _extract_code("No numbers here at all") is None

    def test_empty_string(self):
        assert _extract_code("") is None

    def test_short_number_not_extracted(self):
        assert _extract_code("Code is 123") is None

    def test_credentials_loading(self):
        assert isinstance(_HAS_CREDENTIALS, bool)

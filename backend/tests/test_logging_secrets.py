"""Provider API keys travel in query strings, so HTTP client request logging must stay off."""
import logging

import app.main  # noqa: F401  (applies logging configuration)


def test_httpx_request_urls_are_not_logged_at_info():
    for name in ("httpx", "httpcore"):
        assert logging.getLogger(name).getEffectiveLevel() >= logging.WARNING

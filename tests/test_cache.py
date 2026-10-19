"""Unit tests for Redis cache configuration and parsing."""

import os
import sys
import unittest
from pathlib import Path


# Ensure 'main' directory is in sys.path
MAIN_DIR = str(Path(__file__).resolve().parent.parent / "main")
if MAIN_DIR not in sys.path:
    sys.path.insert(0, MAIN_DIR)

from cache import _RedisConfigCache, get_raw_redis_config, parse_redis_config  # noqa: E402


_DEFAULT_PORT = 6379
_CUSTOM_PORT_1 = 6380
_CUSTOM_PORT_2 = 6381
_CUSTOM_DB_2 = 2
_CUSTOM_DB_3 = 3


class RedisConfigTestCase(unittest.TestCase):
    """Test suite for Redis configuration string parsing."""

    def test_parse_empty_or_none(self) -> None:
        """Verify empty or None config strings return default empty configuration."""
        assert parse_redis_config(None) == (None, _DEFAULT_PORT, 0, None)
        assert parse_redis_config("") == (None, _DEFAULT_PORT, 0, None)
        assert parse_redis_config("   ") == (None, _DEFAULT_PORT, 0, None)

    def test_parse_explicit_no_redis(self) -> None:
        """Verify ':6379:0:' expresses no Redis server."""
        assert parse_redis_config(":6379:0:") == (None, _DEFAULT_PORT, 0, None)
        assert parse_redis_config(" :6379:0: ") == (None, _DEFAULT_PORT, 0, None)

    def test_parse_standard_connection(self) -> None:
        """Verify standard formatted Redis config string."""
        raw = "10.51.63.107:6379:0:46b83368-84cb-4dce-9a83-b15ceffc26b0"
        host, port, db, auth = parse_redis_config(raw)
        assert host == "10.51.63.107"
        assert port == _DEFAULT_PORT
        assert db == 0
        assert auth == "46b83368-84cb-4dce-9a83-b15ceffc26b0"

    def test_parse_auth_with_colons(self) -> None:
        """Verify password containing multiple colons is preserved accurately."""
        raw = "10.51.63.107:6379:0:MySuper:Pwd"
        host, port, db, auth = parse_redis_config(raw)
        assert host == "10.51.63.107"
        assert port == _DEFAULT_PORT
        assert db == 0
        assert auth == "MySuper:Pwd"

        raw_multi = "localhost:6380:2:pass:with:many:colons:here:"
        host, port, db, auth = parse_redis_config(raw_multi)
        assert host == "localhost"
        assert port == _CUSTOM_PORT_1
        assert db == _CUSTOM_DB_2
        assert auth == "pass:with:many:colons:here:"

    def test_parse_no_auth(self) -> None:
        """Verify parsing when auth is empty or omitted."""
        assert parse_redis_config("127.0.0.1:6379:0") == ("127.0.0.1", _DEFAULT_PORT, 0, None)
        assert parse_redis_config("127.0.0.1:6379:0:") == ("127.0.0.1", _DEFAULT_PORT, 0, None)

    def test_parse_invalid_format(self) -> None:
        """Verify malformed input returns safe defaults."""
        assert parse_redis_config("malformed") == (None, _DEFAULT_PORT, 0, None)
        assert parse_redis_config("host:port") == (None, _DEFAULT_PORT, 0, None)

    def test_env_override(self) -> None:
        """Verify REDIS_CONFIG environment variable overrides other resolution."""
        _RedisConfigCache.resolved = False
        _RedisConfigCache.raw_config = None
        os.environ["REDIS_CONFIG"] = "192.168.1.1:6381:3:custom_pwd"
        try:
            raw = get_raw_redis_config()
            expected = ("192.168.1.1", _CUSTOM_PORT_2, _CUSTOM_DB_3, "custom_pwd")
            assert parse_redis_config(raw) == expected
        finally:
            os.environ.pop("REDIS_CONFIG", None)
            _RedisConfigCache.resolved = False
            _RedisConfigCache.raw_config = None


if __name__ == "__main__":
    unittest.main()

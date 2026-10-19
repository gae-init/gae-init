"""Cache helpers and authentication attempt rate limiting."""

import logging
import time

import flask
import redis
from google.appengine.api import memcache
from google.cloud import ndb, secretmanager

import config
import util


DEFAULT_TIMEOUT = 3600

logger = logging.getLogger(__name__)

_MIN_CONFIG_PARTS = 3
_MAX_CONFIG_SPLITS = 3


def parse_redis_config(raw_config: str | None) -> tuple[str | None, int, int, str | None]:
    """
    Parse a 'HOST:PORT:DB:AUTH' config string, where PORT defaults to 6379 and DB to 0.

    Returns (host, port, db, auth).
    Supports ':6379:0:' as a valid string indicating no Redis server.
    Allows colons inside the AUTH component.
    """
    if not raw_config:
        return None, 6379, 0, None

    parts = raw_config.strip().split(":", _MAX_CONFIG_SPLITS)
    if len(parts) < _MIN_CONFIG_PARTS:
        logger.warning("Invalid Redis config format: %s", raw_config)
        return None, 6379, 0, None

    host = parts[0].strip() or None
    try:
        port = int(parts[1].strip()) if parts[1].strip() else 6379
    except ValueError:
        port = 6379
    try:
        db = int(parts[2].strip()) if parts[2].strip() else 0
    except ValueError:
        db = 0
    auth = parts[_MIN_CONFIG_PARTS].strip() or None if len(parts) > _MIN_CONFIG_PARTS else None
    return host, port, db, auth


class _RedisConfigCache:
    raw_config: str | None = None
    resolved: bool = False


def get_raw_redis_config() -> str | None:
    """
    Resolve Redis config string once and memorize in-memory.

    Order of priority:
    1. Overriding environment variable 'REDIS_CONFIG'.
    2. Google Secret Manager (using the 'redis-config' secret).
    """
    if _RedisConfigCache.resolved:
        return _RedisConfigCache.raw_config

    # Check for environment variable override
    env_config = util.get_env_str("REDIS_CONFIG", None) or None
    if env_config is not None:
        _RedisConfigCache.raw_config = env_config
        _RedisConfigCache.resolved = True
        return _RedisConfigCache.raw_config

    # Obtain from Secret Manager
    msg = "Secret Manager lookup for 'redis-config'"
    try:
        sm_client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{config.PROJECT_ID}/secrets/redis-config/versions/latest"
        response = sm_client.access_secret_version(request={"name": name})
        logger.info("%s succeeded.", msg)
    except Exception as e:  # noqa: BLE001
        logger.warning("%s failed: %s", msg, e)
    else:
        _RedisConfigCache.raw_config = response.payload.data.decode("utf-8").strip()

    _RedisConfigCache.resolved = True
    return _RedisConfigCache.raw_config


class _RedisState:
    client: redis.Redis | None = None
    global_cache: ndb.RedisCache | None = None
    attempts: int = 0
    max_attempts: int = 3
    last_failure_time: float = 0.0
    cooldown_seconds: float = 60.0


###############################################################################
# Memorystore / Redis Client
###############################################################################
def get_redis_client() -> redis.Redis | None:
    """Return an active redis.Redis client if configured and reachable."""
    if _RedisState.client is not None:
        return _RedisState.client

    host, port, db, auth = parse_redis_config(get_raw_redis_config())
    if not host:
        return None

    now = time.monotonic()
    if _RedisState.attempts >= _RedisState.max_attempts:
        if (now - _RedisState.last_failure_time) < _RedisState.cooldown_seconds:
            return None
        _RedisState.attempts = _RedisState.max_attempts - 1

    msg = f"Redis at {host}:{port} (db={db}){' with auth' if auth else ''}"
    logger.info("Connecting... to %s.", msg)
    try:
        redis_pool = redis.ConnectionPool(
            host=host,
            port=port,
            password=auth,
            max_connections=20,
        )
        client = redis.Redis(
            connection_pool=redis_pool,
            db=db,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
            ssl=False,
        )
        client.ping()
        logger.info("Connected to %s.", msg)
    except (redis.ConnectionError, redis.TimeoutError) as e:
        _RedisState.attempts += 1
        _RedisState.last_failure_time = now
        logger.warning(
            "Could not connect to %s (attempt %d/%d). Error: %s",
            msg,
            _RedisState.attempts,
            _RedisState.max_attempts,
            e,
        )
        return None
    else:
        _RedisState.client = client
        _RedisState.attempts = 0
        return _RedisState.client


def get_ndb_global_cache() -> ndb.RedisCache | None:
    """
    Return an ndb.RedisCache instance if configured and reachable.

    Otherwise returns None (disabling L2 caching, running NDB with L1 cache only).
    """
    if _RedisState.global_cache is not None:
        return _RedisState.global_cache

    client = get_redis_client()
    if client is None:
        return None

    _RedisState.global_cache = ndb.RedisCache(client)
    logger.info("NDB L2 cache enabled via Redis.")
    return _RedisState.global_cache


###############################################################################
# Helpers
###############################################################################
def bump_counter(key: str, time: int = DEFAULT_TIMEOUT, limit: int = 4) -> None:
    """Atomically increment a counter in cache, falling back to memcache."""
    r_client = get_redis_client()
    if r_client:
        try:
            pipe = r_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, time)
            pipe.execute()
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning("Redis bump_counter failed: %s", e)
        else:
            return

    # Fallback to legacy App Engine memcache if available
    client = memcache.Client()
    for _ in range(limit):
        counter = client.gets(key)
        if counter is None:
            client.set(key, 0, time=time)
            counter = 0
        if client.cas(key, counter + 1):
            break


###############################################################################
# Auth Attempts stuff
###############################################################################
def get_auth_attempt_key() -> str:
    """Return the cached key for the current request's client IP."""
    return f"auth_attempt_{flask.request.remote_addr}"


def reset_auth_attempt() -> None:
    """Reset the authentication attempt counter for the current client IP."""
    key = get_auth_attempt_key()
    r_client = get_redis_client()
    if r_client:
        try:
            r_client.delete(key)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning("Redis reset_auth_attempt failed: %s", e)
        else:
            return

    client = memcache.Client()
    client.set(key, 0, time=DEFAULT_TIMEOUT)


def get_auth_attempt() -> int:
    """Get the current count of authentication attempts for the client IP."""
    key = get_auth_attempt_key()
    r_client = get_redis_client()
    if r_client:
        try:
            val = r_client.get(key)
            return int(val) if val is not None else 0
        except (redis.ConnectionError, redis.TimeoutError, ValueError) as e:
            logger.warning("Redis get_auth_attempt failed: %s", e)

    client = memcache.Client()
    return int(client.get(key) or 0)


def bump_auth_attempt() -> None:
    """Increment the authentication attempt counter for the current client IP."""
    bump_counter(get_auth_attempt_key(), limit=config.SIGNIN_RETRY_LIMIT)

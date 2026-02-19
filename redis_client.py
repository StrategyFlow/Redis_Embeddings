"""
Redis connection utilities.

Provides a centralized way to connect to Redis and verify the connection.
"""

import redis
from config import REDIS_HOST, REDIS_PORT


def get_redis_client() -> redis.Redis:
    """
    Create and return a Redis client connection.
    
    Returns:
        redis.Redis: Connected Redis client instance.
        
    Raises:
        redis.ConnectionError: If unable to connect to Redis.
    """
    client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=False)
    
    # Verify connection
    try:
        client.ping()
        print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    except redis.ConnectionError as e:
        print(f"Failed to connect to Redis: {e}")
        print("  Make sure Redis is running (docker-compose up -d)")
        raise
    
    return client


def flush_database(client: redis.Redis, confirm: bool = True) -> bool:
    """
    Flush all data from the current Redis database.
    
    Args:
        client: Redis client instance.
        confirm: If True, prompt for confirmation before flushing.
        
    Returns:
        bool: True if database was flushed, False otherwise.
    """
    if confirm:
        response = input("This will delete ALL data in the database. Continue? (y/N): ")
        if response.lower() != 'y':
            print("  Cancelled.")
            return False
    
    client.flushdb()
    print("Database flushed.")
    return True

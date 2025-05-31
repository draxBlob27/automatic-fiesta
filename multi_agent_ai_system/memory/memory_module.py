import redis
import json
from datetime import datetime
import logging
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryModule:
    def __init__(self, host, port, password):
        try:
            self.r = redis.StrictRedis(host=host, port=port, decode_responses=True, password=password)
            # Test connection
            if not self.r.ping():
                raise ConnectionError("Redis server not responding")
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise e

    def store_context(self, thread_id: str, key: str, value: Any):
        """
        Store a single key-value pair under a thread ID.
        Value is JSON serialized.
        """
        try:
            self.r.hset(f"THREAD:{thread_id}", key, json.dumps(value))
            logger.debug(f"Stored context: THREAD:{thread_id} {key}={value}")
        except Exception as e:
            logger.error(f"Error storing context for {thread_id}: {e}")

    def store_context_bulk(self, thread_id: str, data: Dict[str, Any]):
        """
        Store multiple key-value pairs at once under a thread ID.
        """
        try:
            json_data = {k: json.dumps(v) for k, v in data.items()}
            self.r.hset(f"THREAD:{thread_id}", mapping=json_data)
            logger.debug(f"Stored bulk context for THREAD:{thread_id}: {data}")
        except Exception as e:
            logger.error(f"Error storing bulk context for {thread_id}: {e}")

    def get_context(self, thread_id: str, key: str) -> Optional[Any]:
        """
        Retrieve a single value by key under a thread ID.
        Returns None if key doesn't exist.
        """
        try:
            value = self.r.hget(f"THREAD:{thread_id}", key)
            if value is not None:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Error retrieving context for {thread_id} key {key}: {e}")
        return None

    def get_full_context(self, thread_id: str) -> Dict[str, Any]:
        """
        Retrieve all key-values stored under a thread ID.
        """
        try:
            raw_data = self.r.hgetall(f"THREAD:{thread_id}")
            return {k: json.loads(v) for k, v in raw_data.items()}
        except Exception as e:
            logger.error(f"Error retrieving full context for {thread_id}: {e}")
            return {}

    def log_event(self, thread_id: str, event_type: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Log an event for a thread, stored as a Redis list entry.
        """
        log_entry = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        try:
            self.r.rpush(f"THREAD:{thread_id}:logs", json.dumps(log_entry))
            logger.debug(f"Logged event for THREAD:{thread_id}: {event_type}")
        except Exception as e:
            logger.error(f"Error logging event for {thread_id}: {e}")

    def get_logs(self, thread_id: str) -> list:
        """
        Retrieve all logs for a thread.
        """
        try:
            logs = self.r.lrange(f"THREAD:{thread_id}:logs", 0, -1)
            return [json.loads(log) for log in logs]
        except Exception as e:
            logger.error(f"Error retrieving logs for {thread_id}: {e}")
            return []

    def clear_thread_data(self, thread_id: str):
        """
        Clear all stored data and logs for a thread
        """
        try:
            self.r.delete(f"THREAD:{thread_id}")
            self.r.delete(f"THREAD:{thread_id}:logs")
            logger.info(f"Cleared data for THREAD:{thread_id}")
        except Exception as e:
            logger.error(f"Error clearing data for {thread_id}: {e}")


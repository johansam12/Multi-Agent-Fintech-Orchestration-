import json
import redis
from typing import Dict, Any

class RedisStateManager:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        # Initialize Redis client connection
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def save_session_state(self, session_id: str, state: Dict[str, Any], expire_seconds: int = 3600):
        """Saves the current workflow state into Redis with a TTL (Time-To-Live)."""
        key = f"workflow:session:{session_id}"
        # Serialize dict to JSON string for storage
        self.client.setex(key, expire_seconds, json.dumps(state))

    def get_session_state(self, session_id: str) -> Dict[str, Any] | None:
        """Retrieves an active workflow state from Redis cache."""
        key = f"workflow:session:{session_id}"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def append_audit_scratchpad(self, session_id: str, log_entry: str):
        """Pushes real-time agent execution notes into a Redis list."""
        list_key = f"workflow:scratchpad:{session_id}"
        self.client.rpush(list_key, log_entry)
        self.client.expire(list_key, 3600)

    def get_audit_scratchpad(self, session_id: str) -> list:
        """Fetches all temporary scratchpad logs for a session."""
        list_key = f"workflow:scratchpad:{session_id}"
        return self.client.lrange(list_key, 0, -1)
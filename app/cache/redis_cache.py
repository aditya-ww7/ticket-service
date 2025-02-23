from typing import Optional, Dict, Any
import json
import hashlib
from redis import Redis


class RedisCache:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.request_cache_ttl = 3600  # 1 hour

    def get_cached_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        cached = self.redis.hgetall(f"request:{request_id}")
        if not cached:
            return None

        try:
            return {
                "hash": cached[b"hash"].decode() if isinstance(cached[b"hash"], bytes) else cached[b"hash"],
                "data": json.loads(cached[b"data"].decode() if isinstance(cached[b"data"], bytes) else cached[b"data"])
            }
        except (KeyError, json.JSONDecodeError):
            return None

    def generate_request_hash(self, data: Dict[str, Any]) -> str:
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(sorted_data.encode()).hexdigest()

    def cache_request(self, request_id: str, request_data: Dict[str, Any]) -> None:
        request_hash = self.generate_request_hash(request_data)
        self.redis.hset(
            f"request:{request_id}",
            mapping={
                "hash": request_hash,
                "data": json.dumps(request_data)
            }
        )
        self.redis.expire(f"request:{request_id}", self.request_cache_ttl)

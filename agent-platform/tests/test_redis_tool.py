from tools.base import ToolRequest
from tools.redis_store import RedisConnectionConfig, RedisKVStore
from tools.redis_tool import RedisKVTool


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.expires = {}

    def ping(self):
        return True

    def set(self, key, value, ex=None):
        self.data[key] = value
        self.expires[key] = ex
        return True

    def get(self, key):
        return self.data.get(key)

    def delete(self, key):
        existed = key in self.data
        self.data.pop(key, None)
        return 1 if existed else 0

    def ttl(self, key):
        if key not in self.data:
            return -2
        return self.expires.get(key) or -1


def build_store() -> RedisKVStore:
    return RedisKVStore(
        RedisConnectionConfig(
            host="localhost",
            port=6379,
            key_prefix="test-agent",
            default_ttl_seconds=60,
        ),
        client=FakeRedis(),
    )


def test_redis_store_set_get_delete_json():
    store = build_store()
    key = store.set_json("session-1", {"x": 1})
    assert key == "test-agent:session-1"
    assert store.get_json("session-1") == {"x": 1}
    assert store.delete("session-1") == 1
    assert store.get_json("session-1") is None


def test_redis_tool_set_get_ttl_delete():
    tool = RedisKVTool(build_store())

    set_result = tool.run(
        ToolRequest(
            query="hello",
            session_id="s1",
            params={
                "action": "set",
                "key": "k1",
                "value": {"message": "hello"},
                "ttl_seconds": 30,
            },
        )
    )
    assert set_result.success is True

    get_result = tool.run(
        ToolRequest(
            query="",
            session_id="s1",
            params={"action": "get", "key": "k1"},
        )
    )
    assert get_result.metadata["value"] == {"message": "hello"}

    ttl_result = tool.run(
        ToolRequest(
            query="",
            session_id="s1",
            params={"action": "ttl", "key": "k1"},
        )
    )
    assert ttl_result.metadata["ttl"] == 30

    delete_result = tool.run(
        ToolRequest(
            query="",
            session_id="s1",
            params={"action": "delete", "key": "k1"},
        )
    )
    assert delete_result.metadata["deleted"] == 1
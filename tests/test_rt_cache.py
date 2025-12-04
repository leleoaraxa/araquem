from app.cache import rt_cache


def test_get_config_version_is_memoized():
    rt_cache.get_config_version.cache_clear()
    first = rt_cache.get_config_version()
    second = rt_cache.get_config_version()
    assert first == second
    assert first.startswith("cfg-")


def test_make_cache_key_includes_config_version(monkeypatch):
    monkeypatch.setattr(rt_cache, "get_config_version", lambda: "cfg-testtoken")
    key = rt_cache.make_cache_key("build", "scope", "entity", {"x": 1})
    assert key.startswith("araquem:build:cfg-testtoken:scope:entity:")

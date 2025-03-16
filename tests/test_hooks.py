# tests/test_hooks.py

import pytest
from engine.hooks import HookManager

def test_hook_manager():
    call_history = []

    def hook_callback(*args, **kwargs):
        call_history.append((args, kwargs))

    hm = HookManager()
    hm.register_hook("testEvent", hook_callback)
    hm.run_hook("testEvent", 42, key="value")

    assert len(call_history) == 1
    args, kwargs = call_history[0]
    assert args[0] == 42
    assert kwargs["key"] == "value"

def test_hook_unregister():
    call_history = []

    def hook_callback(*args, **kwargs):
        call_history.append("called")

    hm = HookManager()
    hm.register_hook("testEvent", hook_callback)
    hm.unregister_hook("testEvent", hook_callback)
    hm.run_hook("testEvent")
    assert len(call_history) == 0
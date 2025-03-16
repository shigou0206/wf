# engine/hooks.py

from typing import Callable, Dict, List, Any

class HookManager:
    """
    HookManager 用于管理钩子回调函数。
    你可以通过 register_hook() 为特定事件注册回调，
    在 run_hook() 时依次调用所有注册的回调，并传入相关参数。
    """

    def __init__(self):
        self._hooks: Dict[str, List[Callable[..., None]]] = {}

    def register_hook(self, event_name: str, callback: Callable[..., None]) -> None:
        """
        注册一个钩子回调函数。
        
        :param event_name: 钩子事件名称，例如 "workflowExecuteBefore"、"nodeExecuteAfter" 等
        :param callback: 回调函数，接收可选参数
        """
        if event_name not in self._hooks:
            self._hooks[event_name] = []
        self._hooks[event_name].append(callback)

    def unregister_hook(self, event_name: str, callback: Callable[..., None]) -> None:
        """
        注销某个钩子回调。
        """
        if event_name in self._hooks:
            self._hooks[event_name] = [cb for cb in self._hooks[event_name] if cb != callback]

    def run_hook(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """
        运行指定事件的所有钩子回调函数。
        
        :param event_name: 事件名称
        :param args: 位置参数，将传递给回调函数
        :param kwargs: 关键字参数，将传递给回调函数
        """
        if event_name not in self._hooks:
            return

        for callback in self._hooks[event_name]:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[HookManager] Error in hook '{event_name}': {e}")
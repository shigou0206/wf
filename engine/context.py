from typing import Any, Dict, List, Optional


class NodeExecutionContext:
    """
    为节点执行时提供的上下文：包括输入数据、全局配置、执行模式等。
    """
    def __init__(
        self,
        node_name: str,
        input_data: Optional[List[Dict[str, Any]]],
        mode: str = "manual",
        global_config: Optional[Dict[str, Any]] = None,
    ):
        self.node_name = node_name
        self.input_data = input_data or []
        self.mode = mode
        if global_config is None:
            self.global_config = {}
        else:
            self.global_config = global_config

    def __repr__(self):
        return f"<NodeExecutionContext node={self.node_name}, input_items={len(self.input_data)}>"

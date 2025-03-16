import time
from typing import Any, Dict, List, Optional
from enum import Enum, auto

class ExecutionStatus(Enum):
    NEW = auto()
    RUNNING = auto()
    WAITING = auto()
    SUCCESS = auto()
    CANCELED = auto()
    ERROR = auto()


class ExecutionError(Exception):
    """
    执行过程中的错误类，可以存储更多上下文。
    """
    def __init__(self, message: str, node_name: Optional[str] = None):
        super().__init__(message)
        self.node_name = node_name


class NodeResult:
    """
    单个节点执行的结果：
      - data: 二维列表，data[outputIndex] = list of items
              或者 None 表示无输出
      - error: 如果执行出错，可在此存储错误信息

    多输出的关键：
      data = [
        [ {item}, {item}, ... ],  # outputIndex=0
        [ {item}, {item}, ... ],  # outputIndex=1
        ...
      ]
    """
    def __init__(self, data: Optional[List[List[Dict[str, Any]]]] = None, error: Optional[Exception] = None):
        self.data = data
        self.error = error

    def __repr__(self):
        return f"<NodeResult data={self.data}, error={self.error}>"
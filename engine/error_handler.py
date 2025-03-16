import time
from typing import Any, Dict

from .models import NodeResult, ExecutionError
from graph.workflow import Node

class ErrorPolicy:
    """
    节点错误策略。可扩展:
      - STOP_WORKFLOW
      - CONTINUE_ON_FAIL
      - RETRY_ON_FAIL
      - ERROR_OUTPUT
    """
    STOP_WORKFLOW = "stopWorkflow"
    CONTINUE_ON_FAIL = "continueOnFail"
    RETRY_ON_FAIL = "retryOnFail"
    ERROR_OUTPUT = "errorOutput"

class ErrorHandler:
    """
    根据节点配置 (parameters 中) 的错误策略，对执行错误做相应处理.
    """

    def __init__(self, node: Node, mode: str = "manual"):
        self.node = node
        self.mode = mode
        self.policy = self._fetch_error_policy_from_node()
        self.max_retries = self.node.parameters.get("maxRetries", 0)
        self.retry_delay = self.node.parameters.get("retryDelay", 0)

    def _fetch_error_policy_from_node(self) -> str:
        """
        读取 node.parameters 中的 "onError" 配置, 返回 policy 字符串, 
        若无配置, 默认 "stopWorkflow".
        """
        return self.node.parameters.get("onError", ErrorPolicy.STOP_WORKFLOW)

    def handle_error(
        self,
        error: Exception,
        current_try: int,
        run_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        当节点执行出错时, 处理错误 (比如重试, 或继续, 或停止).
        这里返回一个 dict, 说明接下来应做什么:
          e.g. { "action": "retry", "wait": <秒> }
               { "action": "stop", "error": <error> }
               { "action": "continue", "items": <some fallback items> }
               { "action": "errorOutput", "errorItem": {...} }
        executor.py 根据它做相应动作.
        """
        if self.policy == ErrorPolicy.CONTINUE_ON_FAIL:
            return {
                "action": "continue",
                "items": [{
                    "error": str(error),
                    "errorType": type(error).__name__
                }]
            }
        elif self.policy == ErrorPolicy.RETRY_ON_FAIL:
            if current_try < self.max_retries:
                return {
                    "action": "retry",
                    "wait": self.retry_delay
                }
            else:
                return {
                    "action": "stop",
                    "error": error
                }
        elif self.policy == ErrorPolicy.ERROR_OUTPUT:
            return {
                "action": "errorOutput",
                "errorItem": {
                    "message": str(error),
                    "errorType": type(error).__name__
                }
            }
        else:
            return {
                "action": "stop",
                "error": error
            }
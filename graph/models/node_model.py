from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


class OnError(str, Enum):
    CONTINUE_ERROR_OUTPUT = "continueErrorOutput"
    CONTINUE_REGULAR_OUTPUT = "continueRegularOutput"
    STOP_WORKFLOW = "stopWorkflow"


@dataclass
class NodeCredentialsDetail:
    """
    Dataclass 对应原先的 NodeCredentialsDetail TypedDict
    """
    name: str
    id: Optional[str] = None


# 映射：credentials_key -> NodeCredentialsDetail
NodeCredentials = Dict[str, NodeCredentialsDetail]


@dataclass
class WorkflowNode:
    """
    Dataclass 版本的 WorkflowNode，替代 TypedDict。
    Fields with default=None 等价于可选字段。
    """

    id: Optional[str] = None
    name: Optional[str] = None
    type_version: Optional[int] = None
    node_type: Optional[str] = None
    position: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    disabled: Optional[bool] = None
    notes: Optional[str] = None
    notes_in_flow: Optional[bool] = None
    retry_on_fail: Optional[bool] = None
    max_tries: Optional[int] = None
    wait_between_tries: Optional[int] = None
    always_output_data: Optional[bool] = None
    execute_once: Optional[bool] = None
    on_error: Optional[OnError] = None
    continue_on_fail: Optional[bool] = None
    parameters: object = field(default_factory=lambda: {})
    credentials: Optional[NodeCredentials] = None
    webhook_id: Optional[str] = None
    extends_credential: Optional[str] = None


# 映射： node_key -> WorkflowNode
WorkflowNodes = Dict[str, WorkflowNode]
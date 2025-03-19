from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Union, List, Literal
from .utils import ConnectionType
from .node_type import NodeConnectionType


class OnError(str, Enum):
    CONTINUE_ERROR_OUTPUT = "continueErrorOutput"
    CONTINUE_REGULAR_OUTPUT = "continueRegularOutput"
    STOP_WORKFLOW = "stopWorkflow"


@dataclass
class NodeCredentialsDetail:
    name: str
    id: Optional[str] = None


NodeCredentials = Dict[str, NodeCredentialsDetail]


@dataclass
class WorkflowNode:
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

@dataclass
class ConnectedNode:
    """
    Pythonic class版本，与 TypeScript IConnectedNode 等价。
    """
    name: str
    indicies: List[int]
    depth: int

@dataclass
class NodePropertyOptions:
    name: str
    value: Union[str, int, bool]
    action: Optional[str] = None
    description: Optional[str] = None
    output_connection_type: Optional[ConnectionType] = None


CategoryType = Literal["error"]

@dataclass
class NodeOutputConfiguration:
    """
    Pythonic dataclass 等价于 TypeScript: {
        category?: 'error',
        displayName?: string,
        maxConnections?: number,
        required?: boolean,
        type: NodeConnectionType
    }
    """
    category: Optional[CategoryType] = None
    display_name: Optional[str] = None
    max_connections: Optional[int] = None
    required: Optional[bool] = None
    type: Optional[NodeConnectionType] = None
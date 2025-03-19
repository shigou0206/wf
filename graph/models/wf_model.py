from dataclasses import dataclass, field
from typing import Optional, Any

from .node_model import WorkflowNode, Nodes
from .connection_model import Connections
from .node_type import NodeTypes
from .data_model import WorkflowSettings, PinData


@dataclass
class WorkflowParameters:
    id: Optional[str] = None
    name: Optional[str] = None
    nodes: list[WorkflowNode] = field(default_factory=list)
    connections: Optional[Connections] = None
    active: bool = False
    node_types: Optional[NodeTypes] = None
    static_data: Optional[Any] = None
    settings: Optional[WorkflowSettings] = None
    pin_data: Optional[PinData] = None

class Workflow:
    """
    Python 等价实现:
    - fields 对应 TS 类中的属性
    - 使用 __init__ 做构造逻辑 (包括 nodes 和 staticData 的初始化)
    """

    id: str
    name: Optional[str] = None
    nodes: Nodes = field(default_factory=dict)
    connections_by_source_node: Connections = field(default_factory=dict)
    connections_by_destination_node: Connections = field(default_factory=dict)
    node_types: NodeTypes = None
    expression: str = None
    active: bool = False
    settings: WorkflowSettings = field(default_factory=dict)
    timezone: str = ""
    static_data: Any = field(default_factory=dict)
    test_static_data: Optional[Any] = None
    pin_data: Optional[PinData] = None

from dataclasses import dataclass, field
from typing import Optional, Any

from .node_model import WorkflowNode, WorkflowNodes
from .connection_model import Connections
from .node_type import NodeTypes
from .data_model import WorkflowSettings, PinData
from .utils import get_node_parameters, get_connections_by_destination, GlobalState


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
    def __init__(self, parameters: WorkflowParameters):
        self.id: str = parameters.id or ""
        self.name: Optional[str] = parameters.name
        self.node_types: Optional[NodeTypes] = parameters.node_types
        self.nodes: WorkflowNodes = {}
        for node in parameters.nodes:
            self.nodes[node.name] = node
            node_type = self.node_types.get_by_name_and_version(node.type, node.type_version) if self.node_types else None
            if node_type:
                node.parameters = get_node_parameters(node_type.description.properties, node.parameters, node)

        self.connections_by_destination = get_connections_by_destination(parameters.connections)
        self.active = parameters.active
        self.static_data = parameters.static_data
        self.settings = parameters.settings
        self.pin_data = parameters.pin_data
        self.timezone = self.settings.timezone if self.settings else GlobalState.get_global_state().get("defaultTimezone")



        
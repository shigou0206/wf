from typing import TypedDict, Union, Literal, Optional, List, Dict, Any
from dataclasses import dataclass, field
from .node_model import NodeInputConfiguration, NodeOutputConfiguration
from .connection_model import ConnectionType

ThemeIconColor = Literal[
    "gray",
    "black",
    "blue",
    "light-blue",
    "dark-blue",
    "orange",
    "orange-red",
    "pink-red",
    "red",
    "light-green",
    "green",
    "dark-green",
    "azure",
    "purple",
    "crimson",
]

class ThemedStrDict(TypedDict):
    light: str
    dark: str

ThemedString = Union[str, ThemedStrDict]

Icon = ThemedString

class CodexData(TypedDict, total=False):
    details: Optional[str]

@dataclass
class NodeTypeBaseDescription:
    displayName: str
    name: str
    group: list[str]
    description: str
    defaultVersion: int

    icon: Optional[Icon] = None
    iconColor: Optional[ThemeIconColor] = None
    iconUrl: Optional[ThemedString] = None
    badgeIconUrl: Optional[ThemedString] = None
    documentationUrl: Optional[str] = None
    subtitle: Optional[str] = None
    codex: Optional[CodexData] = None
    parameterPane: Optional[Literal["wide"]] = None
    hidden: Optional[bool] = False
    usableAsTool: Optional[bool] = False

@dataclass
class NodeTypeDescription(NodeTypeBaseDescription):
    version: Union[int, List[int]]
    defaults: Optional[Dict[str, Any]] = None
    event_trigger_description: Optional[str] = None
    activation_message: Optional[str] = None
    inputs: Union[List[Union[ConnectionType, NodeInputConfiguration]], str]
    required_inputs: Optional[Union[str, List[int], int]] = None
    input_names: Optional[List[str]] = None
    outputs: Union[List[Union[ConnectionType, NodeOutputConfiguration]], str]
    output_names: Optional[List[str]] = None
    properties: List[Any]
    max_nodes: Optional[int] = None
    polling: Optional[bool] = None
    supports_cors: Optional[bool] = None
    request_defaults: Optional[Dict[str, Any]] = None
    request_operations: Optional[Dict[str, Any]] = None
    translation: Optional[Dict[str, object]] = None
    mock_manual_execution: Optional[bool] = None
    extends_credential: Optional[str] = None
    hints: Optional[List[Any]] = None
    _load_options_methods: Optional[List[str]] = None

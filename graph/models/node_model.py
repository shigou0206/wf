from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Union, List, Any
from .connection_model import ConnectionType
from .data_model import DisplayOptions
from .http_model import HttpRequestOptions, NodeRequestOutput


class OnError(str, Enum):
    CONTINUE_ERROR_OUTPUT = "continueErrorOutput"
    CONTINUE_REGULAR_OUTPUT = "continueRegularOutput"
    STOP_WORKFLOW = "stopWorkflow"

    @classmethod
    def from_string(cls, value: str) -> "OnError":
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"Invalid OnError value: {value}")


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
    type: Optional[str] = None
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
    parameters: Dict[str, Union[str, int, bool, list, dict]] = field(default_factory=dict)
    credentials: Optional[NodeCredentials] = None
    webhook_id: Optional[str] = None
    extends_credential: Optional[str] = None


WorkflowNodes = Dict[str, WorkflowNode]

@dataclass
class ConnectedNode:
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


class CategoryType(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    SUCCESS = "success"

    @classmethod
    def from_string(cls, value: str) -> "CategoryType":
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"Invalid CategoryType value: {value}")
    
@dataclass
class NodeInputConfiguration:
    type: ConnectionType
    category: Optional[str] = None
    display_name: Optional[str] = None
    required: Optional[bool] = None
    filter: Optional[List[str]] = None
    max_connections: Optional[int] = None

@dataclass
class NodeOutputConfiguration:
    category: Optional[CategoryType] = None
    display_name: Optional[str] = None
    max_connections: Optional[int] = None
    required: Optional[bool] = None
    type: Optional[ConnectionType] = None

class NodePropertyTypes(str, Enum):
    BOOLEAN = "boolean"
    BUTTON = "button"
    COLLECTION = "collection"
    COLOR = "color"
    DATETIME = "dateTime"
    FIXED_COLLECTION = "fixedCollection"
    HIDDEN = "hidden"
    JSON = "json"
    NOTICE = "notice"
    MULTI_OPTIONS = "multiOptions"
    NUMBER = "number"
    OPTIONS = "options"
    STRING = "string"
    CREDENTIALS_SELECT = "credentialsSelect"
    RESOURCE_LOCATOR = "resourceLocator"
    CURL_IMPORT = "curlImport"
    RESOURCE_MAPPER = "resourceMapper"
    FILTER = "filter"
    ASSIGNMENT_COLLECTION = "assignmentCollection"
    CREDENTIALS = "credentials"
    WORKFLOW_SELECTOR = "workflowSelector"

    @classmethod
    def from_string(cls, value: str) -> "NodePropertyTypes":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Invalid NodePropertyType: {value}")
        
@dataclass
class EntryType:
    selectable: Optional[bool] = None
    hidden: Optional[bool] = None
    queryable: Optional[bool] = None
    data: Optional[Dict[str, Union[HttpRequestOptions, NodeRequestOutput]]] = None


NodePropertyTypeOptions = Dict[str, Any]

@dataclass
class NodeProperties:
    display_name: str
    name: str
    type: NodePropertyTypes
    default: Optional[Any] = None
    type_options: Optional[NodePropertyTypeOptions] = None
    description: Optional[str] = None
    hint: Optional[str] = None
    disabled_options: Optional[DisplayOptions] = None
    display_options: Optional[DisplayOptions] = None
    options: Optional[List[Union[NodePropertyOptions, "NodeProperties"]]] = None
    placeholder: Optional[str] = None
    is_node_setting: Optional[bool] = False
    no_data_expression: Optional[bool] = False
    required: Optional[bool] = False
    credential_types: Optional[List[str]] = None
    modes: Optional[List[str]] = None
    requires_data_path: Optional[str] = None
    do_not_inherit: Optional[bool] = False
    validate_type: Optional[str] = None
    ignore_validation_during_execution: Optional[bool] = False


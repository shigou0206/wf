from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Callable,  
    Union,
    Awaitable,
)

from .description_model import NodeTypeDescription, NodeTypeBaseDescription
from .data_model import NodeExecutionData, NodeOutput
from .utils import CloseFunction
from .func_protocol import *

ResourceMapperFields = Any
NodeParameterValueType = Any
NodePropertyOptions = Any
NodeListSearchResult = Any
CredentialTestFunction = Callable[..., Any]

WebhookType = str
WebhookSetupMethodNames = str

ManualTriggerFunction = Callable[[], Awaitable[None]]
ManualTriggerResponse = Awaitable[List[List[NodeExecutionData]]]

@dataclass
class TriggerResponse:
    close_function: Optional[CloseFunction] = None
    manual_trigger_function: Optional[ManualTriggerFunction] = None
    manual_trigger_response: Optional[ManualTriggerResponse] = None

@dataclass
class WebhookResponse:
    workflow_data: Optional[List[List[NodeExecutionData]]] = None
    webhook_response: Any = None
    no_webhook_response: Optional[bool] = None

@dataclass
class SupplyData:
    response: Any
    metadata: Optional[Dict[str, Any]] = None
    closeFunction: Optional[CloseFunction] = None


@dataclass
class NodePropertyOptions:
    name: Optional[str] = None
    value: Optional[str] = None

@dataclass
class NodeListSearchItems(NodePropertyOptions):
    icon: Optional[str] = None
    url: Optional[str] = None

@dataclass
class NodeListSearchResult:
    results: List[NodeListSearchItems] = field(default_factory=list)
    pagination_token: Any = None


class NodeType(ABC):
    def __init__(self, description: NodeTypeDescription):
        self.description = description

    def supply_data(
        self,
        context: SupplyDataFunctions,
        item_index: int
    ) -> SupplyData:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement supply_data().")

    def execute(
        self,
        context: ExecuteFunctions
    ) -> NodeOutput:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement execute().")


    def poll(
        self,
        context: PollFunctions
    ) -> Optional[List[List[NodeExecutionData]]]:
        return None

    def trigger(
        self,
        context: TriggerFunctions
    ) -> Optional[TriggerResponse]:
        return None

    def webhook(
        self,
        context: WebhookFunctions
    ) -> WebhookResponse:
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement webhook().")


    def methods_load_options(self) -> Dict[str, Callable[[LoadOptionsFunctions], List[NodePropertyOptions]]]:
        return {}

    def methods_list_search(self) -> Dict[str, Callable[[LoadOptionsFunctions, Optional[str], Optional[str]], NodeListSearchResult]]:
        return {}

    def methods_credential_test(self) -> Dict[str, CredentialTestFunction]:
        return {}

    def methods_resource_mapping(self) -> Dict[str, Callable[[LoadOptionsFunctions], ResourceMapperFields]]:
        return {}

    def methods_local_resource_mapping(self) -> Dict[str, Callable[[LocalLoadOptionsFunctions], ResourceMapperFields]]:
        return {}

    def methods_action_handler(self) -> Dict[str, Callable[[LoadOptionsFunctions, Union[dict, str, None]], NodeParameterValueType]]:
        return {}

    def methods(self) -> Dict[str, Any]:
        return {
            "loadOptions": self.methods_load_options(),
            "listSearch": self.methods_list_search(),
            "credentialTest": self.methods_credential_test(),
            "resourceMapping": self.methods_resource_mapping(),
            "localResourceMapping": self.methods_local_resource_mapping(),
            "actionHandler": self.methods_action_handler(),
        }

    def webhook_methods(self) -> Dict[WebhookType, Dict[WebhookSetupMethodNames, Callable[[HookFunctions], bool]]]:
        return {}

    def custom_operations(self) -> Dict[str, Dict[str, Callable[[ExecuteFunctions], NodeOutput]]]:
        return {}
    
class VersionedNodeType(ABC):
    @property
    @abstractmethod
    def node_versions(self) -> Dict[int, NodeType]:
        pass

    @property
    @abstractmethod
    def current_version(self) -> int:
        pass

    @property
    @abstractmethod
    def description(self) -> NodeTypeBaseDescription:
        pass

    @abstractmethod
    def get_node_type(self, version: Optional[int] = None) -> NodeType:
        pass

class NodeTypes(ABC):
    @abstractmethod
    def get_by_name(self, node_type: str) -> Union[NodeType, VersionedNodeType]:
        pass

    @abstractmethod
    def get_by_name_and_version(self, node_type: str, version: Optional[int] = None) -> NodeType:
        pass

    @abstractmethod
    def get_known_types(self) -> Any:
        pass
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

# 下列类或 Protocol 仅占位, 你可以做更细化的定义:

# 数据、结果、配置等类型:
ResourceMapperFields = Any
NodeParameterValueType = Any
NodePropertyOptions = Any
NodeListSearchResult = Any
CredentialTestFunction = Callable[..., Any]

# WebhookType, WebhookSetupMethodNames 在 TS 中可能是字符串枚举，这里简单用 str
WebhookType = str
WebhookSetupMethodNames = str

ManualTriggerFunction = Callable[[], Awaitable[None]]
ManualTriggerResponse = Awaitable[List[List[NodeExecutionData]]]

@dataclass
class TriggerResponse:
    """
    与 TypeScript 的 ITriggerResponse 等价，但使用 dataclass。
    若不传对应字段则默认为 None。
    """
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
    """
    对应 TypeScript 中的:

      export interface SupplyData {
        metadata?: IDataObject;       # -> metadata: Optional[Dict[str, Any]]
        response: unknown;            # -> response: Any (required)
        closeFunction?: CloseFunction # -> Optional[CloseFunction]
      }
    """
    response: Any
    metadata: Optional[Dict[str, Any]] = None
    closeFunction: Optional[CloseFunction] = None


@dataclass
class NodePropertyOptions:
    name: Optional[str] = None
    value: Optional[str] = None
    # 若有更多必填字段，可去掉 Optional 并不给默认值

@dataclass
class NodeListSearchItems(NodePropertyOptions):
    icon: Optional[str] = None
    url: Optional[str] = None

@dataclass
class NodeListSearchResult:
    results: List[NodeListSearchItems] = field(default_factory=list)
    pagination_token: Any = None

#
# 2. 用抽象基类表示 "INodeType"
#

class NodeType(ABC):
    """
    Python 中的抽象基类，模拟 TypeScript `INodeType` 的结构和可选方法。
    子类可以选择性实现 supply_data、execute、poll、trigger、webhook 等方法。
    """

    def __init__(self, description: NodeTypeDescription):
        self.description = description

    #
    # === 对应 supplyData?(this: ISupplyDataFunctions, itemIndex: number) ===
    #
    def supply_data(
        self,
        context: SupplyDataFunctions,
        item_index: int
    ) -> SupplyData:
        """
        如果节点需要提供数据，可在子类中 override。
        默认抛出 NotImplementedError，表示未实现。
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement supply_data().")

    #
    # === 对应 execute?(this: IExecuteFunctions) ===
    #
    def execute(
        self,
        context: ExecuteFunctions
    ) -> NodeOutput:
        """
        如果节点需要执行逻辑，可在子类中 override。
        默认抛出 NotImplementedError。
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement execute().")

    #
    # === 对应 poll?(this: IPollFunctions) ===
    #
    def poll(
        self,
        context: PollFunctions
    ) -> Optional[List[List[NodeExecutionData]]]:
        """
        如果节点需要轮询，可在子类中 override。
        返回 None 表示未实现或无结果。
        """
        return None

    #
    # === 对应 trigger?(this: ITriggerFunctions) ===
    #
    def trigger(
        self,
        context: TriggerFunctions
    ) -> Optional[TriggerResponse]:
        """
        如果节点需要触发机制，可在子类中 override。
        返回 None 表示未实现。
        """
        return None

    #
    # === 对应 webhook?(this: IWebhookFunctions) ===
    #
    def webhook(
        self,
        context: WebhookFunctions
    ) -> WebhookResponse:
        """
        如果节点实现 webhook，可在子类中 override。
        默认抛出异常。
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement webhook().")

    #
    # === 对应 methods?: { ... } ===
    # 在 TS 是个可选对象/字典; 在 Python, 常见做法是用方法或属性返回一个字典。
    #
    # 你可以把 loadOptions、listSearch 等做成单独方法/属性来返回字典或直接写在子类。
    #

    def methods_load_options(self) -> Dict[str, Callable[[LoadOptionsFunctions], List[NodePropertyOptions]]]:
        """
        对应 methods.loadOptions
        在子类中可返回:
        {
            \"someKey\": self._some_load_options_function,
            ...
        }
        """
        return {}

    def methods_list_search(self) -> Dict[str, Callable[[LoadOptionsFunctions, Optional[str], Optional[str]], NodeListSearchResult]]:
        """
        对应 methods.listSearch
        """
        return {}

    def methods_credential_test(self) -> Dict[str, CredentialTestFunction]:
        """
        对应 methods.credentialTest
        """
        return {}

    def methods_resource_mapping(self) -> Dict[str, Callable[[LoadOptionsFunctions], ResourceMapperFields]]:
        """
        对应 methods.resourceMapping
        """
        return {}

    def methods_local_resource_mapping(self) -> Dict[str, Callable[[LocalLoadOptionsFunctions], ResourceMapperFields]]:
        """
        对应 methods.localResourceMapping
        """
        return {}

    def methods_action_handler(self) -> Dict[str, Callable[[LoadOptionsFunctions, Union[dict, str, None]], NodeParameterValueType]]:
        """
        对应 methods.actionHandler
        """
        return {}

    #
    # 组合所有 methods
    #
    def methods(self) -> Dict[str, Any]:
        """
        在 TS 中, methods 是一个复合对象。
        在 Python, 你也可以直接组装一个 dict 返回。
        """
        return {
            "loadOptions": self.methods_load_options(),
            "listSearch": self.methods_list_search(),
            "credentialTest": self.methods_credential_test(),
            "resourceMapping": self.methods_resource_mapping(),
            "localResourceMapping": self.methods_local_resource_mapping(),
            "actionHandler": self.methods_action_handler(),
        }

    #
    # === 对应 webhookMethods?: { [name in WebhookType]?: ... } ===
    #
    def webhook_methods(self) -> Dict[WebhookType, Dict[WebhookSetupMethodNames, Callable[[HookFunctions], bool]]]:
        """
        在子类中可返回相应字典:
        {
            "webhookType": {
                "setup": self._some_setup_func,
                "remove": self._some_remove_func
            }
        }
        """
        return {}

    #
    # === 对应 customOperations?: { [resource: string]: { [operation: string]: (this: IExecuteFunctions) => Promise<NodeOutput> } } ===
    #
    def custom_operations(self) -> Dict[str, Dict[str, Callable[[ExecuteFunctions], NodeOutput]]]:
        """
        如: { resource: { operation: func } }   
        """
        return {}
    
class VersionedNodeType(ABC):
    """
    对应 TypeScript: 

    export interface IVersionedNodeType {
        nodeVersions: { [key: number]: INodeType };
        currentVersion: number;
        description: INodeTypeBaseDescription;
        getNodeType: (version?: number) => INodeType;
    }
    """

    # nodeVersions 使用属性+方法 或在子类中直接实现，视项目需要
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
    """
    对应 TypeScript 中的:
    
    export interface INodeTypes {
        getByName(nodeType: string): INodeType | IVersionedNodeType;
        getByNameAndVersion(nodeType: string, version?: number): INodeType;
        getKnownTypes(): IDataObject;
    }
    """

    @abstractmethod
    def get_by_name(self, node_type: str) -> Union[NodeType, VersionedNodeType]:
        pass

    @abstractmethod
    def get_by_name_and_version(self, node_type: str, version: Optional[int] = None) -> NodeType:
        pass

    @abstractmethod
    def get_known_types(self) -> Any:
        pass
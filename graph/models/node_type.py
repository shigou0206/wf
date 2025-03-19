from abc import ABC
from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Callable,
    Protocol,
    Union,
)

from .description_model import NodeTypeDescription

# 下列类或 Protocol 仅占位, 你可以做更细化的定义:
class ISupplyDataFunctions(Protocol):
    pass

class IExecuteFunctions(Protocol):
    pass

class IPollFunctions(Protocol):
    pass

class ITriggerFunctions(Protocol):
    pass

class IWebhookFunctions(Protocol):
    pass

class ILoadOptionsFunctions(Protocol):
    pass

class ILocalLoadOptionsFunctions(Protocol):
    pass

class IHookFunctions(Protocol):
    pass

# 数据、结果、配置等类型:
SupplyData = Any
NodeOutput = Any
INodeExecutionData = Any
ITriggerResponse = Any
IWebhookResponseData = Any
ResourceMapperFields = Any
NodeParameterValueType = Any
INodePropertyOptions = Any
INodeListSearchResult = Any
ICredentialTestFunction = Callable[..., Any]

# WebhookType, WebhookSetupMethodNames 在 TS 中可能是字符串枚举，这里简单用 str
WebhookType = str
WebhookSetupMethodNames = str


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
        context: ISupplyDataFunctions,
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
        context: IExecuteFunctions
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
        context: IPollFunctions
    ) -> Optional[List[List[INodeExecutionData]]]:
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
        context: ITriggerFunctions
    ) -> Optional[ITriggerResponse]:
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
        context: IWebhookFunctions
    ) -> IWebhookResponseData:
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

    def methods_load_options(self) -> Dict[str, Callable[[ILoadOptionsFunctions], List[INodePropertyOptions]]]:
        """
        对应 methods.loadOptions
        在子类中可返回:
        {
            \"someKey\": self._some_load_options_function,
            ...
        }
        """
        return {}

    def methods_list_search(self) -> Dict[str, Callable[[ILoadOptionsFunctions, Optional[str], Optional[str]], INodeListSearchResult]]:
        """
        对应 methods.listSearch
        """
        return {}

    def methods_credential_test(self) -> Dict[str, ICredentialTestFunction]:
        """
        对应 methods.credentialTest
        """
        return {}

    def methods_resource_mapping(self) -> Dict[str, Callable[[ILoadOptionsFunctions], ResourceMapperFields]]:
        """
        对应 methods.resourceMapping
        """
        return {}

    def methods_local_resource_mapping(self) -> Dict[str, Callable[[ILocalLoadOptionsFunctions], ResourceMapperFields]]:
        """
        对应 methods.localResourceMapping
        """
        return {}

    def methods_action_handler(self) -> Dict[str, Callable[[ILoadOptionsFunctions, Union[dict, str, None]], NodeParameterValueType]]:
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
    def webhook_methods(self) -> Dict[WebhookType, Dict[WebhookSetupMethodNames, Callable[[IHookFunctions], bool]]]:
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
    def custom_operations(self) -> Dict[str, Dict[str, Callable[[IExecuteFunctions], NodeOutput]]]:
        """
        如: { resource: { operation: func } }   
        """
        return {}

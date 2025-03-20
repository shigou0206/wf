from dataclasses import dataclass, field
from typing import Optional, Any, Dict, Callable, List, Union
import logging

from .node_model import WorkflowNode, WorkflowNodes, NodeOutputConfiguration
from .connection_model import Connections, ConnectionType
from .node_type import NodeTypes
from .data_model import WorkflowSettings, PinData
from .expression import Expression
from .utils import (
    get_node_parameters, 
    get_connections_by_destination, 
    GlobalState, 
    rename_node_in_parameter_value, 
    NODES_WITH_RENAMABLE_CONTENT
)


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

        self.connections_by_destination_node = get_connections_by_destination(parameters.connections)
        self.active = parameters.active
        self.static_data = parameters.static_data
        self.settings = parameters.settings
        self.pin_data = parameters.pin_data
        self.timezone = self.settings.timezone if self.settings else GlobalState.get_global_state().get("defaultTimezone")
        self.expression = Expression({})

    def get_static_data(self, context_type: str, node: Optional[WorkflowNode] = None) -> Dict[str, Any]:
        if context_type == "global":
            key = "global"
        elif context_type == "node":
            if node is None:
                raise ValueError('Context type "node" requires a node parameter.')
            key = f"node:{node.name}"
        else:
            raise ValueError(f"Unknown context type: {context_type}. Only 'global' and 'node' are supported.")

        # 如果 testStaticData 存在并包含 key，则返回 testStaticData[key]
        if self.test_static_data and key in self.test_static_data:
            return self.test_static_data[key]

        # 确保静态数据结构存在
        if key not in self.static_data:
            self.static_data[key] = {}

        return self.static_data[key]
    
    def set_test_static_data(self, test_static_data: Dict[str, Any]) -> None:
        self.test_static_data = test_static_data

    def query_nodes(self, check_function: Callable[[Any], bool]) -> List[Any]:
        return_nodes = []

        for node_name, node in self.nodes.items():
            if getattr(node, "disabled", False):
                continue

            node_type = self.node_types.get_by_name_and_version(node.type, getattr(node, "type_version", None))

            if node_type is not None and check_function(node_type):
                return_nodes.append(node)

        return return_nodes

    def get_trigger_nodes(self) -> List[Any]:
        return self.query_nodes(lambda node_type: bool(getattr(node_type, "trigger", False)))

    def get_poll_nodes(self) -> List[Any]:
        return self.query_nodes(lambda node_type: bool(getattr(node_type, "poll", False)))
    
    def get_node(self, node_name: str) -> Optional[Any]:
        return self.nodes.get(node_name, None)
    
    def get_nodes(self, node_names: List[str]) -> List[Any]:
        nodes = []
        for name in node_names:
            node = self.get_node(name)
            if not node:
                logging.warning(f"Could not find a node with the name '{name}' in the workflow.")
                continue
            nodes.append(node)

        return nodes
    
    def get_pin_data_of_node(self, node_name: str) -> Optional[List[Any]]:
        return self.pin_data.get(node_name)
    
    def rename_node(self, current_name: str, new_name: str):
        if current_name in self.nodes:
            self.nodes[new_name] = self.nodes.pop(current_name)
            self.nodes[new_name].name = new_name

        for node in self.nodes.values():
            node.parameters = rename_node_in_parameter_value(node.parameters, current_name, new_name)

            if node.type in NODES_WITH_RENAMABLE_CONTENT:
                if "jsCode" in node.parameters:
                    node.parameters["jsCode"] = rename_node_in_parameter_value(
                        node.parameters["jsCode"], current_name, new_name, has_renamable_content=True
                    )

        if current_name in self.connections_by_source_node:
            self.connections_by_source_node[new_name] = self.connections_by_source_node.pop(current_name)

        for source_node, connections in self.connections_by_source_node.items():
            for connection_type, connection_list in connections.items():
                for source_index, connection_group in enumerate(connection_list):
                    for connection in connection_group:
                        if connection["node"] == current_name:
                            connection["node"] = new_name

        self.connections_by_destination_node = get_connections_by_destination(self.connections_by_source_node)

    def get_highest_node(
        self, node_name: str, node_connection_index: Optional[int] = None, checked_nodes: Optional[List[str]] = None
    ) -> List[str]:
        if checked_nodes is None:
            checked_nodes = []

        current_highest = []
        
        if not self.nodes[node_name].disabled:
            current_highest.append(node_name)

        if node_name not in self.connections_by_destination_node:
            return current_highest

        if ConnectionType.Main not in self.connections_by_destination_node[node_name]:
            return current_highest

        if node_name in checked_nodes:
            return current_highest
        checked_nodes.append(node_name)

        return_nodes = []

        for connection_index, connections in enumerate(self.connections_by_destination_node[node_name][ConnectionType.Main]):
            if node_connection_index is not None and node_connection_index != connection_index:
                continue

            for connection in connections:
                if connection.node in checked_nodes:
                    continue

                if connection.node not in self.nodes:
                    continue

                add_nodes = self.get_highest_node(connection.node, None, checked_nodes)

                if not add_nodes:
                    if not self.nodes[connection.node].disabled:
                        add_nodes = [connection.node]

                for name in add_nodes:
                    if name not in return_nodes:
                        return_nodes.append(name)

        return return_nodes
    
    def get_node_outputs(self, node, node_type_data) -> List[Union[str, NodeOutputConfiguration]]:
        if isinstance(node_type_data.outputs, list):
            outputs = node_type_data.outputs
        else:
            try:
                outputs = self.expression.get_simple_parameter_value(
                    node,
                    node_type_data.outputs,
                    mode="internal",
                    additional_keys={},
                ) or []
            except Exception:
                print(f"Could not calculate outputs dynamically for node: {node.name}")
                outputs = []

        if node.on_error == "continueErrorOutput":
            # 确保不会修改原始数据
            outputs = outputs.copy()

            if len(outputs) == 1:
                if isinstance(outputs[0], str):
                    outputs[0] = NodeOutputConfiguration(type=outputs[0], display_name="Success")
                else:
                    outputs[0].display_name = "Success"

            # 追加 "Error" 输出端口
            outputs.append(NodeOutputConfiguration(type=ConnectionType.MAIN, category="error", display_name="Error"))

        return outputs
    
    def get_parent_main_input_node(self, node: WorkflowNode) -> Optional[WorkflowNode]:
        if node is None:
            return None

        node_type = self.node_types.get_by_name_and_version(node.node_type, node.type_version)
        
        outputs = self.get_node_outputs(node, node_type.description)

        non_main_nodes_connected = []
        for output in outputs:
            output_type = output.type if isinstance(output, NodeOutputConfiguration) else output
            if output_type != ConnectionType.MAIN:
                parent_nodes = self.get_child_nodes(node.name, output_type)
                if parent_nodes:
                    non_main_nodes_connected.extend(parent_nodes)

        if non_main_nodes_connected:
            return_node = self.get_node(non_main_nodes_connected[0])
            if return_node is None:
                raise RuntimeError(f'Node "{non_main_nodes_connected[0]}" not found')

            return self.get_parent_main_input_node(return_node)

        return node
    
    def get_node_connection_indexes(
        self,
        node_name: str,
        parent_node_name: str,
        connection_type: ConnectionType = ConnectionType.MAIN,
        depth: int = -1,
        checked_nodes: Optional[list[str]] = None,
    ) -> Optional[dict]:
        """
        获取 `node_name` 和 `parent_node_name` 之间的连接索引。

        Args:
            node_name (str): 目标节点的名称
            parent_node_name (str): 父节点的名称
            connection_type (ConnectionType): 连接类型，默认 `MAIN`
            depth (int): 递归搜索的深度，默认 -1（无限制）
            checked_nodes (list[str]): 已检查的节点（防止循环）
        
        Returns:
            dict: 包含 `sourceIndex` 和 `destinationIndex` 的字典
        """
        node = self.get_node(parent_node_name)
        if node is None:
            return None

        depth = depth if depth == -1 else depth - 1
        if depth == 0:
            return None  # 达到最大深度

        if node_name not in self.connections_by_destination_node:
            return None
        if connection_type not in self.connections_by_destination_node[node_name]:
            return None

        checked_nodes = checked_nodes or []
        if node_name in checked_nodes:
            return None  # 防止无限循环

        checked_nodes.append(node_name)

        for connections_by_index in self.connections_by_destination_node[node_name][connection_type]:
            if not connections_by_index:
                continue

            for destination_index, connection in enumerate(connections_by_index):
                if parent_node_name == connection["node"]:
                    return {"sourceIndex": connection["index"], "destinationIndex": destination_index}

                if connection["node"] in checked_nodes:
                    continue  # 已经检查过的节点跳过

                output_index = self.get_node_connection_indexes(
                    connection["node"], parent_node_name, connection_type, depth, checked_nodes
                )
                if output_index is not None:
                    return output_index

        return None
    
    def _get_start_node(self, node_names: List[str]) -> Optional[WorkflowNode]:
        for node_name in node_names:
            node = self.nodes.get(node_name)

            if not node:
                continue

            # 只有一个节点，且未禁用，则直接返回
            if len(node_names) == 1 and not node.disabled:
                return node

            node_type = self.node_types.get_by_name_and_version(node.type, node.type_version)

            # 跳过手动聊天触发器
            if node_type.description.name == "MANUAL_CHAT_TRIGGER_LANGCHAIN_NODE_TYPE":
                continue

            # 找到第一个未禁用的 trigger 或 poll 节点
            if (node_type and (hasattr(node_type, "trigger") or hasattr(node_type, "poll"))) and not node.disabled:
                return node

        # 没找到，则按照 STARTING_NODE_TYPES 排序
        # sorted_nodes = sorted(
        #     self.nodes.values(),
        #     key=lambda n: STARTING_NODE_TYPES.index(n.type) if n.type in STARTING_NODE_TYPES else float("inf")
        # )

        # # 返回排序后的第一个可用节点
        # for node in sorted_nodes:
        #     if node.type in STARTING_NODE_TYPES and not node.disabled:
        #         return node

        return None
    
    def get_start_node(self, destination_node: Optional[str] = None) -> Optional[WorkflowNode]:
        if destination_node:
            node_names = self.get_highest_node(destination_node)

            if not node_names:

                node_names.append(destination_node)

            start_node = self._get_start_node(node_names)
            if start_node:
                return start_node

            return self.nodes.get(node_names[0])

        return self._get_start_node(list(self.nodes.keys()))
from typing import Optional, Callable, List, Dict, Awaitable, Any
from .node_model import NodeProperties
from .connection_model import NodeConnection, Connections
from collections import defaultdict
import copy

CloseFunction = Callable[[], Awaitable[None]]

class GlobalState:
    """Manages global state settings such as timezone."""
    
    _state: Dict[str, str] = {"defaultTimezone": "America/New_York"}

    @classmethod
    def set_global_state(cls, state: Dict[str, str]) -> None:
        """
        Updates the global state.

        :param state: A dictionary representing the new global state.
        """
        cls._state = state

    @classmethod
    def get_global_state(cls) -> Dict[str, str]:
        """
        Returns a deep copy of the global state to prevent modification.

        :return: A dictionary containing the global state.
        """
        return copy.deepcopy(cls._state)

def get_parameter_dependencies(node_properties_array: List[NodeProperties]) -> Dict[str, List[str]]:
    dependencies: Dict[str, List[str]] = {}

    for node_properties in node_properties_array:
        name = node_properties.name
        display_options = node_properties.display_options

        if not isinstance(name, str) or not name.strip():
            continue

        if name not in dependencies:
            dependencies[name] = []

        if not isinstance(display_options, dict):
            continue

        for display_rule in display_options.values():
            if not isinstance(display_rule, dict):
                continue

            for parameter_name in display_rule.keys():
                if isinstance(parameter_name, str) and not parameter_name.startswith("@"):
                    if parameter_name not in dependencies[name]:
                        dependencies[name].append(parameter_name)

    return dependencies

def get_parameter_resolve_order(
    node_properties_array: List[NodeProperties],
    parameter_dependencies: Dict[str, List[str]],
) -> List[int]:
    execution_order: List[int] = []
    index_to_resolve = list(range(len(node_properties_array)))
    resolved_parameters: List[str] = []
    dependency_check = {prop.name: set(parameter_dependencies.get(prop.name, [])) for prop in node_properties_array}

    last_index_length = len(index_to_resolve)
    last_index_reduction = -1
    iterations = 0
    max_iterations = len(node_properties_array) * 2  # Avoid infinite loops

    while index_to_resolve:
        iterations += 1

        if iterations > max_iterations:
            raise RuntimeError(
                "Circular dependency detected! Could not resolve parameter dependencies."
            )

        index = index_to_resolve.pop(0)
        property_name = node_properties_array[index].name

        if not parameter_dependencies.get(property_name):
            execution_order.append(index)
            resolved_parameters.append(property_name)
            continue

        dependencies = parameter_dependencies[property_name]
        unresolved_dependencies = [
            dep for dep in dependencies if dep not in resolved_parameters and not dep.startswith("/")
        ]

        if unresolved_dependencies:
            index_to_resolve.append(index)
            continue

        execution_order.append(index)
        resolved_parameters.append(property_name)

        if len(index_to_resolve) < last_index_length:
            last_index_reduction = iterations

        last_index_length = len(index_to_resolve)

    return execution_order


def get_node_parameters(
    node_properties_array: List[NodeProperties],
    node_values: Optional[Dict[str, Any]],
    return_defaults: bool,
    return_none_displayed: bool,
    node: Optional[Dict[str, Any]],
    only_simple_types: bool = False,
    data_is_resolved: bool = False,
    node_values_root: Optional[Dict[str, Any]] = None,
    parent_type: Optional[str] = None,
    parameter_dependencies: Optional[Dict[str, List[str]]] = None
) -> Dict[str, Any]:
    """ Fully aligned version of getNodeParameters from TypeScript to Python """

    if parameter_dependencies is None:
        parameter_dependencies = get_parameter_dependencies(node_properties_array)

    duplicate_parameter_names = set()
    parameter_names = set()

    for node_properties in node_properties_array:
        name = node_properties.name
        if name in parameter_names:
            duplicate_parameter_names.add(name)
        else:
            parameter_names.add(name)

    node_parameters: Dict[str, Any] = {}
    node_parameters_full: Dict[str, Any] = {}

    # Preprocess node values to check displayed parameters
    node_values_display_check = node_parameters_full
    if not data_is_resolved and not return_none_displayed:
        node_values_display_check = get_node_parameters(
            node_properties_array,
            node_values,
            return_defaults=True,
            return_none_displayed=True,
            node=node,
            only_simple_types=True,
            data_is_resolved=True,
            node_values_root=node_values_root,
            parent_type=parent_type,
            parameter_dependencies=parameter_dependencies,
        )

    node_values_root = node_values_root or node_values_display_check

    parameter_iteration_order = get_parameter_resolve_order(node_properties_array, parameter_dependencies)

    for parameter_index in parameter_iteration_order:
        node_properties = node_properties_array[parameter_index]
        name = node_properties.name

        if not node_values or (name not in node_values and (not return_defaults or parent_type == "collection")):
            continue

        if name in duplicate_parameter_names:
            continue

        # Process simple types
        if node_properties.type not in {"collection", "fixedCollection"}:
            if return_defaults:
                node_parameters[name] = node_values.get(name, node_properties.default)
            elif name in node_values and node_values[name] != node_properties.default:
                node_parameters[name] = node_values[name]

        if only_simple_types:
            continue  # Skip deeper processing

        # Handle complex parameter types: collections
        if node_properties.type == "collection":
            if node_properties.type_options and node_properties.type_options.get("multipleValues"):
                # If multiple values are allowed, return array directly
                node_parameters[name] = node_values.get(name, []) if return_defaults else node_values.get(name)
            else:
                # Otherwise, recursively resolve parameters inside the collection
                temp_node_parameters = get_node_parameters(
                    node_properties.options or [],
                    node_values.get(name, {}),
                    return_defaults,
                    return_none_displayed,
                    node,
                    False,
                    False,
                    node_values_root,
                    node_properties.type,
                )
                if temp_node_parameters:
                    node_parameters[name] = temp_node_parameters

        elif node_properties.type == "fixedCollection":
            collection_values: Dict[str, Any] = {}
            property_values = node_values.get(name, {} if return_defaults else None)

            if return_defaults and not property_values:
                property_values = node_properties.default

            for item_name, value in (property_values or {}).items():
                if isinstance(value, list):
                    collection_values[item_name] = [
                        get_node_parameters(
                            node_properties.options or [], v, return_defaults, return_none_displayed, node, False, False, node_values_root, node_properties.type
                        ) for v in value
                    ]
                else:
                    collection_values[item_name] = get_node_parameters(
                        node_properties.options or [], value, return_defaults, return_none_displayed, node, False, False, node_values_root, node_properties.type
                    )

            node_parameters[name] = collection_values

    return node_parameters

def get_connections_by_destination(connections: Connections) -> Connections:
    return_connections: Connections = defaultdict(lambda: defaultdict(list))

    for source_node, node_connections in connections.items():
        for connection_type, input_connections in node_connections.items():
            for input_index, connection_list in enumerate(input_connections or []):
                if not connection_list:
                    continue

                for connection_info in connection_list:
                    dest_node = connection_info.node
                    dest_type = connection_info.connection_type
                    dest_index = connection_info.index

                    while len(return_connections[dest_node][dest_type.value]) <= dest_index:
                        return_connections[dest_node][dest_type.value].append([])

                    return_connections[dest_node][dest_type.value][dest_index].append(
                        NodeConnection(source_node, connection_type, input_index)
                    )

    return return_connections


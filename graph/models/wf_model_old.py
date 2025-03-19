import re
from typing import Dict, List, Optional, Set
from collections import deque

class ConnectionInfo:
    __slots__ = ("node", "conn_type", "index")
    def __init__(self, node: str, conn_type: str, index: int):
        self.node = node
        self.conn_type = conn_type
        self.index = index

    def __repr__(self):
        return f"ConnectionInfo(node={self.node}, type={self.conn_type}, index={self.index})"


class Node:
    def __init__(
        self,
        name: str,
        node_type: str,
        type_version: int = 1,
        parameters: Optional[dict] = None,
        disabled: bool = False,
    ):
        self.name = name
        self.type = node_type
        self.type_version = type_version
        self.parameters = parameters if parameters is not None else {}
        self.disabled = disabled

    def __repr__(self):
        return (f"<Node name={self.name}, type={self.type}, "
                f"version={self.type_version}, disabled={self.disabled}>")


class Workflow:
    """
    修正 rename_node 时的字符串替换, 防止缺少引号导致 `$node["NodeA_new]` 之类错误.
    """

    EXPR_PATTERNS = [
        (re.compile(r'(\$node\[\s*(["\']))(.*?)\2(\s*\])'), 3),  # group(3) = oldName
        (re.compile(r'(\$node\.)([A-Za-z0-9_]+)([\.\(\s]|$)'), 2),  # group(2) = oldName
        (re.compile(r'(\$items\(\s*(["\']))(.*?)\2(\s*[,\)])'), 3), # group(3) = oldName
    ]

    def __init__(
        self,
        workflow_id: str,
        name: str,
        nodes: List[Node],
        connections_by_source_node: Dict[str, Dict[str, List[List[ConnectionInfo]]]],
        active: bool = False,
        static_data: Optional[dict] = None,
    ):
        self.id = workflow_id
        self.name = name
        self.active = active

        self.nodes: Dict[str, Node] = {n.name: n for n in nodes}

        self.connections_by_source_node = connections_by_source_node

        self.connections_by_destination_node = self._build_connections_by_destination(connections_by_source_node)

        self.static_data = static_data or {}

    def _build_connections_by_destination(self, src):
        result: Dict[str, Dict[str, List[List[ConnectionInfo]]]] = {}
        for source_node, type_dict in src.items():
            for conn_type, list_of_lists in type_dict.items():
                for out_idx, conn_infos in enumerate(list_of_lists):
                    if not conn_infos:
                        continue
                    for c_info in conn_infos:
                        dest_node = c_info.node
                        dest_type = c_info.conn_type
                        dest_index = c_info.index

                        if dest_node not in result:
                            result[dest_node] = {}
                        if dest_type not in result[dest_node]:
                            result[dest_node][dest_type] = []

                        while len(result[dest_node][dest_type]) <= dest_index:
                            result[dest_node][dest_type].append([])

                        reversed_info = ConnectionInfo(
                            node=source_node,
                            conn_type=conn_type,
                            index=out_idx
                        )
                        result[dest_node][dest_type][dest_index].append(reversed_info)
        return result

    def get_node(self, node_name: str) -> Optional[Node]:
        return self.nodes.get(node_name)

    def rename_node(self, old_name: str, new_name: str):
        if old_name not in self.nodes or old_name == new_name:
            return

        node_obj = self.nodes[old_name]
        node_obj.name = new_name
        self.nodes[new_name] = node_obj
        del self.nodes[old_name]

        for n in self.nodes.values():
            n.parameters = self._recursive_replace_in_parameters(n.parameters, old_name, new_name)

        if old_name in self.connections_by_source_node:
            self.connections_by_source_node[new_name] = self.connections_by_source_node[old_name]
            del self.connections_by_source_node[old_name]

        for src_node, conn_types in self.connections_by_source_node.items():
            for ctype, list_of_lists in conn_types.items():
                for conn_list in list_of_lists:
                    for ci in conn_list:
                        if ci.node == old_name:
                            ci.node = new_name

        self.connections_by_destination_node = self._build_connections_by_destination(self.connections_by_source_node)

    def _recursive_replace_in_parameters(self, value, old_name, new_name):
        if isinstance(value, str):
            return self._replace_in_string(value, old_name, new_name)
        elif isinstance(value, list):
            return [self._recursive_replace_in_parameters(v, old_name, new_name) for v in value]
        elif isinstance(value, dict):
            return {
                k: self._recursive_replace_in_parameters(v, old_name, new_name)
                for k,v in value.items()
            }
        return value

    def _replace_in_string(self, text: str, old_name: str, new_name: str) -> str:
        """
        利用正则替换 `$node["oldName"]` / `$node.oldName` / `$items("oldName")` => new_name
        注意插回捕获分组的引号, 避免 `$node["NodeA_new]`.
        """
        def _replace_func(pattern_id: int):
            def do_replace(m: re.Match) -> str:
                captured_name = m.group(3)
                if captured_name == old_name:
                    if pattern_id == 1:
                        return f"{m.group(1)}{new_name}{m.group(2)}{m.group(4)}"
                    elif pattern_id == 2:
                        return f"{m.group(1)}{new_name}{m.group(3)}"
                    elif pattern_id == 3:
                        return f"{m.group(1)}{new_name}{m.group(2)}{m.group(4)}"
                return m.group(0)
            return do_replace

        new_text = text
        for idx, (pattern, _) in enumerate(self.EXPR_PATTERNS, 1):
            new_text = pattern.sub(_replace_func(idx), new_text)
        return new_text

    def get_child_nodes(self, node_name: str, conn_type: str = "main") -> List[str]:
        visited: Set[str] = set()
        result: List[str] = []

        def dfs(curr: str):
            if curr in visited:
                return
            visited.add(curr)
            if curr not in self.connections_by_source_node:
                return
            type_dict = self.connections_by_source_node[curr]
            if conn_type == "ALL":
                types_to_check = list(type_dict.keys())
            else:
                types_to_check = [conn_type]

            for t in types_to_check:
                if t not in type_dict:
                    continue
                for conn_infos in type_dict[t]:
                    if not conn_infos:
                        continue
                    for ci in conn_infos:
                        child = ci.node
                        if child not in visited:
                            result.append(child)
                            dfs(child)

        dfs(node_name)
        if node_name in result:
            result.remove(node_name)
        return result

    def get_child_nodes_bfs(self, node_name: str, conn_type: str = "main") -> List[str]:
        visited: Set[str] = set()
        queue = deque([node_name])
        output: List[str] = []

        while queue:
            c = queue.popleft()
            if c in visited:
                continue
            visited.add(c)
            if c != node_name:
                output.append(c)

            if c not in self.connections_by_source_node:
                continue

            type_dict = self.connections_by_source_node[c]
            if conn_type == "ALL":
                types_to_check = list(type_dict.keys())
            else:
                types_to_check = [conn_type]

            for t in types_to_check:
                if t not in type_dict:
                    continue
                for conn_infos in type_dict[t]:
                    if conn_infos:
                        for ci in conn_infos:
                            nxt = ci.node
                            if nxt not in visited:
                                queue.append(nxt)
        return output

    def get_parent_nodes(self, node_name: str, conn_type: str = "main") -> List[str]:
        visited: Set[str] = set()
        result: List[str] = []

        def dfs(curr: str):
            if curr in visited:
                return
            visited.add(curr)
            if curr not in self.connections_by_destination_node:
                return
            type_dict = self.connections_by_destination_node[curr]
            if conn_type == "ALL":
                types_to_check = list(type_dict.keys())
            else:
                types_to_check = [conn_type]
            for t in types_to_check:
                if t not in type_dict:
                    continue
                for conn_infos in type_dict[t]:
                    if not conn_infos:
                        continue
                    for ci in conn_infos:
                        p = ci.node
                        if p not in visited:
                            result.append(p)
                            dfs(p)

        dfs(node_name)
        if node_name in result:
            result.remove(node_name)
        return result

    def get_start_node(self) -> Optional[Node]:
        """
        1) 优先找 type 中含 'trigger' & not disabled
        2) 否则找无父节点 or 父节点都disabled
        """
        # 1) trigger
        for node in self.nodes.values():
            if "trigger" in node.type.lower() and not node.disabled:
                return node

        # 2) find no parents
        for node in self.nodes.values():
            if node.disabled:
                continue
            parents = self.get_parent_nodes(node.name)
            if not parents:
                return node
            # or all parent disabled
            all_disabled = True
            for p in parents:
                if not self.nodes[p].disabled:
                    all_disabled = False
                    break
            if all_disabled:
                return node
        return None
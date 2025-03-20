from typing import Any, Dict, List, Optional, Tuple, Union
from collections import defaultdict, deque
import time

from .models import NodeResult, ExecutionStatus, ExecutionError
from .context import NodeExecutionContext
from .node_types import NodeType, SwitchNodeType, ProducerNodeType
from graph.models.wf_model_old import Workflow, Node, ConnectionInfo

from .logger import Logger
from .hooks import HookManager


class ErrorPolicy:
    STOP_WORKFLOW = "stopWorkflow"
    CONTINUE_ON_FAIL = "continueOnFail"
    RETRY_ON_FAIL = "retryOnFail"
    ERROR_OUTPUT = "errorOutput"


class WorkflowExecutor:
    """
    功能：
    1) 多输入合并：使用 waitingData 与 inputRequirements 实现。
    2) 若未指定 start_nodes，则自动查找（无父节点或 trigger 节点）。
    3) 支持同时启动多个起点（允许多路输入合并）。
    4) 可指定 destination_node，仅执行该节点及其所有上游子图。
    5) 节点错误策略：通过 onError、maxRetries、retryDelay、errorOutputIndex 控制，
       支持 stopWorkflow、continueOnFail、retryOnFail、errorOutput 四种策略。
    6) 内置日志记录与钩子调用，便于调试、监控与前端反馈。
    """

    def __init__(
        self,
        workflow: Workflow,
        mode: str = "manual",
        global_config: Optional[Dict[str, Any]] = None,
    ):
        self.workflow = workflow
        self.mode = mode
        self.global_config = global_config if global_config is not None else {}
        self.status: ExecutionStatus = ExecutionStatus.NEW

        self.run_data: Dict[str, List[NodeResult]] = {}

        self.start_time: float = 0
        self.end_time: float = 0

        self.waitingData: Dict[str, Dict[int, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))

        self.inputRequirements: Dict[str, int] = {}
        self._calculate_input_requirements()

        self.hook_manager = HookManager()

        Logger.info("WorkflowExecutor initialized.", extra={"mode": self.mode, "workflow_id": self.workflow.id})

    def _calculate_input_requirements(self):
        Logger.debug("Calculating input requirements...", extra={})
        from collections import defaultdict
        dest_map: Dict[str, set] = defaultdict(set)

        for srcNode, connTypes in self.workflow.connections_by_source_node.items():
            mainConns = connTypes.get("main", [])
            for outIdx, connInfos in enumerate(mainConns):
                for cInfo in connInfos:
                    dest_map[cInfo.node].add(cInfo.index)

        for nodeName, idxSet in dest_map.items():
            self.inputRequirements[nodeName] = len(idxSet)
            Logger.debug(f"Node '{nodeName}' requires {len(idxSet)} input(s).", extra={})

    def execute_workflow(
        self,
        start_node_names: Optional[List[str]] = None,
        destination_node: Optional[str] = None,
        start_inputs: Optional[Dict[str, List[Dict[str, Any]]]] = None  # 新增参数
    ) -> Dict[str, Any]:
        Logger.info("Starting Workflow Execution.", extra={"mode": self.mode, "destination_node": destination_node})
        self.status = ExecutionStatus.RUNNING
        self.start_time = time.time()

        self.hook_manager.run_hook("workflowExecuteBefore", workflow=self.workflow, start_time=self.start_time)

        subgraph_nodes = None
        if destination_node:
            subgraph_nodes = self._find_ancestors_including(destination_node)
            Logger.debug("Subgraph computed.", extra={"destination_node": destination_node, "subgraph_nodes": list(subgraph_nodes)})

        node_stack: deque[Tuple[Node, Optional[List[Dict[str, Any]]]]] = deque()

        if start_node_names:
            Logger.debug("Using provided start_node_names.", extra={"start_node_names": start_node_names})
            for nm in start_node_names:
                n_obj = self.workflow.get_node(nm)
                if not n_obj:
                    continue
                if subgraph_nodes and nm not in subgraph_nodes:
                    Logger.debug(f"Node '{nm}' not in subgraph; skipped.", extra={})
                    continue
                node_input = start_inputs.get(nm) if start_inputs and nm in start_inputs else None
                node_stack.append((n_obj, node_input))
        else:
            if subgraph_nodes:
                auto_starts = self._find_start_nodes_in_subgraph(subgraph_nodes)
            else:
                auto_starts = self._find_start_nodes()
            if not auto_starts:
                Logger.error("No valid start nodes found.", extra={})
                self.status = ExecutionStatus.ERROR
                return self._build_result(error_msg="No valid start nodes found")
            Logger.debug("Auto start nodes found.", extra={"start_nodes": [n.name for n in auto_starts]})
            for stN in auto_starts:
                node_stack.append((stN, None))

        try:
            while node_stack:
                current_node, input_data = node_stack.pop()
                Logger.debug(f"Popped node '{current_node.name}' from stack.", extra={})

                if subgraph_nodes and current_node.name not in subgraph_nodes:
                    Logger.debug(f"Node '{current_node.name}' not in subgraph; skipped.", extra={})
                    continue

                if current_node.disabled:
                    Logger.info(f"Node '{current_node.name}' is disabled; recording input and skipping.", extra={})
                    self.run_data.setdefault(current_node.name, [])
                    self.run_data[current_node.name].append(NodeResult(data=[[input_data or []]]))
                    continue

                self.hook_manager.run_hook("nodeExecuteBefore", node=current_node, input_data=input_data, timestamp=time.time())

                node_logic = self._get_node_type_logic(current_node)
                Logger.debug(f"Node '{current_node.name}' logic type: {node_logic.__class__.__name__}", extra={})

                result = self._run_node_with_error_strategy(current_node, node_logic, input_data)
                self.run_data.setdefault(current_node.name, [])
                self.run_data[current_node.name].append(result)

                self.hook_manager.run_hook("nodeExecuteAfter", node=current_node, result=result, timestamp=time.time())

                if result.error:
                    Logger.error(f"Node '{current_node.name}' final error; stopping workflow.", extra={})
                    self.status = ExecutionStatus.ERROR
                    raise ExecutionError(str(result.error), node_name=current_node.name)

                if not result.data:
                    Logger.debug(f"Node '{current_node.name}' produced no output; skipping children.", extra={})
                    continue

                if current_node.name in self.workflow.connections_by_source_node:
                    mainConns = self.workflow.connections_by_source_node[current_node.name].get("main", [])
                    for outIdx, outItems in enumerate(result.data):
                        if outIdx >= len(mainConns):
                            continue
                        for cInfo in mainConns[outIdx]:
                            childName = cInfo.node
                            if subgraph_nodes and childName not in subgraph_nodes:
                                Logger.debug(f"Child node '{childName}' not in subgraph; skipped.", extra={})
                                continue
                            Logger.debug(f"Distributing output to child '{childName}', inputIndex={cInfo.index}, items={len(outItems)}", extra={})
                            self.waitingData[childName][cInfo.index].extend(outItems)
                            if self._is_node_ready(childName):
                                combinedData = self._combine_all_inputs(childName)
                                del self.waitingData[childName]
                                childNode = self.workflow.get_node(childName)
                                Logger.debug(f"Child '{childName}' is ready; pushing stack with {len(combinedData)} items.", extra={})
                                node_stack.append((childNode, combinedData))

            Logger.info("Workflow execution completed successfully.", extra={})
            self.status = ExecutionStatus.SUCCESS

        except ExecutionError as e:
            Logger.error(f"ExecutionError: {e}", extra={})
            self.status = ExecutionStatus.ERROR
            return self._build_result(error_msg=str(e), node_name=e.node_name)
        except Exception as e:
            Logger.error(f"Unknown exception: {e}", extra={})
            self.status = ExecutionStatus.ERROR
            return self._build_result(error_msg=str(e))
        finally:
            self.end_time = time.time()

            self.hook_manager.run_hook("workflowExecuteAfter", result=self._build_result(), end_time=self.end_time)

        return self._build_result()

    def _find_ancestors_including(self, node_name: str) -> set:
        visited = set()
        def dfs(nm: str):
            if nm in visited:
                return
            visited.add(nm)
            parents = self.workflow.get_parent_nodes(nm, "main")
            for p in parents:
                dfs(p)
        dfs(node_name)
        return visited

    def _find_start_nodes_in_subgraph(self, sub_nodes: set) -> List[Node]:
        res = []
        for nm in sub_nodes:
            n_obj = self.workflow.get_node(nm)
            if n_obj.disabled:
                continue
            logic = self._get_node_type_logic(n_obj)
            if logic.is_trigger:
                res.append(n_obj)
                continue
            pset = self.workflow.get_parent_nodes(nm, "main")
            p_in = [p for p in pset if p in sub_nodes]
            if not p_in:
                res.append(n_obj)
        return res

    def _find_start_nodes(self) -> List[Node]:
        all_nodes = set(self.workflow.nodes.keys())
        child_nodes = set()
        for srcName, connDict in self.workflow.connections_by_source_node.items():
            main_conns = connDict.get("main", [])
            for cList in main_conns:
                for cInfo in cList:
                    child_nodes.add(cInfo.node)
        no_parent = all_nodes - child_nodes
        out = []
        for nm in all_nodes:
            n_obj = self.workflow.nodes[nm]
            if n_obj.disabled:
                continue
            logic = self._get_node_type_logic(n_obj)
            if logic.is_trigger:
                out.append(n_obj)
            elif nm in no_parent:
                out.append(n_obj)
        return out

    # =============== error / retry ===============
    def _run_node_with_error_strategy(
        self,
        node: Node,
        node_type_logic: NodeType,
        input_data: Optional[List[Dict[str, Any]]]
    ) -> NodeResult:
        on_err = node.parameters.get("onError", ErrorPolicy.STOP_WORKFLOW)
        maxR = int(node.parameters.get("maxRetries", 0))
        rDelay = float(node.parameters.get("retryDelay", 0))
        errIdx = int(node.parameters.get("errorOutputIndex", 1))

        cur_try = 0
        while True:
            cur_try += 1
            Logger.debug(f"Node '{node.name}' try #{cur_try}, onError={on_err}, maxR={maxR}", extra={})
            try:
                result = self._run_node_logic_impl(node, node_type_logic, input_data)
                Logger.debug(f"Node '{node.name}' success on attempt #{cur_try}", extra={})
                return result
            except Exception as e:
                Logger.error(f"Node '{node.name}' EX on try #{cur_try}: {e}", extra={})
                if on_err == ErrorPolicy.CONTINUE_ON_FAIL:
                    fb = {"error": str(e), "errType": type(e).__name__}
                    Logger.info(f"continueOnFail: produce fallback item {fb}", extra={})
                    return NodeResult(data=[[fb]], error=None)
                elif on_err == ErrorPolicy.RETRY_ON_FAIL:
                    if cur_try <= maxR:
                        Logger.info(f"retryOnFail: attempt {cur_try}, sleep {rDelay}, next...", extra={})
                        if rDelay > 0:
                            time.sleep(rDelay)
                        continue
                    else:
                        Logger.error(f"Used up {maxR} retries; raising ExecutionError", extra={})
                        raise ExecutionError(str(e)) from e
                elif on_err == ErrorPolicy.ERROR_OUTPUT:
                    Logger.info(f"errorOutput: produce error on outputIndex={errIdx}", extra={})
                    outs: List[List[Dict[str, Any]]] = []
                    for i in range(errIdx + 1):
                        outs.append([])
                    outs[errIdx] = [{"error": str(e), "errType": type(e).__name__}]
                    return NodeResult(data=outs, error=None)
                else:
                    Logger.error("stopWorkflow: raising ExecutionError", extra={})
                    raise ExecutionError(str(e)) from e

    def _run_node_logic_impl(
        self,
        node: Node,
        node_logic: NodeType,
        input_data: Optional[List[Dict[str, Any]]]
    ) -> NodeResult:
        
        if node_logic.is_trigger:
            if self.mode == "manual":
                Logger.debug(f"Node '{node.name}' (trigger) produce trig item", extra={})
                return NodeResult(data=[[{"trig": True}]])
            else:
                out = [dict(item) for item in (input_data or [])]
                Logger.debug(f"Node '{node.name}' (trigger) pass-through {len(out)} items", extra={})
                return NodeResult(data=[out])
        else:
            if not node_logic.can_execute:
                Logger.debug(f"Node '{node.name}' can_execute=False; pass-through", extra={})
                return NodeResult(data=[[input_data or []]])
            Logger.debug(f"Node '{node.name}' calling node_logic.execute() with {len(input_data or [])} items", extra={})
            ctx = NodeExecutionContext(node.name, input_data, self.mode, self.global_config)
            return node_logic.execute(ctx)

    # =============== waitingData / combine ===============
    def _is_node_ready(self, node_name: str) -> bool:
        need = self.inputRequirements.get(node_name, 1)
        if node_name not in self.waitingData:
            return False
        w_d = self.waitingData[node_name]
        for i in range(need):
            if i not in w_d:
                return False
        return True

    def _combine_all_inputs(self, node_name: str) -> List[Dict[str, Any]]:
        combined = []
        need = self.inputRequirements.get(node_name, 1)
        for i in range(need):
            combined.extend(self.waitingData[node_name][i])
        return combined

    # =============== nodeType logic ===============
    def _get_node_type_logic(self, node: Node) -> NodeType:
        node_type_lower = node.type.lower()
        if "producer" in node_type_lower:
            return ProducerNodeType(name=node.type)
        if "switch" in node_type_lower:
            return SwitchNodeType(name=node.type)
        if "trigger" in node_type_lower:
            return NodeType(name=node.type, can_execute=False, is_trigger=True)
        if "condition" in node_type_lower:
            from .node_types import ConditionNodeType
            return ConditionNodeType(name=node.type)
        if "executesubworkflow" in node_type_lower:
            from .node_types import ExecuteSubWorkflowNode
            return ExecuteSubWorkflowNode(name=node.type)
        return NodeType(name=node.type, can_execute=True, is_trigger=False)

    # =============== final result ===============
    def _build_result(self, error_msg: Optional[str] = None, node_name: Optional[str] = None) -> Dict[str, Any]:
        dur = self.end_time - self.start_time if self.end_time > self.start_time else 0
        res: Dict[str, Any] = {
            "status": self.status.name,
            "startedAt": self.start_time,
            "finishedAt": self.end_time,
            "executionTime": dur,
            "runData": {}
        }
        if error_msg:
            res["error"] = {
                "message": error_msg,
                "nodeName": node_name
            }
        run_data_repr = {}
        for nm, nResList in self.run_data.items():
            run_data_repr[nm] = [repr(r) for r in nResList]
        res["runData"] = run_data_repr
        return res
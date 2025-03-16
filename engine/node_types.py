# engine/node_types.py

from typing import List, Dict, Any
from .context import NodeExecutionContext
from .models import NodeResult

class NodeType:
    """
    基础节点类型:
      - processor、pass-through 等
    """
    def __init__(self, name: str, can_execute: bool = True, is_trigger: bool = False):
        self.name = name
        self.can_execute = can_execute
        self.is_trigger = is_trigger

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        """
        默认实现：将输入数据直接传递，并在每个输出项上打上 processedBy 标记。
        如果没有输入，则返回空输出。
        """
        out = []
        for item in (context.input_data or []):
            new_item = dict(item)
            new_item["processedBy"] = context.node_name
            out.append(new_item)
        return NodeResult(data=[out])


class ProducerNodeType(NodeType):
    """
    Producer 节点：
    - 如果没有输入，则生成初始数据；
    - 如果有输入，则将数据传递并添加 processedBy 标记。
    """
    def execute(self, context: NodeExecutionContext) -> NodeResult:
        if not context.input_data:
            data_out = [{
                "source": "producer",
                "msg": f"Data from {context.node_name}",
                "processedBy": context.node_name
            }]
            return NodeResult(data=[data_out])
        else:
            out = []
            for item in context.input_data:
                new_item = dict(item)
                new_item["processedBy"] = context.node_name
                out.append(new_item)
            return NodeResult(data=[out])


class SwitchNodeType(NodeType):
    """
    Switch 节点示例：
    根据输入项中 "category" 字段判断，如果等于 "A" 则输出到分支 0，否则输出到分支 1。
    """
    def __init__(self, name: str):
        super().__init__(name, can_execute=True, is_trigger=False)

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        out0: List[Dict[str, Any]] = []
        out1: List[Dict[str, Any]] = []
        for item in (context.input_data or []):
            new_item = dict(item)
            new_item["processedBy"] = context.node_name
            if new_item.get("category") == "A":
                new_item["branch"] = "true"
                out0.append(new_item)
            else:
                new_item["branch"] = "false"
                out1.append(new_item)
        return NodeResult(data=[out0, out1])


class TriggerNodeType(NodeType):
    """
    Trigger 节点示例：
    - 在手动模式下返回一条触发数据，
    - 否则将输入数据传递，并添加 processedBy 标记。
    """
    def __init__(self, name: str):
        super().__init__(name, can_execute=False, is_trigger=True)

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        if context.mode == "manual":
            return NodeResult(data=[[{"trig": True, "processedBy": context.node_name}]])
        else:
            out = []
            for item in (context.input_data or []):
                new_item = dict(item)
                new_item["processedBy"] = context.node_name
                out.append(new_item)
            return NodeResult(data=[out])


class ConditionNodeType(NodeType):
    """
    条件节点示例：
    - 遍历输入数据，根据 item 中的 "pass" 字段判断，
      如果为 True 则输出到分支 0，否则输出到分支 1。
    - 每个输出项均添加 processedBy 和 branch 标记。
    """
    def __init__(self, name: str):
        super().__init__(name, can_execute=True, is_trigger=False)

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        out_true = []
        out_false = []
        for item in (context.input_data or []):
            new_item = dict(item)
            new_item["processedBy"] = context.node_name
            if new_item.get("pass", False):
                new_item["branch"] = "true"
                out_true.append(new_item)
            else:
                new_item["branch"] = "false"
                out_false.append(new_item)
        return NodeResult(data=[out_true, out_false])


class ExecuteSubWorkflowNode(NodeType):
    """
    子工作流节点示例：
    - 该节点假定在 global_config 中存在键 "subWorkflow"，
      其值为一个 Workflow 对象（子工作流）。
    - 执行时通过创建新的 WorkflowExecutor 执行子工作流，
      并将子工作流的 runData 作为输出返回。
    - 如果子工作流执行过程中出现异常，可考虑扩展错误处理（目前简单返回空数据）。
    """
    def __init__(self, name: str):
        super().__init__(name, can_execute=True, is_trigger=False)

    def execute(self, context: NodeExecutionContext) -> NodeResult:
        sub_wf = context.global_config.get("subWorkflow")
        if not sub_wf:
            return NodeResult(data=[[]])
        try:
            from engine.executor import WorkflowExecutor
            print(f"[SubWorkflowNode] Executing sub-workflow for node '{context.node_name}'")
            sub_executor = WorkflowExecutor(sub_wf, mode=context.mode, global_config=context.global_config)
            sub_result = sub_executor.execute_workflow()
            return NodeResult(data=[[{"subRunData": sub_result.get("runData", {})}]])
        except Exception as e:
            print(f"[SubWorkflowNode] Error executing sub-workflow: {e}")
            return NodeResult(data=[[]], error=str(e))
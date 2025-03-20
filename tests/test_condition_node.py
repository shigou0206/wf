# tests/test_condition_node.py

import pytest
from graph.models.wf_model_old import Workflow, Node, ConnectionInfo
from engine.executor import WorkflowExecutor
from engine.node_types import ConditionNodeType

def test_condition_node():
    """
    测试 ConditionNodeType：
    - 当输入数据中包含 {"pass": True} 与 {"pass": False} 的项时，
      应分别分到两个输出分支，并在输出数据中标记 processedBy 和 branch。
    """
    # 构造 Condition 节点，类型为 "condition"（_get_node_type_logic 会返回 ConditionNodeType）
    condition_node = Node("CondNode", "condition", parameters={})
    # 模拟下游节点（这里不实际执行，只用于构建连接）
    dummy_node = Node("Dummy", "processor", parameters={})
    
    # 构造连接：CondNode 的输出分支 0 连接到 Dummy（仅用于后续数据传递，测试主要关注 CondNode 的输出）
    connections = {
        "CondNode": {
            "main": [
                [ConnectionInfo("Dummy", "main", 0)],  # 输出分支 0
                []  # 输出分支 1 没有连接
            ]
        }
    }
    
    # 构造工作流：包含 CondNode 和 Dummy 节点
    wf = Workflow("wfCond", "Condition Test", [condition_node, dummy_node], connections, active=True)
    
    # 构造测试输入数据：2 条数据，其中一条 pass=True，一条 pass=False
    input_data = [
        {"id": 1, "pass": True, "val": "A"},
        {"id": 2, "pass": False, "val": "B"}
    ]
    
    # 创建 WorkflowExecutor，并通过新增参数 start_inputs 传入初始输入数据
    executor = WorkflowExecutor(wf, mode="manual")
    result = executor.execute_workflow(
        start_node_names=["CondNode"],
        start_inputs={"CondNode": input_data}
    )
    
    # 检查运行结果
    run_data = result["runData"]
    assert "CondNode" in run_data
    # 获取第一次执行的结果（注意：NodeResult 的 repr 可能不够直观，实际项目中建议解析结构化数据）
    cond_run_repr = run_data["CondNode"][0]
    print("ConditionNode result:", cond_run_repr)
    
    # 断言输出不为空，并且应包含 "branch" 字段信息，说明节点对输入做了判断
    # 此处简单断言 repr 字符串中包含 "branch" 以及 "CondNode"
    assert "branch" in cond_run_repr
    assert "CondNode" in cond_run_repr
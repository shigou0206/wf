# tests/test_partial_execution.py

import pytest
from graph.models.wf_model_old import Workflow, Node, ConnectionInfo
from engine.executor import WorkflowExecutor

def test_partial_execution_destination():
    """
    测试仅执行 NodeC 及其所有上游节点
    假设:
      NodeA -> NodeB -> NodeC
      NodeD -> NodeX (不相关)
    """
    # 构造节点
    nA = Node("NodeA", "producer")
    nB = Node("NodeB", "processor")
    nC = Node("NodeC", "processor")
    nD = Node("NodeD", "producer")
    nX = Node("NodeX", "processor")

    # 连接: A->B->C, D->X
    connections = {
        "NodeA": {
            "main": [
                [ConnectionInfo("NodeB","main",0)]
            ]
        },
        "NodeB": {
            "main": [
                [ConnectionInfo("NodeC","main",0)]
            ]
        },
        "NodeD": {
            "main": [
                [ConnectionInfo("NodeX","main",0)]
            ]
        }
    }

    wf = Workflow("wfPartial","PartialTest",[nA,nB,nC,nD,nX], connections, True)
    executor = WorkflowExecutor(wf, mode="manual")

    # 只执行 NodeC + 其祖先 => subgraph={NodeA,NodeB,NodeC}
    result = executor.execute_workflow(destination_node="NodeC")

    # 验证
    assert result["status"] == "SUCCESS"

    run_data = result["runData"]
    # NodeD, NodeX 不应该出现 => not in runData
    assert "NodeD" not in run_data
    assert "NodeX" not in run_data

    # NodeA, NodeB, NodeC 应该出现
    assert "NodeA" in run_data
    assert "NodeB" in run_data
    assert "NodeC" in run_data

    # Producer NodeA 在无输入时会产出1条(模拟外部数据)
    # B,C pass-through => 最终C可见 processedBy=NodeA, NodeB
    nodeC_runs = run_data["NodeC"]
    # nodeC_runs 是 NodeResult 列表
    # nodeC_runs[0] => <NodeResult data=[[...]]...>
    # 断言 "NodeA" 或 "NodeB" 出现在那里面

    data_str = nodeC_runs[0]  # 字符串 repr
    print("NodeC data =>", data_str)
    assert "NodeA" in data_str or "NodeB" in data_str, "Expect partial execution includes A,B => C"
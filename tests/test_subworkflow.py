# tests/test_subworkflow.py

import pytest
from graph.workflow import Workflow, Node, ConnectionInfo
from engine.executor import WorkflowExecutor
from engine.node_types import ExecuteSubWorkflowNode, ProducerNodeType

def test_execute_subworkflow_node():
    """
    测试 ExecuteSubWorkflowNode:
      - 子工作流包含一个 Producer 节点，该节点在无输入时产生数据。
      - ExecuteSubWorkflowNode 通过 global_config["subWorkflow"] 获取子工作流，
        执行后返回子工作流的 runData 作为输出。
    """
    # 构造子工作流：
    # 子工作流只有一个 Producer 节点（起始节点）
    sub_node = Node("SubProducer", "producer", parameters={})
    # 子工作流无连接
    sub_connections = {}
    sub_wf = Workflow("subWf", "Sub Workflow", [sub_node], sub_connections, active=True)

    # 构造 ExecuteSubWorkflowNode 节点
    subwf_node = Node("SubWorkflowNode", "executeSubWorkflow", parameters={})
    # 模拟下游节点，连接 ExecuteSubWorkflowNode 输出到 Dummy
    dummy_node = Node("Dummy", "processor", parameters={})
    connections = {
        "SubWorkflowNode": {
            "main": [
                [ConnectionInfo("Dummy", "main", 0)]
            ]
        }
    }
    # 构造主工作流，包含 ExecuteSubWorkflowNode 和 Dummy 节点
    wf = Workflow("wfMain", "Main Workflow", [subwf_node, dummy_node], connections, active=True)

    # 在 global_config 中注入子工作流
    global_config = {"subWorkflow": sub_wf}

    executor = WorkflowExecutor(wf, mode="manual", global_config=global_config)
    # 为确保执行 ExecuteSubWorkflowNode, 直接从它开始执行
    result = executor.execute_workflow(start_node_names=["SubWorkflowNode"])
    
    # 检查结果:
    # ExecuteSubWorkflowNode 的输出数据应包含子工作流的 runData（这里简单测试返回值包含 "SubProducer"）
    run_data = result["runData"]
    assert "SubWorkflowNode" in run_data
    subwf_run_repr = run_data["SubWorkflowNode"][0]
    print("SubWorkflowNode run:", subwf_run_repr)
    # 如果 Producer 节点在无输入时返回 "Data from SubProducer" 等信息，则检测之
    assert "SubProducer" in subwf_run_repr
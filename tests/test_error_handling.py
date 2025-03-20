# tests/test_error_handling.py

import pytest
from graph.models.wf_model_old import Workflow, Node, ConnectionInfo
from engine.executor import WorkflowExecutor
from engine.models import ExecutionError, NodeResult

def test_retry_on_fail():
    """
    NodeA(会抛异常前2次), onError=retryOnFail, maxRetries=2 => 第三次成功 => NodeB 后续执行
    """
    def failing_execute(context):
        call_count = context.global_config.setdefault("A_calls",0)
        print(f"[debug] call_count before inc => {call_count}")
        context.global_config["A_calls"] = call_count+1
        new_count = context.global_config["A_calls"]
        print(f"[debug] call_count after inc => {new_count}")
        if call_count<2:
            raise Exception("Simulated error")
        print("[debug] => returning success NodeResult")
        return NodeResult(data=[[{"msg":"OK after retries"}]])

    # mock NodeType
    from engine.node_types import NodeType
    class FailingNodeType(NodeType):
        def execute(self, context):
            return failing_execute(context)

    # NodeA => failing node
    nA = Node("NodeA","failing", parameters={
        "onError":"retryOnFail","maxRetries":2,"retryDelay":0
    })
    nB = Node("NodeB","processor")

    connections = {
        "NodeA":{
            "main":[ [ConnectionInfo("NodeB","main",0)] ]
        }
    }
    wf = Workflow("wfErrTest","ErrTest",[nA,nB], connections, True)
    executor = WorkflowExecutor(wf, mode="manual", global_config={})

    # patch _get_node_type_logic for NodeA
    def custom_get_node_type_logic(node):
        if node.name=="NodeA":
            return FailingNodeType(name=node.type)
        return executor._get_node_type_logic_orig(node)

    # monkey-patch
    executor._get_node_type_logic_orig = executor._get_node_type_logic
    executor._get_node_type_logic = custom_get_node_type_logic

    result = executor.execute_workflow()

    assert result["status"] == "SUCCESS"
    rd = result["runData"]
    assert "NodeA" in rd
    # check calls
    assert executor.global_config["A_calls"] == 3  # 2 fails + 1 success
    # NodeB got some data
    assert "NodeB" in rd
# tests/test_engine.py

import pytest
from graph.workflow import Workflow, Node, ConnectionInfo
from engine.executor import WorkflowExecutor

def create_multi_input_workflow():
    """
    构造一个简单的多输入场景：
    NodeA -> NodeC (inputIndex=0)
    NodeB -> NodeC (inputIndex=1)
    NodeC.type='merge'
    """
    nodeA = Node("NodeA", node_type="producer", disabled=False)
    nodeB = Node("NodeB", node_type="producer", disabled=False)
    nodeC = Node("NodeC", node_type="merge", disabled=False)

    connections_by_source = {
        "NodeA": {
            "main": [
                [ConnectionInfo("NodeC", "main", 0)]
            ]
        },
        "NodeB": {
            "main": [
                [ConnectionInfo("NodeC", "main", 1)]
            ]
        }
    }

    wf = Workflow(
        workflow_id="wf_multi_input",
        name="TestMultiInputWorkflow",
        nodes=[nodeA, nodeB, nodeC],
        connections_by_source_node=connections_by_source,
        active=True,
    )
    return wf

@pytest.mark.parametrize("start_nodes", [
    (["NodeA"]),       # 只启动 A
    (["NodeB"]),       # 只启动 B
    (["NodeA","NodeB"])# 同时启动 A,B
])
def test_multi_input_merge(start_nodes):
    """
    测试多种启动方式，以观察 NodeC 是否能在一次执行中拿到 A,B 的数据合并。
    """
    wf = create_multi_input_workflow()
    executor = WorkflowExecutor(wf, mode="manual")
    
    # 执行：传入多个 start_nodes => 同时启动
    # 如果只传一个，就只启动那一个
    result = executor.execute_workflow(start_node_names=start_nodes)
    print(f"Result after starting {start_nodes} =>", result)

    # 断言执行成功
    assert result["status"] == "SUCCESS"

    # 查看 runData
    runData = result["runData"]
    
    # 1) 当只启动 "NodeA" => NodeB 不会执行 => NodeC 也仅收到 NodeA 的数据(或空)
    # 2) 当只启动 "NodeB" => NodeA 不会执行 => NodeC 也仅收到 NodeB 的数据(或空)
    # 3) 当启动 ["NodeA","NodeB"] => NodeC 同时拿到 inputIndex=0,1 => 多输入合并
    
    if set(start_nodes) == {"NodeA"}:
        # NodeB 未执行 => NodeC 未收到 B => 可能 NodeC 并不执行 if it needs 2 inputs
        # or NodeC 只拿到 inputIndex=0
        # 仅断言 不报错
        assert "NodeA" in runData
        # NodeB, NodeC 不一定出现
    elif set(start_nodes) == {"NodeB"}:
        # 同理
        assert "NodeB" in runData
    else:
        # 同时启动 A,B => NodeC 应该执行
        # check NodeC in runData
        assert "NodeA" in runData
        assert "NodeB" in runData
        assert "NodeC" in runData, "NodeC should run if A,B both started"

        # NodeC 的执行结果
        # runData["NodeC"] 是个列表，每个元素是 <NodeResult data=... error=None>
        nodeC_runs = runData["NodeC"]
        assert len(nodeC_runs) > 0, "NodeC should have at least one run"
        
        # 查看 NodeC 第一次执行
        # 形如 '<NodeResult data=[[...items..]], error=None>'
        # 这里可进一步检查合并后的数据
        c_run_data_str = nodeC_runs[0]
        # 你可用 assert "processedBy" in c_run_data_str 等
        # 但要注意它是字符串repr
        assert "NodeA" in c_run_data_str or "NodeB" in c_run_data_str, \
            "Expect NodeC to contain items from A or B"

    # 整个测试的结论: 不同启动方式下, NodeC 行为不同


def test_no_start_node():
    """
    如果不指定任何 start_node_names,
    则 Executor 若是 n8n 风格, 会查找 "无父节点" 或 "trigger" 一起启动.
    这里 NodeA,NodeB 都无父 => 都会被执行 => NodeC 也能合并
    """
    wf = create_multi_input_workflow()
    executor = WorkflowExecutor(wf, mode="manual")
    # 不传 start_node_names => auto
    result = executor.execute_workflow()  # 由 executor._find_start_nodes() 找
    print("Result with no explicit start =>", result)
    assert result["status"] == "SUCCESS"
    runData = result["runData"]

    # NodeA,NodeB 都应该出现, NodeC 也应该出现
    assert "NodeA" in runData
    assert "NodeB" in runData
    assert "NodeC" in runData, "C should have run with 2 inputs"
# tests/test_workflow.py

import pytest
from graph.models.wf_model_old import Workflow, Node, ConnectionInfo

def test_rename_node():
    """
    测试 rename_node 同时替换表达式:
      - 原引用如 `$node["NodeA"]`, `$items("NodeA")` 应替换成 `$node["NodeA_new"]`, `$items("NodeA_new")`
      - 并非简单地让 "NodeA" 从字符串中消失, 而是旧引用不再出现
    """
    nA = Node("NodeA", "processor", parameters={
        "someExpr": '$node["NodeA"].data + $items("NodeA")'
    })
    nB = Node("NodeB", "processor")
    connections = {
        "NodeA": {
            "main": [
                [ConnectionInfo("NodeB", "main", 0)]
            ]
        }
    }
    wf = Workflow("wf1", "RenameTest", [nA, nB], connections, True)

    # rename NodeA => NodeA_new
    wf.rename_node("NodeA", "NodeA_new")

    # 1) 检查 nodes dict
    assert "NodeA" not in wf.nodes
    assert "NodeA_new" in wf.nodes

    # 2) 检查表达式
    nodeA_new = wf.get_node("NodeA_new")
    expr = nodeA_new.parameters["someExpr"]
    print("Final expr =>", expr)

    # 验证 "旧形式引用" 已去除:
    #   `$node["NodeA"]` / `$items("NodeA")` 不再出现
    # 而出现 `$node["NodeA_new"]` / `$items("NodeA_new")`
    # 
    # 方法1: 只要不出现 `$node["NodeA"]` / `$items("NodeA")`
    assert '$node["NodeA"]' not in expr
    assert '$items("NodeA")' not in expr

    # 方法2: 如果要断言任何 `$node. + oldName`
    assert '$node.NodeA' not in expr

    # 同时确认新名出现
    assert "NodeA_new" in expr
    assert '$items("NodeA_new")' in expr
    assert '$node["NodeA_new"]' in expr

def test_dfs_child_nodes():
    """
    测试 get_child_nodes (DFS)
    """
    nA = Node("NodeA", "processor")
    nB = Node("NodeB", "processor")
    nC = Node("NodeC", "processor")
    nD = Node("NodeD", "processor")

    # A->B, A->C, B->D
    connections = {
        "NodeA": {
            "main": [
                [ConnectionInfo("NodeB", "main", 0), ConnectionInfo("NodeC", "main", 0)]
            ]
        },
        "NodeB": {
            "main": [
                [ConnectionInfo("NodeD", "main", 0)]
            ]
        }
    }
    wf = Workflow("wf2", "DFS", [nA, nB, nC, nD], connections)

    children_of_A = wf.get_child_nodes("NodeA")
    # 期望 B,C,D 都出现
    assert set(children_of_A) == {"NodeB","NodeC","NodeD"}

def test_bfs_child_nodes():
    """
    测试 get_child_nodes_bfs (BFS)
    """
    nA = Node("NodeA","processor")
    nB = Node("NodeB","processor")
    nC = Node("NodeC","processor")
    nD = Node("NodeD","processor")

    # A->B, A->C, B->D
    connections = {
        "NodeA": {
            "main": [
                [ConnectionInfo("NodeB","main",0), ConnectionInfo("NodeC","main",0)]
            ]
        },
        "NodeB": {
            "main": [
                [ConnectionInfo("NodeD","main",0)]
            ]
        }
    }
    wf = Workflow("wf3","BFS", [nA,nB,nC,nD], connections)

    bfs_children = wf.get_child_nodes_bfs("NodeA")
    # BFS 顺序不可完全保证. 但至少检查包含B,C,D
    assert set(bfs_children) == {"NodeB","NodeC","NodeD"}

def test_parent_nodes():
    """
    测试 get_parent_nodes
    """
    nA = Node("NodeA","processor")
    nB = Node("NodeB","processor")
    nC = Node("NodeC","processor")

    # A->B, B->C
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
        }
    }
    wf = Workflow("wf4","ParentTest", [nA,nB,nC], connections)
    p_of_C = wf.get_parent_nodes("NodeC")  # DFS
    assert set(p_of_C) == {"NodeA","NodeB"}

def test_get_start_node():
    """
    测试 get_start_node
    """
    # NodeX => trigger, NodeY => no parent
    nX = Node("NodeX","trigger")
    nY = Node("NodeY","processor")
    nZ = Node("NodeZ","processor")

    # Y->Z
    connections = {
        "NodeY": {
            "main": [
                [ConnectionInfo("NodeZ","main",0)]
            ]
        }
    }
    wf = Workflow("wf5","StartTest", [nX,nY,nZ], connections)

    startNode = wf.get_start_node()
    # 优先找 trigger => NodeX
    assert startNode is not None
    assert startNode.name == "NodeX"

    # 如果 we disable NodeX
    nX.disabled = True
    newStart = wf.get_start_node()
    # NodeX 被禁用 => fallback => node without parent => Y
    assert newStart.name == "NodeY"
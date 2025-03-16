# main.py

from graph.workflow import Workflow, Node, ConnectionInfo
from engine.executor import WorkflowExecutor   

def main():
    # 构造节点
    nA = Node("NodeA", "trigger")
    nB = Node("NodeB", "switch")
    nC = Node("NodeC", "processor")
    nD = Node("NodeD", "processor")

    connections_by_source = {
        "NodeA": {
            "main": [
                [
                    ConnectionInfo("NodeB", "main", 0)
                ]
            ]
        },
        "NodeB": {
            "main": [
                [ConnectionInfo("NodeC", "main", 0)],
                [ConnectionInfo("NodeD", "main", 0)],
            ]
        }
    }

    wf = Workflow(
        workflow_id="wf1",
        name="TestWorkflowWithBranch",
        nodes=[nA, nB, nC, nD],
        connections_by_source_node=connections_by_source,
        active=True
    )

    executor = WorkflowExecutor(wf, mode="manual")
    result = executor.execute_workflow()
    print("Execution result =>", result)

if __name__ == "__main__":
    main()
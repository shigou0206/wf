from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Literal, Any
from datetime import datetime
from .data_model import NodeExecutionData
from .node_model import WorkflowNode

class ExecutionStatus(Enum):
    NEW = "new"
    RUNNING = "running"
    WAITING = "waiting"
    SUCCESS = "success"
    CANCELED = "canceled"
    ERROR = "error"

class WorkflowExecuteMode(Enum):
    CLI = "cli"
    ERROR = "error"
    INTEGRATED = "integrated"
    INTERNAL = "internal"
    MANUAL = "manual"
    RETRY = "retry"
    TRIGGER = "trigger"
    WEBHOOK = "webhook"
    EVALUATION = "evaluation"

TaskDataConnections = Dict[str, List[Optional[NodeExecutionData]]]

@dataclass
class TaskSubRunMetadata:
    """存储任务子运行的元数据"""
    node: str
    run_index: int

@dataclass
class RelatedExecution:
    """存储父/子执行的信息"""
    execution_id: str
    workflow_id: str

@dataclass
class TaskMetadata:
    """任务的元数据"""
    sub_run: Optional[List[TaskSubRunMetadata]] = field(default_factory=list)
    parent_execution: Optional[RelatedExecution] = None
    sub_execution: Optional[RelatedExecution] = None
    sub_executions_count: Optional[int] = None

@dataclass
class NodeHint:
    """存储节点的提示信息"""
    message: str
    type: Optional[Literal["info", "warning", "danger"]] = None
    location: Optional[Literal["outputPane", "inputPane", "ndv"]] = None
    display_condition: Optional[str] = None
    when_to_display: Optional[Literal["always", "beforeExecution", "afterExecution"]] = None

@dataclass
class NodeExecutionHint:
    """简化的 NodeHint 不包含 when_to_display 和 display_condition"""
    message: str
    type: Optional[Literal["info", "warning", "danger"]] = None
    location: Optional[Literal["outputPane", "inputPane", "ndv"]] = None

@dataclass
class SourceData:
    """存储任务数据连接的来源信息"""
    previous_node: str
    previous_node_output: Optional[int] = 0  # 默认为 0
    previous_node_run: Optional[int] = 0  # 默认为 0

TaskDataConnectionsSource = Dict[str, List[Optional[SourceData]]]

@dataclass
class ExecuteData:
    """存储执行数据，包括任务数据连接、元数据、当前节点信息"""
    data: TaskDataConnections
    node: WorkflowNode
    source: Optional[TaskDataConnectionsSource] = None
    metadata: Optional[TaskMetadata] = None

@dataclass
class PairedItemData:
    """表示配对的项数据，包含索引、输入和可能的来源覆盖"""
    item: int
    input: int = 0  # 默认为 0
    source_overwrite: Optional[SourceData] = None

@dataclass
class TaskData:
    """存储节点执行后的数据"""
    start_time: float
    execution_time: float
    execution_status: Optional[ExecutionStatus] = None
    data: Optional[TaskDataConnections] = None
    input_override: Optional[TaskDataConnections] = None
    error: Optional[str] = None
    hints: Optional[List[NodeExecutionHint]] = None
    source: List[Optional[SourceData]] = field(default_factory=list)
    metadata: Optional[TaskMetadata] = None

RunData = Dict[str, List[TaskData]] 

@dataclass
class StartNodeData:
    name: str
    source_data: Optional[SourceData] = None

ContextObject = Dict[str, Any]

# 存储执行上下文数据，key 可以是 "flow" 或 "node:<NODE_NAME>"
ExecuteContextData = Dict[str, ContextObject]

@dataclass
class RunExecutionData:
    start_data: Optional[StartNodeData] = None
    result_data: Dict[str, Any] = field(default_factory=lambda: {
        "error": None,
        "runData": {},
        "pinData": None,
        "lastNodeExecuted": None,
        "metadata": {},
    })
    execution_data: Optional[Dict[str, Any]] = field(default_factory=lambda: {
        "contextData": ExecuteContextData(),
        "nodeExecutionStack": [],
        "metadata": {},
        "waitingExecution": None,
        "waitingExecutionSource": None,
    })
    parent_execution: Optional[RelatedExecution] = None
    wait_till: Optional[datetime] = None
    push_ref: Optional[str] = None
    is_test_webhook: Optional[bool] = False
    manual_data: Optional[Dict[str, Any]] = None

@dataclass
class Run:
    data: RunExecutionData
    mode: str  # WorkflowExecuteMode 类型
    started_at: datetime
    stopped_at: Optional[datetime] = None
    status: ExecutionStatus = ExecutionStatus.NEW
    wait_till: Optional[datetime] = None

from __future__ import annotations

from typing import Any
from dataclasses import dataclass, field
from typing import Dict, Optional, Union, List, Literal

BinaryFileType = Literal["text", "json", "image", "audio", "video", "pdf", "html"]

@dataclass
class BinaryData:
    data: str
    mime_type: str
    file_type: Optional[BinaryFileType] = None
    file_name: Optional[str] = None
    directory: Optional[str] = None
    file_extension: Optional[str] = None
    file_size: Optional[int] = None
    id: Optional[str] = None

# Simplified: just a type alias for str -> BinaryData mapping
BinaryKeyData = Dict[str, BinaryData]

@dataclass
class RelatedExecution:
    sub_execution: Optional[RelatedExecution] = None

@dataclass
class SourceInfo:
    previous_node: Optional[str] = None
    previous_node_output: Optional[int] = None
    previous_node_run: Optional[int] = None

@dataclass
class PairedItem:
    item: int
    input: Optional[int] = None
    source_overwrite: Optional[SourceInfo] = None

@dataclass
class NodeExecutionData:
    json_data: object = field(default_factory=dict)
    binary: Optional[BinaryKeyData] = None
    error: Optional[str] = None
    paired_item: Optional[Union[PairedItem, List[PairedItem], int]] = None
    metadata: Optional[Dict[str, RelatedExecution]] = None
    extra: Dict[str, object] = field(default_factory=dict)

PinData = Dict[str, List[NodeExecutionData]]

NodeOutput = Union[
    List[List[NodeExecutionData]],
    None
]

CallerPolicy = Literal["any", "none", "workflowsFromAList", "workflowsFromSameOwner"]
SaveDataExecution = Literal["DEFAULT", "all", "none"]
DefaultOrBool = Union[Literal["DEFAULT"], bool]
ExecutionOrder = Literal["v0", "v1"]
TimezoneType = Union[Literal["DEFAULT"], str]

@dataclass
class WorkflowSettings:
    """
    Pythonic 版本，对应 IWorkflowSettings。
    使用 snake_case 命名，并用 Optional[...] 表示可选字段。
    """
    timezone: Optional[TimezoneType] = None
    error_workflow: Optional[str] = None
    caller_ids: Optional[str] = None
    caller_policy: Optional[CallerPolicy] = None
    save_data_error_execution: Optional[SaveDataExecution] = None
    save_data_success_execution: Optional[SaveDataExecution] = None
    save_manual_executions: Optional[DefaultOrBool] = None
    save_execution_progress: Optional[DefaultOrBool] = None
    execution_timeout: Optional[int] = None
    execution_order: Optional[ExecutionOrder] = None

ObservableObject = Dict[str, Any]

# Example usage
if __name__ == "__main__":
    bd = BinaryData(
        data="base64encoded==",
        mime_type="image/png",
        file_name="test.png",
        file_size=12345,
        file_type="image"
    )
    binary_map: BinaryKeyData = {"myImage": bd}

    ri = RelatedExecution()  # sub_execution=None
    si = SourceInfo(previous_node="NodeA", previous_node_output=0, previous_node_run=1)
    pi = PairedItem(item=42, input=0, source_overwrite=si)

    node_exec_data = NodeExecutionData(
        json_data={"some": "data"},
        binary=binary_map,
        error=None,
        paired_item=pi,
        metadata={"exec1": ri},
        extra={"arbitrary_field": 999}
    )

    print(node_exec_data)

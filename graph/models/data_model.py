from __future__ import annotations

from typing import Dict, Optional, Union, List, Literal, TypedDict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

class BinaryFileType(Enum):
    TEXT = "text"
    JSON = "json"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    PDF = "pdf"
    HTML = "html"

    @classmethod
    def from_string(cls, value: str) -> Optional["BinaryFileType"]:
        for item in cls:
            if item.value == value.lower():
                return item
        return None

@dataclass
class BinaryData:
    data: str
    mime_type: str
    file_type: Optional[BinaryFileType] = None
    file_name: Optional[str] = None
    directory: Optional[str] = None
    file_extension: Optional[str] = None
    file_size: int = 0
    id: Optional[str] = None

    def get_full_path(self) -> Optional[Path]:
        if self.directory and self.file_name:
            return Path(self.directory) / self.file_name
        return None

    def is_valid_file(self) -> bool:
        return bool(self.data and self.mime_type and self.file_name)

    def to_dict(self) -> dict:
        return {
            "data": self.data,
            "mime_type": self.mime_type,
            "file_type": self.file_type.value if self.file_type else None,
            "file_name": self.file_name,
            "directory": self.directory,
            "file_extension": self.file_extension,
            "file_size": self.file_size,
            "id": self.id
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BinaryData":
        return cls(
            data=data["data"],
            mime_type=data["mime_type"],
            file_type=BinaryFileType.from_string(data.get("file_type", "")),
            file_name=data.get("file_name"),
            directory=data.get("directory"),
            file_extension=data.get("file_extension"),
            file_size=data.get("file_size", 0),
            id=data.get("id"),
        )

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

class DisplayConditionDict(TypedDict):
    cnd: Dict[str, Union[str, int, bool, Dict[str, Union[str, int]]]]

@dataclass
class DisplayCondition:
    eq: Optional[Union[str, int]] = None
    not_eq: Optional[Union[str, int]] = None
    gte: Optional[Union[str, int]] = None
    lte: Optional[Union[str, int]] = None
    gt: Optional[Union[str, int]] = None
    lt: Optional[Union[str, int]] = None
    between: Optional[Dict[str, Union[str, int]]] = None
    startsWith: Optional[str] = None
    endsWith: Optional[str] = None
    includes: Optional[str] = None
    regex: Optional[str] = None
    exists: Optional[bool] = None

class DisplayOptionsDict(TypedDict, total=False):
    hide: Dict[str, List[DisplayConditionDict]]
    show: Dict[str, List[DisplayConditionDict]]
    hideOnCloud: bool


@dataclass
class DisplayOptions:
    hide: Optional[Dict[str, List[DisplayCondition]]] = None
    show: Optional[Dict[str, List[DisplayCondition]]] = None
    hideOnCloud: Optional[bool] = None

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

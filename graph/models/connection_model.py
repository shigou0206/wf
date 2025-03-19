from enum import Enum
from typing import NamedTuple, Dict, List, Optional

#
# 1. 定义 ConnectionType 枚举
#
class ConnectionType(Enum):
    AI_AGENT = "ai_agent"
    AI_CHAIN = "ai_chain"
    AI_DOCUMENT = "ai_document"
    AI_EMBEDDING = "ai_embedding"
    AI_LANGUAGE_MODEL = "ai_languageModel"
    AI_MEMORY = "ai_memory"
    AI_OUTPUT_PARSER = "ai_outputParser"
    AI_RETRIEVER = "ai_retriever"
    AI_TEXT_SPLITTER = "ai_textSplitter"
    AI_TOOL = "ai_tool"
    AI_VECTOR_STORE = "ai_vectorStore"
    MAIN = "main"


#
# 2. 定义 EdgeConnection (对应 INodeConnection: sourceIndex / destinationIndex)
#
class EdgeConnection(NamedTuple):
    """
    表示节点之间的边或连接的索引信息。
    对应 TypeScript 中的 INodeConnection:
      sourceIndex: number;
      destinationIndex: number;
    """
    source_index: int
    destination_index: int


#
# 3. 定义 NodeConnection
#
class NodeConnection(NamedTuple):
    """
    旧有的“节点连接”信息，与 EdgeConnection 并不冲突。
    包含节点名称、连接类型、以及该连接在目标节点输入/输出列表中的 index。
    """
    node: str
    connection_type: ConnectionType
    index: int


#
# 4. 定义若干别名以表示更复杂的结构
#

# NodeInputConnections 是二维列表（每个元素可以是 None 或 NodeConnection 列表）
NodeInputConnections = List[Optional[List[NodeConnection]]]

# NodeConnections: 一个字符串(key) -> NodeInputConnections 的映射
NodeConnections = Dict[str, NodeInputConnections]

# Connections: 最外层再包一层字符串(key) -> NodeConnections
Connections = Dict[str, NodeConnections]
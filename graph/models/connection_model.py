from enum import Enum
from typing import NamedTuple, Dict, List, Optional

class ConnectionType(str,Enum):
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


class EdgeConnection(NamedTuple):
    source_index: int
    destination_index: int


class NodeConnection(NamedTuple):
    node: str
    connection_type: ConnectionType
    index: int


NodeInputConnections = List[Optional[List[NodeConnection]]]
NodeConnections = Dict[str, NodeInputConnections]

Connections = Dict[str, NodeConnections]
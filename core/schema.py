# core/schema.py
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    BASIC = "basic"    # 基本概念
    ROLE = "role"      # ロール概念

class AccessLevel(str, Enum):
    LOCKED = "locked"  # 編集不可（AIも変更不可）
    VERIFY = "verify"  # 要承認
    OPEN = "open"      # 自由編集

class KnowledgeNode(BaseModel):
    id: str
    label: str
    type: NodeType
    layer: str
    parent_id: Optional[str] = None  # 親概念へのリンク
    context: Optional[str] = None    # ロール概念の場合の文脈
    attributes: Dict[str, str] = Field(default_factory=dict)

class LayerConfig(BaseModel):
    name: str
    access: AccessLevel
    description: str

class OntologyModel(BaseModel):
    nodes: Dict[str, KnowledgeNode] = {}
    layers: Dict[str, LayerConfig] = {}
    
    def add_node(self, node: KnowledgeNode):
        self.nodes[node.id] = node

    def get_nodes_by_layer(self, layer_name: str) -> List[KnowledgeNode]:
        return [n for n in self.nodes.values() if n.layer == layer_name]
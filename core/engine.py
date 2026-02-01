import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from core.schema import OntologyModel, KnowledgeNode, NodeType, AccessLevel

load_dotenv()

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

class AIResponseData(BaseModel):
    label: str
    type: Literal["basic", "role"]
    context: Optional[str] = None
    parent_id: Optional[str] = None

class AIResponse(BaseModel):
    action: str = "ADD"
    layer: str = "User"
    data: AIResponseData
    suggestions: List[str] = []

class HozoEngine:
    def __init__(self, model: OntologyModel):
        self.model = model
        # 新SDK用のクライアント初期化
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        
        # システム命令の定義
        self.system_instruction = """
        あなたは法造(Hozo)オントロジーの専門家です。
        ユーザーの入力を解析し、指定されたJSONスキーマに従って結果を返してください。
        - 概念名(label)、タイプ(basic または role)、レイヤー、親概念のIDを抽出してください。
        - 追加の提案(suggestions)も提供してください。
        """
        
        # 自動モデル選択ロジック (2026年仕様)
        self.model_id = self._find_best_model()

    def _find_best_model(self):
        """利用可能な最新のFlashモデルを特定する"""
        try:
            # list_models() を使用して最新モデルを確認
            for m in self.client.models.list():
                if "gemini-2.5-flash" in m.name:
                    return m.name
            return "gemini-2.5-flash"
        except:
            return "gemini-2.5-flash"

    def execute(self, user_input: str):
        try:
            # 新SDKでの生成リクエスト (response_schemaを指定して型安全に)
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=f"解析せよ: {user_input}",
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    response_mime_type="application/json",
                    response_schema=AIResponse,
                    temperature=0.1
                )
            )
            
            # レスポンスの解析
            if not response.parsed:
                if response.text:
                    res_dict = json.loads(response.text)
                    res = AIResponse(**res_dict)
                else:
                    raise ValueError("AIからの応答が空です。セーフティフィルタでブロックされた可能性があります。")
            else:
                res = response.parsed
            
            target_layer = res.layer
            node_id = f"node_{len(self.model.nodes) + 1}"
            
            new_node = KnowledgeNode(
                id=node_id,
                label=res.data.label,
                type=NodeType(res.data.type),
                layer=target_layer,
                context=res.data.context,
                parent_id=res.data.parent_id
            )
            
            self.model.add_node(new_node)
            return {
                "status": "success", 
                "node": new_node, 
                "action": res.action,
                "suggestions": res.suggestions
            }

        except Exception as e:
            return {"status": "error", "message": f"API Error: {str(e)}"}
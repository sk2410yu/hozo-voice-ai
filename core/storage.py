import json
import os
from datetime import datetime

class OntologyStorage:
    def __init__(self, file_path="data/ontology_model.json"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def save(self, data_dict: dict):
        """JSON形式でモデルを保存"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=4, ensure_ascii=False)

    def load(self) -> dict:
        """保存されたモデルをロード。なければ初期値を返す"""
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"nodes": {}, "layers": {}}
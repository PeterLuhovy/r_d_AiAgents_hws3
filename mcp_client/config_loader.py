import json
from pathlib import Path

class Config:
    def __init__(self):
        config_file = Path(__file__).parent / "config.json"
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.model = data.get("model", "gpt-4o-mini")
                self.system_prompt = data.get("system_prompt", "You are a helpful assistant. Respond in Slovak.")
                print(f"✅ Config loaded: {self.model}")
        except Exception as e:
            print(f"⚠️ Config error: {e}, using defaults")
            self.model = "gpt-4o-mini"
            self.system_prompt = "You are a helpful assistant. Respond in Slovak."

# Global config instance
config = Config()
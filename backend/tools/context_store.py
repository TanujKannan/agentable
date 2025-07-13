# context_store.py
from typing import Any

class RunContext:
    def __init__(self):
        self.store = {}

    def set(self, key: str, value: Any):
        if key and key.strip():  # Don't store empty or whitespace-only keys
            self.store[key] = value
        else:
            print(f"⚠️  Warning: Attempted to store value with empty key: '{key}'")

    def get(self, key: str):
        return self.store.get(key)

    def all(self):
        return self.store

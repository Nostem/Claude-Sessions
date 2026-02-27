import hashlib, json, os

class StateManager:
    def __init__(self, path: str):
        self.path = path
        self._set = self._load()

    def _load(self) -> set:
        if os.path.exists(self.path):
            with open(self.path) as f:
                return set(json.load(f).get("processed", []))
        return set()

    def _save(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w") as f:
            json.dump({"processed": list(self._set)}, f, indent=2)

    def _hash(self, date, tag, arg) -> str:
        return hashlib.sha256(f"{date}|{tag.lower()}|{arg.lower().strip()}".encode()).hexdigest()

    def is_processed(self, date, tag, arg) -> bool:
        return self._hash(date, tag, arg) in self._set

    def mark_processed(self, date, tag, arg):
        self._set.add(self._hash(date, tag, arg))
        self._save()

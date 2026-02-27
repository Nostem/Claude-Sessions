import os

class Memory:
    def __init__(self, path: str, max_lines: int = 100):
        self.path = path
        self.max_lines = max_lines

    def read_context(self) -> str:
        if not os.path.exists(self.path):
            return ""
        with open(self.path) as f:
            lines = f.readlines()
        recent = [l for l in lines if l.strip()][-self.max_lines:]
        return "".join(recent)

    def append(self, date: str, tag: str, argument: str, summary: str):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a") as f:
            f.write(f"{date} | {tag} | \"{argument}\" → {summary}\n")

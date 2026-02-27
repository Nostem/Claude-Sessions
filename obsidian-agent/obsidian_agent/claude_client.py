import anthropic

class ClaudeClient:
    def __init__(self, api_key: str, system_md_path: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        with open(system_md_path) as f:
            self.system = f.read()

    def call(self, prompt: str, memory_context: str) -> str:
        full = prompt
        if memory_context.strip():
            full = f"## Recent session memory\n\n{memory_context}\n\n---\n\n{prompt}"
        resp = self.client.messages.create(
            model=self.model, max_tokens=2048,
            system=self.system,
            messages=[{"role": "user", "content": full}]
        )
        return resp.content[0].text

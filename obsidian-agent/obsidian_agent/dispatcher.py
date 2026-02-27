from obsidian_agent.handlers.research import handle_research
from obsidian_agent.handlers.writingprompt import handle_writingprompt
from obsidian_agent.handlers.reflect import handle_reflect
from obsidian_agent.handlers.book import handle_book

_HANDLER_NAMES = {
    "research": "handle_research",
    "writingprompt": "handle_writingprompt",
    "reflect": "handle_reflect",
    "book": "handle_book",
}

def dispatch(tag: str, argument: str, config: dict, memory_context: str, date: str):
    name = _HANDLER_NAMES.get(tag.lower())
    if name:
        handler = globals()[name]
        handler(argument, config, memory_context=memory_context, date=date)

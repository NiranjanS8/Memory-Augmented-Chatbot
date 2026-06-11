from backend.memory.types import MemoryRecord, MemoryType


def build_system_prompt(
    memories: list[MemoryRecord],
    model_name: str,
    tools_available: list[str] | None = None,
) -> str:
    """Build a system prompt with injected memories for an LLM call.

    Separates semantic facts from episodic summaries and formats them
    into sections the model can reference naturally. Superseded memories
    (confidence <= 0.1) are excluded.
    """
    active_memories = [m for m in memories if m.confidence > 0.1]

    semantic_facts = [
        m for m in active_memories if m.memory_type == MemoryType.SEMANTIC
    ]
    episodic_summaries = [
        m for m in active_memories if m.memory_type == MemoryType.EPISODIC
    ]

    memory_block = _format_memory_block(semantic_facts, episodic_summaries)
    tools_block = _format_tools_block(tools_available)

    return _SYSTEM_TEMPLATE.format(
        memory_block=memory_block,
        tools_block=tools_block,
        model_name=model_name,
    ).strip()


def _format_memory_block(
    semantic: list[MemoryRecord],
    episodic: list[MemoryRecord],
) -> str:
    if not semantic and not episodic:
        return ""

    sections: list[str] = []

    if semantic:
        facts_str = "\n".join(f"- {m.content}" for m in semantic)
        sections.append(f"## What I know about you\n{facts_str}")

    if episodic:
        episodes_str = "\n".join(
            f"- [{m.source_session or 'previous'}] {m.content}"
            for m in episodic
        )
        sections.append(f"## Our previous conversations\n{episodes_str}")

    return "\n\n".join(sections)


def _format_tools_block(tools: list[str] | None) -> str:
    if not tools:
        return ""
    tool_list = "\n".join(f"- {t}" for t in tools)
    return f"\n\n## Available tools\n{tool_list}"


_SYSTEM_TEMPLATE = """\
You are a helpful, context-aware assistant with persistent memory.

{memory_block}
{tools_block}

Use the above memories naturally — don't announce them or say "I remember that...".
Just use the context to give better, more personalized responses.
If a user corrects a memory, acknowledge it and update your understanding.

Current model: {model_name}"""

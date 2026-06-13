"""
Evaluation harness for cross-session memory recall.

Simulates session-1 conversations to build memories, then asks a fresh
session-2 question and uses LLM-as-judge to score whether expected facts
were recalled.  Target: >= 75 % recall.

Usage:
    python -m backend.eval.run_eval
"""

import asyncio
import json
import sys
from pathlib import Path

import openai

from backend.config import settings, get_model
from backend.memory.manager import MemoryManager
from backend.prompts.system import build_system_prompt
from backend.models.base import Message

EVAL_DATA = Path(__file__).parent / "test_sessions.json"
JUDGE_MODEL = "gpt-4o-mini"
TEST_USER_ID = "__eval_harness__"


def _load_test_cases() -> list[dict]:
    with open(EVAL_DATA) as f:
        return json.load(f)


JUDGE_PROMPT = """\
You are a strict evaluator.  Given a chatbot response and a list of expected \
facts, determine which facts are present in the response.

Return a JSON object: {{"scores": [1, 0, ...]}} where 1 means the fact is \
clearly present and 0 means it is missing or wrong.  The list must have the \
same length as the expected_facts list.  No explanation needed.

Expected facts:
{expected_facts}

Chatbot response:
{response}
"""


def _judge_recall(
    response: str,
    expected_facts: list[str],
    client: openai.OpenAI,
) -> list[int]:
    prompt = JUDGE_PROMPT.format(
        expected_facts=json.dumps(expected_facts),
        response=response,
    )
    completion = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=128,
    )
    parsed = json.loads(completion.choices[0].message.content)
    scores = parsed.get("scores", [0] * len(expected_facts))
    if len(scores) != len(expected_facts):
        return [0] * len(expected_facts)
    return scores


async def _run_case(case: dict, judge_client: openai.OpenAI) -> dict:
    memory_mgr = MemoryManager(TEST_USER_ID)

    for turn in case["session_1"]:
        await memory_mgr.save_turn(
            user_message=turn["user"],
            assistant_message=turn["assistant"],
            source_session=f"eval_{case['id']}_s1",
        )

    await asyncio.sleep(0.5)

    memories = memory_mgr.get_context(case["session_2_query"])
    system_prompt = build_system_prompt(memories, "openai")

    llm = get_model("openai")
    messages = [Message(role="user", content=case["session_2_query"])]
    response = llm.chat(messages, system=system_prompt)

    scores = _judge_recall(response, case["expected_facts"], judge_client)

    memory_mgr.clear_memories()

    recalled = sum(scores)
    total = len(scores)
    return {
        "id": case["id"],
        "category": case["category"],
        "query": case["session_2_query"],
        "response": response[:200],
        "scores": scores,
        "recalled": recalled,
        "total": total,
        "pass": recalled / total >= 0.5,
    }


async def main():
    cases = _load_test_cases()
    judge_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    print(f"Running {len(cases)} eval cases...\n")

    results = []
    total_recalled = 0
    total_facts = 0

    for case in cases:
        result = await _run_case(case, judge_client)
        results.append(result)
        total_recalled += result["recalled"]
        total_facts += result["total"]

        status = "PASS" if result["pass"] else "FAIL"
        pct = result["recalled"] / result["total"] * 100
        print(f"  [{status}] {result['id']}: {result['recalled']}/{result['total']} ({pct:.0f}%)")

    recall_pct = (total_recalled / total_facts * 100) if total_facts else 0
    print(f"\nOverall recall: {total_recalled}/{total_facts} ({recall_pct:.1f}%)")
    print(f"Target: >= 75%  —  {'PASSED' if recall_pct >= 75 else 'FAILED'}")

    report_path = Path(__file__).parent / "eval_results.json"
    with open(report_path, "w") as f:
        json.dump({"results": results, "recall_pct": recall_pct}, f, indent=2)
    print(f"\nDetailed results written to {report_path}")

    return recall_pct >= 75


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

"""
workers/policy_tool.py â Policy & Tool Worker
Sprint 2+3: Kiá»m tra policy dá»±a vÃ o context, gá»i MCP tools khi cáº§n.

Input (tá»« AgentState):
    - task: cÃ¢u há»i
    - retrieved_chunks: context tá»« retrieval_worker
    - needs_tool: True náº¿u supervisor quyáº¿t Äá»nh cáº§n tool call

Output (vÃ o AgentState):
    - policy_result: {"policy_applies", "policy_name", "exceptions_found", "source", "rule"}
    - mcp_tools_used: list of tool calls ÄÃ£ thá»±c hiá»n
    - worker_io_log: log

Gá»i Äá»c láº­p Äá» test:
    python workers/policy_tool.py
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

WORKER_NAME = "policy_tool_worker"


# âââââââââââââââââââââââââââââââââââââââââââââ
# MCP Client â Sprint 3: Thay báº±ng real MCP call
# âââââââââââââââââââââââââââââââââââââââââââââ

def _call_mcp_tool(tool_name: str, tool_input: dict) -> dict:
    """
    Gá»i MCP tool.

    Sprint 3 TODO: Implement báº±ng cÃ¡ch import mcp_server hoáº·c gá»i HTTP.

    Hiá»n táº¡i: Import trá»±c tiáº¿p tá»« mcp_server.py (trong-process mock).
    """
    from datetime import datetime

    try:
        # TODO Sprint 3: Thay báº±ng real MCP client náº¿u dÃ¹ng HTTP server
        from mcp_server import dispatch_tool
        result = dispatch_tool(tool_name, tool_input)
        return {
            "tool": tool_name,
            "input": tool_input,
            "output": result,
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "tool": tool_name,
            "input": tool_input,
            "output": None,
            "error": {"code": "MCP_CALL_FAILED", "reason": str(e)},
            "timestamp": datetime.now().isoformat(),
        }


# âââââââââââââââââââââââââââââââââââââââââââââ
# Policy Analysis Logic
# âââââââââââââââââââââââââââââââââââââââââââââ

def analyze_policy(task: str, chunks: list) -> dict:
    """
    PhÃ¢n tÃ­ch policy dá»±a trÃªn context chunks.

    TODO Sprint 2: Implement logic nÃ y vá»i LLM call hoáº·c rule-based check.

    Cáº§n xá»­ lÃ½ cÃ¡c exceptions:
    - Flash Sale â khÃ´ng ÄÆ°á»£c hoÃ n tiá»n
    - Digital product / license key / subscription â khÃ´ng ÄÆ°á»£c hoÃ n tiá»n
    - Sáº£n pháº©m ÄÃ£ kÃ­ch hoáº¡t â khÃ´ng ÄÆ°á»£c hoÃ n tiá»n
    - ÄÆ¡n hÃ ng trÆ°á»c 01/02/2026 â Ã¡p dá»¥ng policy v3 (khÃ´ng cÃ³ trong docs)

    Returns:
        dict with: policy_applies, policy_name, exceptions_found, source, rule, explanation
    """
    task_lower = task.lower()
    context_text = " ".join([c.get("text", "") for c in chunks]).lower()

    # --- Rule-based exception detection ---
    exceptions_found = []

    # Exception 1: Flash Sale
    if "flash sale" in task_lower or "flash sale" in context_text:
        exceptions_found.append({
            "type": "flash_sale_exception",
            "rule": "ÄÆ¡n hÃ ng Flash Sale khÃ´ng ÄÆ°á»£c hoÃ n tiá»n (Äiá»u 3, chÃ­nh sÃ¡ch v4).",
            "source": "policy_refund_v4.txt",
        })

    # Exception 2: Digital product
    if any(kw in task_lower for kw in ["license key", "license", "subscription", "ká»¹ thuáº­t sá»"]):
        exceptions_found.append({
            "type": "digital_product_exception",
            "rule": "Sáº£n pháº©m ká»¹ thuáº­t sá» (license key, subscription) khÃ´ng ÄÆ°á»£c hoÃ n tiá»n (Äiá»u 3).",
            "source": "policy_refund_v4.txt",
        })

    # Exception 3: Activated product
    if any(kw in task_lower for kw in ["ÄÃ£ kÃ­ch hoáº¡t", "ÄÃ£ ÄÄng kÃ½", "ÄÃ£ sá»­ dá»¥ng"]):
        exceptions_found.append({
            "type": "activated_exception",
            "rule": "Sáº£n pháº©m ÄÃ£ kÃ­ch hoáº¡t hoáº·c ÄÄng kÃ½ tÃ i khoáº£n khÃ´ng ÄÆ°á»£c hoÃ n tiá»n (Äiá»u 3).",
            "source": "policy_refund_v4.txt",
        })

    # Determine policy_applies
    policy_applies = len(exceptions_found) == 0

    # Determine which policy version applies (temporal scoping)
    # TODO: Check náº¿u ÄÆ¡n hÃ ng trÆ°á»c 01/02/2026 â v3 applies (khÃ´ng cÃ³ docs, nÃªn flag cho synthesis)
    policy_name = "refund_policy_v4"
    policy_version_note = ""
    if "31/01" in task_lower or "30/01" in task_lower or "trÆ°á»c 01/02" in task_lower:
        policy_version_note = "ÄÆ¡n hÃ ng Äáº·t trÆ°á»c 01/02/2026 Ã¡p dá»¥ng chÃ­nh sÃ¡ch v3 (khÃ´ng cÃ³ trong tÃ i liá»u hiá»n táº¡i)."

    # TODO Sprint 2: Gá»i LLM Äá» phÃ¢n tÃ­ch phá»©c táº¡p hÆ¡n
    # VÃ­ dá»¥:
    # from openai import OpenAI
    # client = OpenAI()
    # response = client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[
    #         {"role": "system", "content": "Báº¡n lÃ  policy analyst. Dá»±a vÃ o context, xÃ¡c Äá»nh policy Ã¡p dá»¥ng vÃ  cÃ¡c exceptions."},
    #         {"role": "user", "content": f"Task: {task}\n\nContext:\n" + "\n".join([c['text'] for c in chunks])}
    #     ]
    # )
    # analysis = response.choices[0].message.content

    sources = list({c.get("source", "unknown") for c in chunks if c})

    return {
        "policy_applies": policy_applies,
        "policy_name": policy_name,
        "exceptions_found": exceptions_found,
        "source": sources,
        "policy_version_note": policy_version_note,
        "explanation": "Analyzed via rule-based policy check. TODO: upgrade to LLM-based analysis.",
    }


# âââââââââââââââââââââââââââââââââââââââââââââ
# Worker Entry Point
# âââââââââââââââââââââââââââââââââââââââââââââ

def run(state: dict) -> dict:
    """
    Worker entry point â gá»i tá»« graph.py.

    Args:
        state: AgentState dict

    Returns:
        Updated AgentState vá»i policy_result vÃ  mcp_tools_used
    """
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    needs_tool = state.get("needs_tool", False)

    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state.setdefault("mcp_tools_used", [])

    state["workers_called"].append(WORKER_NAME)

    worker_io = {
        "worker": WORKER_NAME,
        "input": {
            "task": task,
            "chunks_count": len(chunks),
            "needs_tool": needs_tool,
        },
        "output": None,
        "error": None,
    }

    try:
        # Step 1: Náº¿u chÆ°a cÃ³ chunks, gá»i MCP search_kb
        if not chunks and needs_tool:
            mcp_result = _call_mcp_tool("search_kb", {"query": task, "top_k": 3})
            state["mcp_tools_used"].append(mcp_result)
            state["history"].append(f"[{WORKER_NAME}] called MCP search_kb")

            if mcp_result.get("output") and mcp_result["output"].get("chunks"):
                chunks = mcp_result["output"]["chunks"]
                state["retrieved_chunks"] = chunks

        # Step 2: PhÃ¢n tÃ­ch policy
        policy_result = analyze_policy(task, chunks)
        state["policy_result"] = policy_result

        # Step 3: Náº¿u cáº§n thÃªm info tá»« MCP (e.g., ticket status), gá»i get_ticket_info
        if needs_tool and any(kw in task.lower() for kw in ["ticket", "p1", "jira"]):
            mcp_result = _call_mcp_tool("get_ticket_info", {"ticket_id": "P1-LATEST"})
            state["mcp_tools_used"].append(mcp_result)
            state["history"].append(f"[{WORKER_NAME}] called MCP get_ticket_info")

        worker_io["output"] = {
            "policy_applies": policy_result["policy_applies"],
            "exceptions_count": len(policy_result.get("exceptions_found", [])),
            "mcp_calls": len(state["mcp_tools_used"]),
        }
        state["history"].append(
            f"[{WORKER_NAME}] policy_applies={policy_result['policy_applies']}, "
            f"exceptions={len(policy_result.get('exceptions_found', []))}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "POLICY_CHECK_FAILED", "reason": str(e)}
        state["policy_result"] = {"error": str(e)}
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


# âââââââââââââââââââââââââââââââââââââââââââââ
# Test Äá»c láº­p
# âââââââââââââââââââââââââââââââââââââââââââââ

if __name__ == "__main__":
    print("=" * 50)
    print("Policy Tool Worker â Standalone Test")
    print("=" * 50)

    test_cases = [
        {
            "task": "KhÃ¡ch hÃ ng Flash Sale yÃªu cáº§u hoÃ n tiá»n vÃ¬ sáº£n pháº©m lá»i â ÄÆ°á»£c khÃ´ng?",
            "retrieved_chunks": [
                {"text": "Ngoáº¡i lá»: ÄÆ¡n hÃ ng Flash Sale khÃ´ng ÄÆ°á»£c hoÃ n tiá»n.", "source": "policy_refund_v4.txt", "score": 0.9}
            ],
        },
        {
            "task": "KhÃ¡ch hÃ ng muá»n hoÃ n tiá»n license key ÄÃ£ kÃ­ch hoáº¡t.",
            "retrieved_chunks": [
                {"text": "Sáº£n pháº©m ká»¹ thuáº­t sá» (license key, subscription) khÃ´ng ÄÆ°á»£c hoÃ n tiá»n.", "source": "policy_refund_v4.txt", "score": 0.88}
            ],
        },
        {
            "task": "KhÃ¡ch hÃ ng yÃªu cáº§u hoÃ n tiá»n trong 5 ngÃ y, sáº£n pháº©m lá»i, chÆ°a kÃ­ch hoáº¡t.",
            "retrieved_chunks": [
                {"text": "YÃªu cáº§u trong 7 ngÃ y lÃ m viá»c, sáº£n pháº©m lá»i nhÃ  sáº£n xuáº¥t, chÆ°a dÃ¹ng.", "source": "policy_refund_v4.txt", "score": 0.85}
            ],
        },
    ]

    for tc in test_cases:
        print(f"\nâ¶ Task: {tc['task'][:70]}...")
        result = run(tc.copy())
        pr = result.get("policy_result", {})
        print(f"  policy_applies: {pr.get('policy_applies')}")
        if pr.get("exceptions_found"):
            for ex in pr["exceptions_found"]:
                print(f"  exception: {ex['type']} â {ex['rule'][:60]}...")
        print(f"  MCP calls: {len(result.get('mcp_tools_used', []))}")

    print("\nâ policy_tool_worker test done.")
# Owner: Ðào Quang Th?ng


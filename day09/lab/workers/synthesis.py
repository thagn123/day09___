"""
workers/synthesis.py â Synthesis Worker
Sprint 2: Tá»ng há»£p cÃ¢u tráº£ lá»i tá»« retrieved_chunks vÃ  policy_result.

Input (tá»« AgentState):
    - task: cÃ¢u há»i
    - retrieved_chunks: evidence tá»« retrieval_worker
    - policy_result: káº¿t quáº£ tá»« policy_tool_worker

Output (vÃ o AgentState):
    - final_answer: cÃ¢u tráº£ lá»i cuá»i vá»i citation
    - sources: danh sÃ¡ch nguá»n tÃ i liá»u ÄÆ°á»£c cite
    - confidence: má»©c Äá» tin cáº­y (0.0 - 1.0)

Gá»i Äá»c láº­p Äá» test:
    python workers/synthesis.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

WORKER_NAME = "synthesis_worker"

SYSTEM_PROMPT = """Báº¡n lÃ  trá»£ lÃ½ IT Helpdesk ná»i bá».

Quy táº¯c nghiÃªm ngáº·t:
1. CHá» tráº£ lá»i dá»±a vÃ o context ÄÆ°á»£c cung cáº¥p. KHÃNG dÃ¹ng kiáº¿n thá»©c ngoÃ i.
2. Náº¿u context khÃ´ng Äá»§ Äá» tráº£ lá»i â nÃ³i rÃµ "KhÃ´ng Äá»§ thÃ´ng tin trong tÃ i liá»u ná»i bá»".
3. TrÃ­ch dáº«n nguá»n cuá»i má»i cÃ¢u quan trá»ng: [tÃªn_file].
4. Tráº£ lá»i sÃºc tÃ­ch, cÃ³ cáº¥u trÃºc. KhÃ´ng dÃ i dÃ²ng.
5. Náº¿u cÃ³ exceptions/ngoáº¡i lá» â nÃªu rÃµ rÃ ng trÆ°á»c khi káº¿t luáº­n.
"""


def _call_llm(messages: list) -> str:
    """
    Gá»i LLM Äá» tá»ng há»£p cÃ¢u tráº£ lá»i.
    TODO Sprint 2: Implement vá»i OpenAI hoáº·c Gemini.
    """
    # Option A: OpenAI
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,  # Low temperature Äá» grounded
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception:
        pass

    # Option B: Gemini
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        combined = "\n".join([m["content"] for m in messages])
        response = model.generate_content(combined)
        return response.text
    except Exception:
        pass

    # Fallback: tráº£ vá» message bÃ¡o lá»i (khÃ´ng hallucinate)
    return "[SYNTHESIS ERROR] KhÃ´ng thá» gá»i LLM. Kiá»m tra API key trong .env."


def _build_context(chunks: list, policy_result: dict) -> str:
    """XÃ¢y dá»±ng context string tá»« chunks vÃ  policy result."""
    parts = []

    if chunks:
        parts.append("=== TÃI LIá»U THAM KHáº¢O ===")
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "unknown")
            text = chunk.get("text", "")
            score = chunk.get("score", 0)
            parts.append(f"[{i}] Nguá»n: {source} (relevance: {score:.2f})\n{text}")

    if policy_result and policy_result.get("exceptions_found"):
        parts.append("\n=== POLICY EXCEPTIONS ===")
        for ex in policy_result["exceptions_found"]:
            parts.append(f"- {ex.get('rule', '')}")

    if not parts:
        return "(KhÃ´ng cÃ³ context)"

    return "\n\n".join(parts)


def _estimate_confidence(chunks: list, answer: str, policy_result: dict) -> float:
    """
    Æ¯á»c tÃ­nh confidence dá»±a vÃ o:
    - Sá» lÆ°á»£ng vÃ  quality cá»§a chunks
    - CÃ³ exceptions khÃ´ng
    - Answer cÃ³ abstain khÃ´ng

    TODO Sprint 2: CÃ³ thá» dÃ¹ng LLM-as-Judge Äá» tÃ­nh confidence chÃ­nh xÃ¡c hÆ¡n.
    """
    if not chunks:
        return 0.1  # KhÃ´ng cÃ³ evidence â low confidence

    if "KhÃ´ng Äá»§ thÃ´ng tin" in answer or "khÃ´ng cÃ³ trong tÃ i liá»u" in answer.lower():
        return 0.3  # Abstain â moderate-low

    # Weighted average cá»§a chunk scores
    if chunks:
        avg_score = sum(c.get("score", 0) for c in chunks) / len(chunks)
    else:
        avg_score = 0

    # Penalty náº¿u cÃ³ exceptions (phá»©c táº¡p hÆ¡n)
    exception_penalty = 0.05 * len(policy_result.get("exceptions_found", []))

    confidence = min(0.95, avg_score - exception_penalty)
    return round(max(0.1, confidence), 2)


def synthesize(task: str, chunks: list, policy_result: dict) -> dict:
    """
    Tá»ng há»£p cÃ¢u tráº£ lá»i tá»« chunks vÃ  policy context.

    Returns:
        {"answer": str, "sources": list, "confidence": float}
    """
    context = _build_context(chunks, policy_result)

    # Build messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""CÃ¢u há»i: {task}

{context}

HÃ£y tráº£ lá»i cÃ¢u há»i dá»±a vÃ o tÃ i liá»u trÃªn."""
        }
    ]

    answer = _call_llm(messages)
    sources = list({c.get("source", "unknown") for c in chunks})
    confidence = _estimate_confidence(chunks, answer, policy_result)

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
    }


def run(state: dict) -> dict:
    """
    Worker entry point â gá»i tá»« graph.py.
    """
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    policy_result = state.get("policy_result", {})

    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state["workers_called"].append(WORKER_NAME)

    worker_io = {
        "worker": WORKER_NAME,
        "input": {
            "task": task,
            "chunks_count": len(chunks),
            "has_policy": bool(policy_result),
        },
        "output": None,
        "error": None,
    }

    try:
        result = synthesize(task, chunks, policy_result)
        state["final_answer"] = result["answer"]
        state["sources"] = result["sources"]
        state["confidence"] = result["confidence"]

        worker_io["output"] = {
            "answer_length": len(result["answer"]),
            "sources": result["sources"],
            "confidence": result["confidence"],
        }
        state["history"].append(
            f"[{WORKER_NAME}] answer generated, confidence={result['confidence']}, "
            f"sources={result['sources']}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "SYNTHESIS_FAILED", "reason": str(e)}
        state["final_answer"] = f"SYNTHESIS_ERROR: {e}"
        state["confidence"] = 0.0
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


# âââââââââââââââââââââââââââââââââââââââââââââ
# Test Äá»c láº­p
# âââââââââââââââââââââââââââââââââââââââââââââ

if __name__ == "__main__":
    print("=" * 50)
    print("Synthesis Worker â Standalone Test")
    print("=" * 50)

    test_state = {
        "task": "SLA ticket P1 lÃ  bao lÃ¢u?",
        "retrieved_chunks": [
            {
                "text": "Ticket P1: Pháº£n há»i ban Äáº§u 15 phÃºt ká» tá»« khi ticket ÄÆ°á»£c táº¡o. Xá»­ lÃ½ vÃ  kháº¯c phá»¥c 4 giá». Escalation: tá»± Äá»ng escalate lÃªn Senior Engineer náº¿u khÃ´ng cÃ³ pháº£n há»i trong 10 phÃºt.",
                "source": "sla_p1_2026.txt",
                "score": 0.92,
            }
        ],
        "policy_result": {},
    }

    result = run(test_state.copy())
    print(f"\nAnswer:\n{result['final_answer']}")
    print(f"\nSources: {result['sources']}")
    print(f"Confidence: {result['confidence']}")

    print("\n--- Test 2: Exception case ---")
    test_state2 = {
        "task": "KhÃ¡ch hÃ ng Flash Sale yÃªu cáº§u hoÃ n tiá»n vÃ¬ lá»i nhÃ  sáº£n xuáº¥t.",
        "retrieved_chunks": [
            {
                "text": "Ngoáº¡i lá»: ÄÆ¡n hÃ ng Flash Sale khÃ´ng ÄÆ°á»£c hoÃ n tiá»n theo Äiá»u 3 chÃ­nh sÃ¡ch v4.",
                "source": "policy_refund_v4.txt",
                "score": 0.88,
            }
        ],
        "policy_result": {
            "policy_applies": False,
            "exceptions_found": [{"type": "flash_sale_exception", "rule": "Flash Sale khÃ´ng ÄÆ°á»£c hoÃ n tiá»n."}],
        },
    }
    result2 = run(test_state2.copy())
    print(f"\nAnswer:\n{result2['final_answer']}")
    print(f"Confidence: {result2['confidence']}")

    print("\nâ synthesis_worker test done.")
# Owner: Ðào Quang Th?ng


"""
Agent orchestrator: Gemini + tool calling with streaming + 503 retry.
"""

import sys
import os
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
from typing import AsyncGenerator
from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.agent.prompts import SYSTEM_PROMPT, DISCLAIMER
from app.agent.tools import TOOL_DECLARATIONS, execute_tool, check_interaction

load_dotenv()

GEMINI_MODEL = "gemini-3.1-flash-lite"

_SESSIONS: dict[str, list] = {}


class AgentOrchestrator:
    """Coordinates Gemini, tools, and streaming."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")

        self.client = genai.Client(api_key=api_key)
        self.model = GEMINI_MODEL
        print(f"✅ Agent orchestrator ready (model: {self.model})")

    # --------------------------------------------------------
    # Retry helper
    # --------------------------------------------------------
    def _call_with_retry(self, fn, max_retries=3):
        """Retry on 503/429 with exponential backoff (2s, 4s, 8s)."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return fn()
            except Exception as e:
                last_error = e
                err_str = str(e)
                is_retryable = (
                    "503" in err_str
                    or "UNAVAILABLE" in err_str
                    or "429" in err_str
                    or "RESOURCE_EXHAUSTED" in err_str
                )
                if is_retryable and attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"⏳ Gemini temporary error, retrying in {wait}s "
                          f"(attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait)
                    continue
                raise
        raise last_error

    # --------------------------------------------------------
    # Fallback answer builder (used when Gemini returns empty)
    # --------------------------------------------------------
    def _build_fallback_answer(self, tool_results):
        """Build a human-readable answer from tool results when Gemini fails."""
        if not tool_results:
            return "I couldn't retrieve the information. Please try again."

        # --- Prescription listing ---
        for tr in tool_results:
            if tr["name"] == "list_prescription_drugs":
                result = tr.get("result", {})
                drugs = result.get("drugs", [])
                if not drugs:
                    return (
                        "You haven't uploaded a prescription yet. "
                        "Go to the **Upload** page, upload a prescription image, "
                        "then come back and ask me again."
                    )

                lines = [
                    f"📋 **Your last prescription** (#{result.get('prescription_id')}) "
                    f"had **{len(drugs)} drugs**:\n"
                ]
                for d in drugs:
                    lines.append(f"- **{d}**")

                lines.append("\n**Checking interactions between them...**\n")

                flagged = []
                for i in range(len(drugs)):
                    for j in range(i + 1, len(drugs)):
                        r = check_interaction(drugs[i], drugs[j])
                        if r.get("found"):
                            flagged.append((drugs[i], drugs[j], r))

                if flagged:
                    lines.append("⚠️ **Interactions found:**\n")
                    for a, b, r in flagged:
                        lines.append(
                            f"- **{a}** + **{b}** — {r.get('severity', '').upper()}: "
                            f"{r.get('description', '')[:120]}..."
                        )
                        lines.append(
                            f"  📚 Source: {r.get('source', 'N/A')} | "
                            f"🎯 Confidence: {r.get('confidence_label', 'N/A')}"
                        )
                else:
                    lines.append(
                        "✅ **No known interactions found** between these drugs in our "
                        "clinical database.\n\n*This does not guarantee safety. Always "
                        "consult your doctor.*"
                    )

                return "\n".join(lines)

        # --- Interaction check ---
        for tr in tool_results:
            if tr["name"] == "check_interaction":
                result = tr.get("result", {})
                if result.get("found"):
                    return (
                        f"⚠️ **{result.get('severity', 'caution').upper()}** — "
                        f"Interaction found between **{result.get('drug_a')}** and "
                        f"**{result.get('drug_b')}**\n\n"
                        f"**What happens:** {result.get('description', 'N/A')}\n\n"
                        f"**Why:** {result.get('mechanism', 'N/A')}\n\n"
                        f"**What to do:** {result.get('recommendation', 'N/A')}\n\n"
                        f"📚 **Source:** {result.get('source', 'N/A')}\n"
                        f"🎯 **Confidence:** {result.get('confidence_label', 'N/A')}"
                    )
                return (
                    f"ℹ️ **Not found in our clinical database.**\n\n"
                    f"The pair **{result.get('drug_a', '?')}** + "
                    f"**{result.get('drug_b', '?')}** does not have a documented "
                    f"interaction in our clinical database.\n\n"
                    f"**This does not guarantee safety.** Always consult your "
                    f"pharmacist or doctor before combining medications."
                )

        return "I processed your request but couldn't generate a detailed answer."

    # --------------------------------------------------------
    # Main streaming chat
    # --------------------------------------------------------
    async def chat_stream(
        self,
        session_id: str,
        user_message: str,
    ) -> AsyncGenerator[dict, None]:
        """Process a user message and yield stream events."""
        if session_id not in _SESSIONS:
            _SESSIONS[session_id] = []
        history = _SESSIONS[session_id]

        contents = []
        for h in history[-10:]:
            contents.append(h)
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        tools = [types.Tool(function_declarations=TOOL_DECLARATIONS)]

        try:
            # === FIRST CALL ===
            response = self._call_with_retry(
                lambda: self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        tools=tools,
                        temperature=0.1,
                        max_output_tokens=2048,
                    ),
                )
            )

            tool_calls = []
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        tool_calls.append(part.function_call)

            if tool_calls:
                yield {"type": "text", "content": "🔍 *Checking the clinical database...*\n\n"}

                tool_results = []
                for tc in tool_calls:
                    tool_name = tc.name
                    tool_args = dict(tc.args) if tc.args else {}

                    yield {"type": "tool_call", "name": tool_name, "args": tool_args}
                    result = execute_tool(tool_name, tool_args)

                    if tool_name == "list_prescription_drugs" and not result.get("found"):
                        yield {
                            "type": "text",
                            "content": (
                                "It looks like you haven't uploaded a prescription yet. "
                                "Head to the **Upload** page first. 👨‍⚕️\n\n"
                            ),
                        }

                    tool_results.append({
                        "name": tool_name,
                        "args": tool_args,
                        "result": result,
                    })
                    yield {"type": "tool_result", "name": tool_name, "result": result}

                # Preserve full model turn (thought-signature requirement)
                contents.append(response.candidates[0].content)
                for tr in tool_results:
                    contents.append({
                        "role": "user",
                        "parts": [{
                            "function_response": {
                                "name": tr["name"],
                                "response": tr["result"],
                            }
                        }],
                    })

                # === SECOND CALL: final natural answer ===
                full_text = ""
                try:
                    stream = self._call_with_retry(
                        lambda: self.client.models.generate_content_stream(
                            model=self.model,
                            contents=contents,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_PROMPT,
                                temperature=0.3,
                                max_output_tokens=512,
                            ),
                        )
                    )
                    for chunk in stream:
                        if chunk.text:
                            full_text += chunk.text
                            yield {"type": "text", "content": chunk.text}
                except Exception as e:
                    print(f"⚠️ Second Gemini call failed: {e}")

                # If Gemini returned nothing → fallback
                if not full_text.strip():
                    fallback = self._build_fallback_answer(tool_results)
                    full_text = fallback
                    yield {"type": "text", "content": fallback}

                if "consult your doctor" not in full_text.lower():
                    full_text += DISCLAIMER
                    yield {"type": "text", "content": DISCLAIMER}

                history.append({"role": "user", "parts": [{"text": user_message}]})
                history.append({"role": "model", "parts": [{"text": full_text}]})

            else:
                # No tool call — direct answer
                text = response.text or self._build_fallback_answer([])
                yield {"type": "text", "content": text}

                if "consult your doctor" not in text.lower():
                    yield {"type": "text", "content": DISCLAIMER}

                history.append({"role": "user", "parts": [{"text": user_message}]})
                history.append({"role": "model", "parts": [{"text": text}]})

            yield {"type": "done"}

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield {"type": "error", "message": str(e)}


def clear_session(session_id: str):
    if session_id in _SESSIONS:
        del _SESSIONS[session_id]


def get_session_history(session_id: str) -> list:
    return _SESSIONS.get(session_id, [])


_orchestrator = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
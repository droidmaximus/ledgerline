import json
import logging
import os
import re

from app.config import Settings

logger = logging.getLogger(__name__)


def _strip_markdown_json(text: str) -> str:
    text = text.strip()
    m = re.match(r"(?s)^```(?:json)?\s*(.+?)\s*```$", text)
    if m:
        return m.group(1).strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            inner = parts[1]
            if inner.startswith("json"):
                inner = inner[4:]
            return inner.strip()
    return text


def _normalize_rubric_scores(d: dict) -> dict:
    """LLMs often return total_score that does not match sub-scores; we derive total from the rubric."""

    def clamp_int(v, lo: int, hi: int) -> int:
        try:
            n = int(round(float(v)))
        except (TypeError, ValueError):
            n = 0
        return max(lo, min(hi, n))

    fa = clamp_int(d.get("factual_accuracy"), 0, 3)
    comp = clamp_int(d.get("completeness"), 0, 3)
    cit = clamp_int(d.get("citation_quality"), 0, 2)
    rel = clamp_int(d.get("relevance"), 0, 2)
    out = dict(d)
    out["factual_accuracy"] = fa
    out["completeness"] = comp
    out["citation_quality"] = cit
    out["relevance"] = rel
    out["total_score"] = float(fa + comp + cit + rel)
    return out


class LLMJudge:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _claude_key(self) -> str:
        return (self.settings.claude_api_key or os.getenv("CLAUDE_API_KEY", "")).strip()

    def _openai_key(self) -> str:
        return (self.settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")).strip()

    def _format_tree_path(self, tree_path) -> str:
        if not tree_path:
            return ""
        if isinstance(tree_path, list):
            parts = [str(x) for x in tree_path if x is not None and str(x).strip()]
            if not parts:
                return ""
            return ", ".join(parts)
        return str(tree_path)

    async def judge_answer(self, question: str, answer: str, tree_path=None) -> dict:
        refs = self._format_tree_path(tree_path)
        refs_block = ""
        if refs:
            refs_block = f"""
Structured references (PageIndex node_ids the gateway used for retrieval — not shown to end users as prose, but valid citations for this pipeline):
{refs}

When scoring citation quality, treat these node_ids as supporting references if the answer is consistent with content that would come from those sections. Do not demand page numbers in the answer text if node_ids were supplied here.
"""

        prompt = f"""You are an expert evaluator for financial document QA systems.

Question: {question}
Answer: {answer}
{refs_block}
Important constraints:
- You only see the question and the model's answer. You do NOT see the retrieved document text or context.
- Do NOT assume what the source document contains (e.g. that a 10-K "usually" has revenue). If the answer says the information is not in the provided context, cannot be found in the excerpts, or similar, treat that as a valid, honest response unless the answer contradicts itself.
- When the answer appropriately refuses to invent numbers and clearly ties that to limited/missing context, score factual accuracy highly and set hallucinations_detected to false. Penalize only clear fabrication or internal contradiction.
- For "not in context" answers, citation quality can be full credit if the answer explains that the context did not support a figure (no fake page numbers). Completeness: a concise, correct abstention can still score well if it directly addresses the question without unnecessary padding.
- Relevance: if the question asked for specific facts and the answer explains they are absent from context, that is on-topic.
- If the Answer includes explicit page numbers, section titles, or filing metadata in prose, count that toward citation quality in addition to any structured node_ids above.

Evaluate the answer on these criteria:
1. Factual accuracy (0-3 points)
2. Completeness (0-3 points)
3. Citation quality (0-2 points)
4. Relevance (0-2 points)

Return ONLY a JSON object. total_score MUST equal factual_accuracy + completeness + citation_quality + relevance (maximum 10).
{{
  "total_score": 0-10,
  "factual_accuracy": 0-3,
  "completeness": 0-3,
  "citation_quality": 0-2,
  "relevance": 0-2,
  "reasoning": "Detailed explanation",
  "hallucinations_detected": true/false
}}"""

        if self._claude_key():
            return await self._judge_claude(prompt)
        if self._openai_key():
            return await self._judge_openai(prompt)
        logger.error("No CLAUDE_API_KEY or OPENAI_API_KEY configured for evaluation judge")
        return {
            "total_score": 0,
            "factual_accuracy": 0,
            "completeness": 0,
            "citation_quality": 0,
            "relevance": 0,
            "reasoning": "No LLM API key configured (set CLAUDE_API_KEY or OPENAI_API_KEY)",
            "hallucinations_detected": True,
        }

    async def _judge_claude(self, prompt: str) -> dict:
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=self._claude_key())
            msg = await client.messages.create(
                model=self.settings.claude_model,
                max_tokens=1024,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text
            content = _strip_markdown_json(raw)
            return _normalize_rubric_scores(json.loads(content))
        except Exception as e:
            logger.error(f"Claude evaluation error: {e}")
            return {
                "total_score": 0,
                "factual_accuracy": 0,
                "completeness": 0,
                "citation_quality": 0,
                "relevance": 0,
                "reasoning": f"Evaluation failed: {e!s}",
                "hallucinations_detected": True,
            }

    async def _judge_openai(self, prompt: str) -> dict:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self._openai_key())
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            content = response.choices[0].message.content or ""
            content = _strip_markdown_json(content)
            return _normalize_rubric_scores(json.loads(content))
        except Exception as e:
            logger.error(f"OpenAI evaluation error: {e}")
            return {
                "total_score": 0,
                "factual_accuracy": 0,
                "completeness": 0,
                "citation_quality": 0,
                "relevance": 0,
                "reasoning": f"Evaluation failed: {e!s}",
                "hallucinations_detected": True,
            }

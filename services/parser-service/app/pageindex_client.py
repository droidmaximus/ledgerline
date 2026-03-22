import logging
import asyncio
import os
import json
import re
from typing import Callable, Optional, Dict
import PyPDF2

from app.config import Settings

logger = logging.getLogger(__name__)


def infer_page_count_from_tree(tree: dict) -> int:
    """Max page from tree metadata (page_count or deepest end_index)."""
    if not isinstance(tree, dict):
        return 0
    pc = tree.get("page_count")
    if isinstance(pc, (int, float)) and int(pc) > 0:
        return int(pc)
    best = 0

    def walk(obj: object) -> None:
        nonlocal best
        if isinstance(obj, dict):
            ei = obj.get("end_index")
            if isinstance(ei, (int, float)) and int(ei) > 0:
                best = max(best, int(ei))
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for x in obj:
                walk(x)

    walk(tree)
    return best


def count_pdf_pages(pdf_path: str) -> int:
    """Page count from the PDF reader."""
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return len(reader.pages)
    except Exception as e:
        logger.warning(f"count_pdf_pages failed: {e}")
        return 0


class PageIndexClient:
    def __init__(self, settings: Settings):
        self.settings = settings

        if not os.getenv("CHATGPT_API_KEY"):
            if settings.chatgpt_api_key:
                os.environ["CHATGPT_API_KEY"] = settings.chatgpt_api_key
            elif settings.openai_api_key:
                os.environ["CHATGPT_API_KEY"] = settings.openai_api_key

        self._pdf_to_tree: Optional[Callable[..., object]] = self._resolve_legacy_pdf_to_tree()

    def _resolve_legacy_pdf_to_tree(self) -> Optional[Callable[..., object]]:
        """Load pageindex.pdf_to_tree when the package exposes it."""
        try:
            from pageindex import pdf_to_tree as legacy_pdf_to_tree
            logger.info("Using legacy pageindex.pdf_to_tree API")
            return legacy_pdf_to_tree
        except (ImportError, AttributeError):
            logger.warning("pageindex.pdf_to_tree not available - will use fallback tree generation")
            return None
        except Exception as e:
            logger.warning(f"Could not load pageindex.pdf_to_tree: {e}")
            return None
    
    async def generate_tree(self, pdf_path: str) -> dict:
        try:
            logger.info(f"Generating PageIndex tree for {pdf_path}")
            loop = asyncio.get_event_loop()
            tree = await loop.run_in_executor(
                None,
                self._generate_tree_sync,
                pdf_path
            )
            
            logger.info(f"Tree generated successfully")
            return tree
            
        except Exception as e:
            logger.error(f"Error generating tree: {e}")
            raise

    def _generate_tree_sync(self, pdf_path: str) -> dict:
        """Legacy pdf_to_tree or LLM/mock fallback."""
        if self._pdf_to_tree is not None:
            return self._pdf_to_tree_sync(pdf_path)
        logger.info("Using fallback tree generation")
        tree = self._fallback_tree_sync(pdf_path)
        self._annotate_page_count(tree, pdf_path)
        return tree
    
    def _pdf_to_tree_sync(self, pdf_path: str) -> dict:
        """Sync call into pageindex.pdf_to_tree."""
        try:
            tree = asyncio.run(self._pdf_to_tree(
                pdf_path=pdf_path,
                if_add_node_summary='yes',
                if_add_doc_description='yes',
                if_add_node_id='yes',
                model=self.settings.pageindex_model
            ))
            self._annotate_page_count(tree, pdf_path)
            return tree
        except Exception as e:
            logger.error(f"PageIndex error: {e}")
            raise

    def _annotate_page_count(self, tree: dict, pdf_path: str) -> None:
        """Set tree['page_count'] if missing."""
        if not isinstance(tree, dict):
            return
        pc = infer_page_count_from_tree(tree)
        if pc <= 0:
            pc = count_pdf_pages(pdf_path)
        if pc > 0:
            tree["page_count"] = pc

    def _fallback_tree_sync(self, pdf_path: str) -> dict:
        """Claude, then OpenAI, else mock tree."""
        try:
            pdf_text, page_count = self._extract_pdf_text(pdf_path)
            logger.info(f"Extracted {page_count} pages from PDF")
            claude_key = self.settings.claude_api_key or os.getenv("CLAUDE_API_KEY")
            if claude_key and claude_key != "your-claude-api-key-here":
                logger.info("Using Claude API for tree generation")
                tree = self._claude_tree_generation(pdf_path, page_count, pdf_text, claude_key)
                return self._ensure_context_rich_tree(tree, pdf_text, page_count)
            import openai
            api_key = self.settings.openai_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("No API key found - using mock tree generation for demo")
                tree = self._mock_tree_structure(pdf_path, page_count, pdf_text)
                return self._ensure_context_rich_tree(tree, pdf_text, page_count)
            client = openai.OpenAI(api_key=api_key)
            prompt = f"""Analyze this document and create a hierarchical tree structure.

Document Preview (first 2000 chars):
{pdf_text[:2000]}

Total pages: {page_count}

Return ONLY this exact JSON (no markdown, no extra text):
{{
  "title": "Document Title",
  "node_id": "0001",
  "start_index": 1,
  "end_index": {page_count},
  "summary": "Brief summary",
  "nodes": [
    {{
      "node_id": "0002",
      "title": "Section 1",
      "start_index": 1,
      "end_index": {max(1, page_count // 2)},
      "summary": "First section summary",
      "nodes": []
    }},
    {{
      "node_id": "0003",
      "title": "Section 2",
      "start_index": {max(1, page_count // 2) + 1},
      "end_index": {page_count},
      "summary": "Second section summary",
      "nodes": []
    }}
  ]
}}
"""
            
            logger.info("Sending request to OpenAI API...")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            logger.info("Parsing response as JSON...")
            tree = json.loads(response_text)
            logger.info(f"Generated tree with {len(tree.get('nodes', []))} top-level nodes")
            return self._ensure_context_rich_tree(tree, pdf_text, page_count)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tree response as JSON: {e}")
            if "api_key" in locals():
                raise
            else:
                logger.warning("Falling back to mock tree generation")
                tree = self._mock_tree_structure(pdf_path, page_count, pdf_text)
                return self._ensure_context_rich_tree(tree, pdf_text, page_count)
                
        except Exception as e:
            logger.warning(f"Tree generation failed ({type(e).__name__}: {str(e)[:100]})")
            if "429" in str(e) or "quota" in str(e).lower():
                logger.warning("API quota exceeded - using mock tree for demo")
                tree = self._mock_tree_structure(pdf_path, page_count, pdf_text)
                return self._ensure_context_rich_tree(tree, pdf_text, page_count)
            raise

    def _split_pdf_text_chunks(self, pdf_text: str, max_total_chars: int = 280_000, chunk_size: int = 4500) -> list:
        """Chunk full text for leaf fallback when page map is thin."""
        text = pdf_text[:max_total_chars] if pdf_text else ""
        if not text.strip():
            return [""]
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
        return chunks if chunks else [text]

    def _parse_page_texts(self, pdf_text: str) -> Dict[int, str]:
        """Map page number -> body from `[PAGE N]` segments."""
        if not pdf_text:
            return {}

        page_map: Dict[int, str] = {}
        matches = list(re.finditer(r"\[PAGE\s+(\d+)\]", pdf_text))
        for i, m in enumerate(matches):
            try:
                page_num = int(m.group(1))
            except Exception:
                continue
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(pdf_text)
            segment = pdf_text[start:end].strip()
            page_map[page_num] = segment
        return page_map

    def _enrich_leaf_nodes_text(self, tree: dict, chunks: list, page_texts: Dict[int, str]) -> None:
        """Fill leaf `text` from page ranges or chunk rotation."""
        idx = [0]
        leaf_text_max_chars = int(os.getenv("PARSER_LEAF_TEXT_MAX_CHARS", "9000"))

        def walk(node: dict) -> None:
            if not isinstance(node, dict):
                return
            kids = node.get("nodes")
            if isinstance(kids, list) and len(kids) > 0:
                for ch in kids:
                    if isinstance(ch, dict):
                        walk(ch)
                return
            existing = (node.get("text") or "").strip()
            if not existing:
                start_idx = node.get("start_index", 1)
                end_idx = node.get("end_index", start_idx)
                try:
                    start_page = int(start_idx)
                    end_page = int(end_idx)
                except Exception:
                    start_page = 1
                    end_page = 1

                if start_page < 1:
                    start_page = 1
                if end_page < start_page:
                    end_page = start_page

                parts = []
                total = 0
                for p in range(start_page, end_page + 1):
                    part = page_texts.get(p, "")
                    if not part:
                        continue
                    if part:
                        parts.append(part)
                        total += len(part)
                    if total >= leaf_text_max_chars:
                        break

                if parts:
                    c = "\n".join(parts)
                    node["text"] = c[:leaf_text_max_chars]
                else:
                    c = chunks[idx[0] % len(chunks)]
                    idx[0] += 1
                    node["text"] = c

                summ = (node.get("summary") or "").strip()
                if not summ and c:
                    node["summary"] = c[:500] + ("…" if len(c) > 500 else "")

        walk(tree)

    def _ensure_context_rich_tree(self, tree: dict, pdf_text: str, page_count: int) -> dict:
        """Add root text, leaf bodies, and synthetic nodes if the model returned none."""
        try:
            if not isinstance(tree, dict):
                tree = {}

            nodes = tree.get("nodes", [])
            if not isinstance(nodes, list):
                nodes = []

            # Root text fallback (used by downstream retrieval if node summaries are sparse)
            if not tree.get("text"):
                tree["text"] = pdf_text[:24000]

            chunks = self._split_pdf_text_chunks(pdf_text)
            page_texts = self._parse_page_texts(pdf_text)

            if len(nodes) == 0:
                chunk_size = 4000
                cap = min(len(pdf_text), int(os.getenv("PARSER_DETERMINISTIC_TREE_TEXT_CAP_CHARS", "240000")))
                raw_chunks = [pdf_text[i : i + chunk_size] for i in range(0, cap, chunk_size)]
                built_nodes = []
                for j, chunk in enumerate(raw_chunks[: min(24, len(raw_chunks) or 1)], start=2):
                    built_nodes.append({
                        "node_id": f"{j:04d}",
                        "title": f"Extracted Section {j - 1}",
                        "start_index": 1,
                        "end_index": page_count,
                        "summary": chunk[:400] + ("…" if len(chunk) > 400 else ""),
                        "text": chunk,
                        "nodes": []
                    })
                tree["nodes"] = built_nodes
                # #region agent log
                _dbg("H6", "services/parser-service/app/pageindex_client.py:_ensure_context_rich_tree", "Built deterministic fallback nodes", {"fallback_nodes": len(built_nodes), "page_count": page_count})
                # #endregion
            else:
                self._enrich_leaf_nodes_text(tree, chunks, page_texts)

            # #region agent log
            _dbg("H6", "services/parser-service/app/pageindex_client.py:_ensure_context_rich_tree", "Final tree context stats", {"root_text_len": len(tree.get('text', '')), "nodes_count": len(tree.get('nodes', []))})
            # #endregion
            tree["page_count"] = page_count
            return tree
        except Exception:
            return tree

    def _claude_tree_generation(self, pdf_path: str, page_count: int, pdf_text: str, api_key: str) -> dict:
        """Ask Claude for a JSON tree (Messages API)."""
        try:
            from anthropic import Anthropic
            
            client = Anthropic(api_key=api_key)
            
            prompt = f"""Analyze this document and create a hierarchical tree structure.

Document Preview (first 2000 chars):
{pdf_text[:2000]}

Total pages: {page_count}

Return ONLY this exact JSON (no markdown, no extra text):
{{
  "title": "Document Title",
  "node_id": "0001",
  "start_index": 1,
  "end_index": {page_count},
  "summary": "Brief summary",
  "nodes": [
    {{
      "node_id": "0002",
      "title": "Section 1",
      "start_index": 1,
      "end_index": {max(1, page_count // 2)},
      "summary": "First section summary",
      "nodes": []
    }},
    {{
      "node_id": "0003",
      "title": "Section 2",
      "start_index": {max(1, page_count // 2) + 1},
      "end_index": {page_count},
      "summary": "Second section summary",
      "nodes": []
    }}
  ]
}}
"""
            
            logger.info("Sending request to Claude API...")
            logger.info(f"Using model: {self.settings.claude_model}")
            logger.info(f"API key present: {bool(api_key and len(api_key) > 10)}")
            
            message = client.messages.create(
                model=self.settings.claude_model,
                max_tokens=2000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            response_text = message.content[0].text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            logger.info("Parsing Claude response as JSON...")
            tree = json.loads(response_text)
            logger.info(f"Generated tree with {len(tree.get('nodes', []))} top-level nodes")
            return tree
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude tree response as JSON: {e}")
            logger.warning("Falling back to mock tree generation")
            return self._mock_tree_structure(pdf_path, page_count, pdf_text)
        except Exception as e:
            logger.warning("Claude tree generation failed: %s: %s", type(e).__name__, e)
            if "429" in str(e) or "quota" in str(e).lower():
                logger.warning("quota exceeded — using mock tree")
            return self._mock_tree_structure(pdf_path, page_count, pdf_text)

    def _mock_tree_structure(self, pdf_path: str, page_count: int, pdf_text: str) -> dict:
        """Heuristic tree when no LLM or quota hit."""
        try:
            import os as os_module
            filename = os_module.path.basename(pdf_path)
            title = filename.replace(".pdf", "").replace("-", " ").title()
            
            nodes_count = max(3, min(page_count // 4, 16))
            nodes = []
            chunk_size = max(3000, len(pdf_text) // max(nodes_count, 1)) if pdf_text else 3000
            
            for i in range(nodes_count):
                start_page = (i * page_count // nodes_count) + 1
                end_page = ((i + 1) * page_count // nodes_count)
                start_c = i * chunk_size
                chunk = pdf_text[start_c : start_c + chunk_size] if pdf_text else ""
                summ = (chunk[:450] + "…") if len(chunk) > 450 else (chunk or f"Content from pages {start_page}-{end_page}")
                
                nodes.append({
                    "node_id": f"{(i + 2):04d}",
                    "title": f"Section {i + 1}",
                    "start_index": start_page,
                    "end_index": end_page,
                    "summary": summ,
                    "text": chunk,
                    "nodes": []
                })
            
            tree = {
                "title": title,
                "node_id": "0001",
                "start_index": 1,
                "end_index": page_count,
                "page_count": page_count,
                "summary": f"Document with {page_count} pages. (Demo tree - LLM unavailable)",
                "nodes": nodes
            }
            
            logger.info(f"Generated mock tree with {len(nodes)} nodes")
            return tree
            
        except Exception as e:
            logger.error(f"Mock tree generation failed: {e}")
            return {
                "title": "Document",
                "node_id": "0001",
                "start_index": 1,
                "end_index": max(1, page_count),
                "page_count": max(1, page_count),
                "summary": "Fallback tree structure",
                "nodes": [{
                    "node_id": "0002",
                    "title": "Content",
                    "start_index": 1,
                    "end_index": max(1, page_count),
                    "summary": "Full document content",
                    "nodes": []
                }]
            }

    def _extract_pdf_text(self, pdf_path: str) -> tuple:
        """Extract text and page count from PDF."""
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                page_count = len(reader.pages)
                
                text = ""
                max_pages = min(page_count, int(os.getenv("PARSER_TEXT_MAX_PAGES", "120")))
                for i, page in enumerate(reader.pages[:max_pages]):
                    try:
                        extracted = page.extract_text()
                        if extracted:
                            text += f"\n[PAGE {i+1}]\n" + extracted + "\n"
                    except Exception:
                        continue
                
                logger.info(
                    "PDF text extraction: scanned %s of %s pages, %s characters",
                    max_pages,
                    page_count,
                    len(text),
                )
                return text or "[Unable to extract text]", page_count
        except Exception as e:
            logger.warning(f"Failed to extract PDF text: {e}")
            return "[Document content unavailable]", 1


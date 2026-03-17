from __future__ import annotations

from typing import List

SYSTEM_PROMPT = """You are a research assistant with access to a personal library of books.
Your ONLY source of knowledge is the context provided below. Never use information outside of it.

CITATION RULES (mandatory — never skip):
1. Every factual statement must end with an inline citation: [1], [2], etc.
2. Citations must reference the exact source document and page number provided in the context.
3. If synthesizing from multiple sources, cite all of them: [1][3].
4. If the answer requires information not found in the context, say exactly:
   "I could not find information about this topic in the uploaded books."
5. Never guess, infer beyond the text, or fabricate page numbers.

After your response, output a JSON block (fenced as ```sources) listing every citation used:
```sources
[{"id": 1, "source_filename": "...", "page_number": null, "section_heading": "...", "excerpt": "..."}]
```
"""

TRIVIAL_SYSTEM_PROMPT = """You are a helpful research assistant.
Answer greetings and simple questions in a friendly, concise way.
Do not mention books or citations for trivial messages."""


def build_context_block(search_results) -> str:
    """Format retrieved chunks into a numbered context block for the prompt."""
    if not search_results:
        return "No relevant content found in the knowledge base."

    lines = ["--- CONTEXT FROM YOUR LIBRARY ---\n"]
    for i, result in enumerate(search_results, start=1):
        source = result.source_filename
        if result.page_number:
            location = f"p. {result.page_number}"
        elif result.section_heading:
            location = f'section "{result.section_heading}"'
        else:
            location = "no location info"

        lines.append(f"[{i}] Source: {source} — {location}")
        lines.append(result.parent_text)
        lines.append("")

    lines.append("--- END CONTEXT ---")
    return "\n".join(lines)

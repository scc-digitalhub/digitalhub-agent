from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple
import yaml
from langchain_core.tools import tool

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge"
_CATALOG_CACHE: Optional[Dict[str, Path]] = None


def _get_catalog() -> Dict[str, Path]:
    """
    Parse knowledge/index.md once to extract the authoritative OKF topic mapping.
    """
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None:
        return _CATALOG_CACHE
    catalog = {}
    content = (KNOWLEDGE_DIR / "index.md").read_text(encoding="utf-8")
    fm = yaml.safe_load(content.split("---")[1])
    for item in fm.get("topics", []):
        catalog[item["id"]] = KNOWLEDGE_DIR / item["path"]
    _CATALOG_CACHE = catalog
    return _CATALOG_CACHE

@tool
def list_knowledge_topics() -> str:
    """
    List all available Open Knowledge Format (OKF) documentation topics, entities, and summaries.
    Call this first to discover what technical guides are available.
    """
    index_file = KNOWLEDGE_DIR / "index.md"
    if not index_file.exists():
        return "Documentation catalog (index.md) not found."
    return index_file.read_text(encoding="utf-8")


@tool
def get_knowledge_doc(topic: str, section: Optional[str] = None) -> str:
    """
    Retrieve Open Knowledge Format (OKF) documentation for a given topic or entity.

    Parameters:
    - topic: Topic ID or entity name (e.g., 'project', 'dataitem', 'function', 'run',
             'python', 'workflow', 'trigger', 'artifact', 'model', 'secret', 'troubleshooting', 'governance').
    - section: (Optional) Specific section heading to retrieve (e.g. 'spec', 'methods', 'recipes', 'handler').
               If omitted, returns the complete guide.
    """
    target_file = _get_catalog().get(topic.lower())

    if not target_file or not target_file.exists():
        catalog = _get_catalog()
        valid_topics = sorted(
            k for k in catalog.keys()
            if not k.endswith(".md") and not k.endswith("s")
        )
        return (
            f"Topic '{topic}' not found in knowledge catalog.\n\n"
            f"Available topics: {', '.join(valid_topics)}.\n"
            "Use list_knowledge_topics() to view the full catalog."
        )

    try:
        content = target_file.read_text(encoding="utf-8")
        if section:
            sec_lower = section.strip().lower()
            chunks = re.split(r"(?m)(?=^#{1,3}\s+)", content)
            matched_chunks = [c for c in chunks if sec_lower in c.split("\n", 1)[0].lower()]
            if matched_chunks:
                return f"# {target_file.stem.upper()} -> Section: '{section}'\n\n" + "\n\n---\n\n".join(matched_chunks)

        return content
    except Exception as e:
        return f"Error reading documentation for topic '{topic}': {e}"


@tool
def search_knowledge(query: str) -> str:
    """
    Search across all Open Knowledge Format (OKF) documentation files for SDK methods,
    parameters, errors, or concepts. Returns the most relevant ranked sections.
    """
    query_str = query.strip()
    if not query_str:
        return "Please provide a non-empty search query."

    tokens = [t.lower() for t in re.findall(r"\w+", query_str) if len(t) > 2]
    phrase = query_str.lower()
    scored_matches: List[Tuple[float, str, str]] = []

    for md_file in KNOWLEDGE_DIR.glob("**/*.md"):
        if md_file.name == "index.md":
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
            rel_path = md_file.relative_to(KNOWLEDGE_DIR)
            sections = re.split(r"(?m)(?=^#{2,3}\s+)", content)

            for sec in sections:
                sec_lower = sec.lower()
                score = 0.0
                if phrase in sec_lower:
                    score += 10.0 

                matched_tokens = sum(1 for tok in tokens if tok in sec_lower)
                if matched_tokens > 0:
                    score += (matched_tokens / max(len(tokens), 1)) * 5.0

                if score > 0:
                    clean_sec = sec.strip()
                    if len(clean_sec) > 900:
                        clean_sec = clean_sec[:900].rsplit("\n", 1)[0] + "\n\n... [truncated, use get_knowledge_doc for full guide]"
                    scored_matches.append((score, str(rel_path), clean_sec))
        except Exception:
            continue

    if not scored_matches:
        return f"No documentation matches found for query: '{query}'."

    scored_matches.sort(key=lambda x: x[0], reverse=True)
    top_matches = scored_matches[:4]

    output_blocks = [f"### File: `{path}`\n{text}" for _, path, text in top_matches]
    return f"Search Results for '{query}':\n\n" + "\n\n---\n\n".join(output_blocks)


KNOWLEDGE_TOOLS = [
    list_knowledge_topics,
    get_knowledge_doc,
    search_knowledge,
]
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from langchain_core.tools import tool

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def _parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter and return (metadata_dict, body_text)."""
    metadata = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            for line in fm_text.strip().splitlines():
                if ":" in line and not line.strip().startswith("-"):
                    key, val = line.split(":", 1)
                    key = key.strip().lower()
                    val = val.strip().strip('"').strip("'")
                    metadata[key] = val
    return metadata, body


def _build_dynamic_index() -> Dict[str, Path]:
    """
    Dynamically scan KNOWLEDGE_DIR and index documents by:
    - filename stem (e.g. 'project', 'dataitem', 'python_function', 'sdk_errors')
    - frontmatter entity (e.g. 'project', 'dataitem', 'function')
    - frontmatter runtime (e.g. 'python')
    - frontmatter type (e.g. 'troubleshooting_guide', 'governance_standard')
    - common plural/singular aliases
    """
    index: Dict[str, Path] = {}
    if not KNOWLEDGE_DIR.exists():
        return index

    for md_file in KNOWLEDGE_DIR.glob("**/*.md"):
        if not md_file.is_file():
            continue
        
        stem = md_file.stem.lower()
        index[stem] = md_file
        
        # Plural/singular stems
        if stem.endswith("s"):
            index[stem[:-1]] = md_file
        else:
            index[f"{stem}s"] = md_file

        # Index parent directory name (e.g. 'troubleshooting', 'governance', 'workflows')
        parent_name = md_file.parent.name.lower()
        if parent_name and parent_name != "knowledge":
            index[parent_name] = md_file
            if parent_name.endswith("s"):
                index[parent_name[:-1]] = md_file

        try:
            content = md_file.read_text(encoding="utf-8")
            fm, _ = _parse_frontmatter(content)

            if "type" in fm:
                doc_type = fm["type"].lower()
                index[doc_type] = md_file
                # Strip suffixes like _guide, _standard, _specification, _recipes
                for suffix in ["_guide", "_standard", "_specification", "_recipes", "_catalog"]:
                    if doc_type.endswith(suffix):
                        clean_type = doc_type[:-len(suffix)]
                        index[clean_type] = md_file

            if "entity" in fm:
                ent = fm["entity"].lower()
                index[ent] = md_file
                index[f"{ent}s"] = md_file

            if "runtime" in fm:
                rt = fm["runtime"].lower()
                index[rt] = md_file
                index[f"{rt}_function"] = md_file
                index[f"{rt}_runtime"] = md_file

            if "domain" in fm:
                dom = fm["domain"].lower()
                index[dom] = md_file
                for part in dom.split("_"):
                    if len(part) > 3:
                        index[part] = md_file

            # Handle index / catalog
            if stem == "index":
                index["catalog"] = md_file
                index["overview"] = md_file
                index["all"] = md_file
        except Exception:
            continue

    return index


def _extract_section(content: str, target_section: str) -> Optional[str]:
    """Extract a specific markdown heading block by title or partial match."""
    lines = content.splitlines()
    target_lower = target_section.lower().strip()
    
    start_idx = None
    start_level = 0

    for i, line in enumerate(lines):
        if line.startswith("#"):
            header_text = line.lstrip("#").strip().lower()
            if target_lower in header_text:
                start_idx = i
                start_level = len(line) - len(line.lstrip("#"))
                break

    if start_idx is None:
        return None

    section_lines = [lines[start_idx]]
    for line in lines[start_idx + 1:]:
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level <= start_level:
                break
        section_lines.append(line)

    return "\n".join(section_lines).strip()


@tool
def list_knowledge_topics() -> str:
    """
    List all available Open Knowledge Format (OKF) documentation topics, summaries, and tags.
    Use this to discover which documentation guides are available in the platform knowledge base.
    """
    index_file = KNOWLEDGE_DIR / "index.md"
    if index_file.exists():
        return index_file.read_text(encoding="utf-8")

    index = _build_dynamic_index()
    return "Available OKF Topics:\n" + "\n".join(f"- {topic} -> {path.name}" for topic, path in sorted(index.items()))


@tool
def get_knowledge_doc(topic: str, section: Optional[str] = None) -> str:
    """
    Retrieve Open Knowledge Format (OKF) documentation for a given topic or entity.
    
    Parameters:
    - topic: The entity, runtime, or guide topic (e.g. 'project', 'dataitem', 'python_function', 'recipes', 'troubleshooting', 'governance', 'index').
    - section: (Optional) A specific heading or subsection title (e.g. 'Writing Python Handlers', 'Build', 'Register vs Log', 'Errors').
      Specifying a section retrieves only that section, reducing token usage.
    """
    normalized_topic = topic.strip().lower()
    dynamic_index = _build_dynamic_index()
    
    target_file = dynamic_index.get(normalized_topic)
    
    # Fallback to direct path resolution if not in index
    if not target_file:
        candidate = KNOWLEDGE_DIR / normalized_topic
        if candidate.exists() and candidate.is_file():
            target_file = candidate
        elif (KNOWLEDGE_DIR / f"{normalized_topic}.md").exists():
            target_file = KNOWLEDGE_DIR / f"{normalized_topic}.md"

    if not target_file or not target_file.exists():
        available = sorted(set(dynamic_index.keys()))
        return (
            f"Topic '{topic}' not found in knowledge base. "
            f"Available topics: {', '.join(available[:12])}... "
            f"Call list_knowledge_topics() to view all guides."
        )

    try:
        full_content = target_file.read_text(encoding="utf-8")
        
        if section:
            extracted = _extract_section(full_content, section)
            if extracted:
                return (
                    f"## Section '{section}' from `{target_file.relative_to(KNOWLEDGE_DIR)}`:\n\n"
                    f"{extracted}"
                )
            return (
                f"Section matching '{section}' not found in `{target_file.name}`. "
                f"Returning full document:\n\n{full_content}"
            )

        return full_content
    except Exception as e:
        return f"Error reading documentation for topic '{topic}': {e}"


@tool
def search_knowledge(query: str) -> str:
    """
    Search across all Open Knowledge Format (OKF) documentation files for a keyword, parameter name, exception, or concept.
    Returns matched markdown section blocks and file references.
    """
    query_lower = query.lower().strip()
    matches = []

    if not KNOWLEDGE_DIR.exists():
        return "Knowledge base directory not found."

    for md_file in KNOWLEDGE_DIR.glob("**/*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if query_lower in content.lower():
                rel_path = md_file.relative_to(KNOWLEDGE_DIR)
                
                # Extract matching sections
                sections = re.split(r"(?m)(?=^##\s+)", content)
                for sec in sections:
                    if query_lower in sec.lower():
                        clean_sec = sec.strip()
                        if len(clean_sec) > 800:
                            clean_sec = clean_sec[:800] + "... [truncated, use get_knowledge_doc to view full section]"
                        matches.append(f"### File: `{rel_path}`\n{clean_sec}")
                        if len(matches) >= 4:
                            break
        except Exception:
            continue

    if not matches:
        return f"No documentation matches found for query: '{query}'."

    return f"Search Results for '{query}':\n\n" + "\n\n---\n\n".join(matches)


KNOWLEDGE_TOOLS = [
    list_knowledge_topics,
    get_knowledge_doc,
    search_knowledge,
]

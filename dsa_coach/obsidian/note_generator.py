"""Generate atomic notes with proper structure for Obsidian.

Creates interview-focused notes (150-300 lines) with:
- Frontmatter (tags, dates, links)
- Core concept explanation (WHY it matters)
- Visual models (mermaid diagrams)
- Key trade-offs
- Implementation approach (15-30 lines of interesting code)
- Interview articulation guide
- Cross-links
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _sanitize_filename(name: str) -> str:
    """Convert pattern/problem name to safe filename."""
    return name.lower().replace("_", "-").replace(" ", "-")


def _generate_frontmatter(
    title: str, tags: list[str], related: list[str] | None = None
) -> str:
    """Generate YAML frontmatter for Obsidian note."""
    frontmatter = [
        "---",
        f"title: {title}",
        f"created: {datetime.now().strftime('%Y-%m-%d')}",
        f"tags: {', '.join(tags)}",
    ]
    
    if related:
        frontmatter.append(f"related: {', '.join(related)}")
    
    frontmatter.append("---\n")
    return "\n".join(frontmatter)


def _generate_core_concept_section(pattern: str, description: str, why_matters: str) -> str:
    """Generate Core Concept section (3-5 paragraphs)."""
    return f"""## Core Concept

{description}

### Why This Matters for Interviews

{why_matters}
"""


def _generate_visual_model_section(pattern: str, has_diagram: bool = False) -> str:
    """Generate Architecture/Visual Model section."""
    if not has_diagram:
        return ""
    
    # Placeholder - actual implementation will generate pattern-specific diagrams
    return f"""## Visual Model

```mermaid
graph LR
    A[Start] --> B[Process]
    B --> C[End]
```

*Diagram showing the {pattern.replace('-', ' ')} approach.*
"""


def _generate_trade_offs_section(trade_offs: list[dict[str, str]]) -> str:
    """Generate Key Trade-offs section."""
    if not trade_offs:
        return ""
    
    lines = ["## Key Trade-offs\n"]
    for trade_off in trade_offs:
        lines.append(f"### {trade_off.get('aspect', 'Consideration')}")
        lines.append(f"\n{trade_off.get('description', '')}\n")
        lines.append(f"**When to use**: {trade_off.get('when_to_use', 'TBD')}\n")
    
    return "\n".join(lines)


def _generate_implementation_section(
    code_example: str, explanation: str
) -> str:
    """Generate Implementation Approach section (15-30 lines of code)."""
    return f"""## Implementation Approach

{explanation}

```python
{code_example}
```
"""


def _generate_interview_guide_section(
    sixty_second_pitch: str,
    key_terminology: list[str],
    follow_up_questions: list[str],
    common_pitfalls: list[str],
) -> str:
    """Generate Interview Articulation Guide."""
    return f"""## Interview Articulation Guide

### 60-Second Explanation

{sixty_second_pitch}

### Key Terminology

{chr(10).join(f"- **{term}**" for term in key_terminology)}

### Expected Follow-up Questions

{chr(10).join(f"- {q}" for q in follow_up_questions)}

### Common Pitfalls

{chr(10).join(f"- ❌ {pitfall}" for pitfall in common_pitfalls)}
"""


def _generate_real_world_section(companies: list[str], use_cases: list[str]) -> str:
    """Generate Real-World Usage section."""
    if not companies and not use_cases:
        return ""
    
    lines = ["## Real-World Usage\n"]
    
    if companies:
        lines.append(f"**Companies**: {', '.join(companies)}\n")
    
    if use_cases:
        lines.append("**Use Cases**:")
        lines.extend(f"- {uc}" for uc in use_cases)
        lines.append("")
    
    return "\n".join(lines)


def _generate_related_concepts_section(related: list[dict[str, str]]) -> str:
    """Generate Related Concepts section with cross-links."""
    if not related:
        return ""
    
    lines = ["## Related Concepts\n"]
    for rel in related:
        name = rel.get("name", "")
        context = rel.get("context", "")
        filename = _sanitize_filename(name)
        lines.append(f"- [[{filename}|{name}]]: {context}")
    
    return "\n".join(lines)


def generate_pattern_note(
    pattern: str,
    title: str,
    description: str,
    why_matters: str,
    trade_offs: list[dict[str, str]],
    code_example: str,
    code_explanation: str,
    sixty_second_pitch: str,
    key_terminology: list[str],
    follow_up_questions: list[str],
    common_pitfalls: list[str],
    companies: list[str] | None = None,
    use_cases: list[str] | None = None,
    related_patterns: list[dict[str, str]] | None = None,
    has_diagram: bool = False,
) -> str:
    """Generate a complete pattern note.
    
    Args:
        pattern: Pattern ID (e.g., "sliding_window")
        title: Human-readable title
        description: Core concept explanation (2-3 paragraphs)
        why_matters: Why this matters for interviews
        trade_offs: List of trade-off dicts with aspect, description, when_to_use
        code_example: 15-30 lines of interesting code
        code_explanation: Explanation of the code approach
        sixty_second_pitch: Elevator pitch explanation
        key_terminology: List of precise terms to use
        follow_up_questions: Expected interviewer questions
        common_pitfalls: Common mistakes to avoid
        companies: Companies using this pattern (optional)
        use_cases: Real-world use cases (optional)
        related_patterns: List of related pattern dicts with name, context
        has_diagram: Whether to include mermaid diagram
        
    Returns:
        Complete markdown note content
    """
    tags = ["dsa/patterns", "interview/algorithms"]
    related_links = [_sanitize_filename(r["name"]) for r in (related_patterns or [])]
    
    sections = [
        _generate_frontmatter(title, tags, related_links),
        f"# {title}\n",
        _generate_core_concept_section(pattern, description, why_matters),
        _generate_visual_model_section(pattern, has_diagram),
        _generate_trade_offs_section(trade_offs),
        _generate_implementation_section(code_example, code_explanation),
        _generate_interview_guide_section(
            sixty_second_pitch,
            key_terminology,
            follow_up_questions,
            common_pitfalls,
        ),
        _generate_real_world_section(companies or [], use_cases or []),
        _generate_related_concepts_section(related_patterns or []),
    ]
    
    content = "\n\n".join(s for s in sections if s)
    
    # Enforce line count (150-300 lines ideal)
    line_count = len(content.split("\n"))
    if line_count < 100:
        content += "\n\n<!-- Note: Consider expanding this note to 150-300 lines for completeness -->"
    elif line_count > 400:
        content += "\n\n<!-- Warning: Note exceeds 400 lines. Consider splitting into atomic concepts -->"
    
    return content


def generate_problem_note(
    problem_id: str,
    title: str,
    pattern: str,
    difficulty: str,
    key_insight: str,
    trade_offs: list[str],
    edge_cases: list[str],
    articulation_improvements: list[dict[str, str]] | None = None,
    solution_approach: str = "",
    time_complexity: str = "",
    space_complexity: str = "",
) -> str:
    """Generate a problem-specific note (only if interview-worthy insights).
    
    Args:
        problem_id: Problem identifier
        title: Problem title
        pattern: Associated pattern
        difficulty: Problem difficulty
        key_insight: Main learning from this problem
        trade_offs: Key trade-offs encountered
        edge_cases: Important edge cases
        articulation_improvements: List of phrasing improvements (before/after)
        solution_approach: Brief solution explanation
        time_complexity: Time complexity
        space_complexity: Space complexity
        
    Returns:
        Complete markdown note content
    """
    tags = ["dsa/problems", f"difficulty/{difficulty.lower()}"]
    pattern_filename = _sanitize_filename(pattern)
    
    frontmatter = _generate_frontmatter(title, tags, [pattern_filename])
    
    sections = [
        frontmatter,
        f"# {title}\n",
        f"**Pattern**: [[{pattern_filename}|{pattern}]]  ",
        f"**Difficulty**: {difficulty}\n",
        f"## Key Insight\n\n{key_insight}\n",
    ]
    
    if solution_approach:
        sections.append(f"## Solution Approach\n\n{solution_approach}\n")
        if time_complexity or space_complexity:
            sections.append("### Complexity")
            if time_complexity:
                sections.append(f"- **Time**: {time_complexity}")
            if space_complexity:
                sections.append(f"- **Space**: {space_complexity}")
            sections.append("")
    
    if trade_offs:
        sections.append("## Trade-offs\n")
        sections.extend(f"- {to}" for to in trade_offs)
        sections.append("")
    
    if edge_cases:
        sections.append("## Edge Cases to Remember\n")
        sections.extend(f"- {ec}" for ec in edge_cases)
        sections.append("")
    
    if articulation_improvements:
        sections.append("## Articulation Improvements\n")
        for improvement in articulation_improvements:
            before = improvement.get("before", "")
            after = improvement.get("after", "")
            sections.append(f"❌ **Before**: {before}")
            sections.append(f"✅ **Better**: {after}\n")
    
    return "\n".join(sections)


def get_filename_for_pattern(pattern: str) -> str:
    """Get the filename for a pattern note."""
    return f"{_sanitize_filename(pattern)}.md"


def get_filename_for_problem(problem_id: str) -> str:
    """Get the filename for a problem note."""
    return f"{_sanitize_filename(problem_id)}.md"



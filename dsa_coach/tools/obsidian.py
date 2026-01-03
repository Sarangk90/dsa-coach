"""Obsidian tools for the DSA Coach agent.

Provides tools for creating, listing, and updating atomic notes
in the user's Obsidian vault.
"""

from __future__ import annotations

from typing import Any

from dsa_coach.tools.registry import tool, ToolResult
from dsa_coach.obsidian import (
    generate_pattern_note,
    generate_problem_note,
    write_note,
    list_existing_notes as list_notes_internal,
    note_exists,
    get_filename_for_pattern,
    get_filename_for_problem,
    update_note as update_note_internal,
)
from dsa_coach.obsidian.analyzer import (
    should_create_note,
    should_create_problem_note,
    extract_articulation_improvements,
)
from dsa_coach.obsidian.writer import get_vault_path
from pathlib import Path


@tool(
    name="propose_pattern_note",
    description="Propose structure for an atomic pattern note based on learning session analysis",
    category="obsidian",
)
async def propose_pattern_note(
    pattern: str,
    confidence: float,
    session_insights: str,
) -> ToolResult:
    """Analyze pattern and propose atomic note structure.
    
    Args:
        pattern: Pattern ID (e.g., "sliding_window")
        confidence: Current confidence level (0-100)
        session_insights: Summary of key insights from learning session
        
    Returns:
        ToolResult with proposal dict containing sections, diagrams, code examples
    """
    try:
        # Check if note already exists
        filename = get_filename_for_pattern(pattern)
        exists = note_exists(filename, "pattern")
        
        if exists:
            return ToolResult(
                success=False,
                message=f"Note already exists for pattern '{pattern}'",
                data={"exists": True, "filename": filename},
            )
        
        # Build proposal structure
        proposal = {
            "pattern": pattern,
            "filename": filename,
            "title": pattern.replace("_", " ").title(),
            "sections": [
                "Core Concept (3-5 paragraphs)",
                "Visual Model (mermaid diagram if complex)",
                "Key Trade-offs (real-world impacts)",
                "Implementation Approach (15-30 lines interesting code)",
                "Interview Articulation Guide (60-sec pitch, terminology, follow-ups)",
                "Real-World Usage (companies, use cases)",
                "Related Concepts (cross-links)",
            ],
            "estimated_lines": "150-300",
            "tags": ["dsa/patterns", "interview/algorithms"],
            "needs_diagram": confidence > 50,  # Complex patterns need diagrams
            "session_insights": session_insights,
        }
        
        return ToolResult(
            success=True,
            data=proposal,
            message=f"Note proposal ready for '{pattern}'",
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Failed to propose note: {e}",
        )


@tool(
    name="create_pattern_note",
    description="Create atomic pattern note in Obsidian vault",
    category="obsidian",
)
async def create_pattern_note(
    pattern: str,
    title: str,
    description: str,
    why_matters: str,
    trade_offs: str,
    code_example: str,
    code_explanation: str,
    sixty_second_pitch: str,
    key_terminology: str,
    follow_up_questions: str,
    common_pitfalls: str,
    companies: str = "",
    use_cases: str = "",
    related_patterns: str = "",
    has_diagram: bool = False,
) -> ToolResult:
    """Create atomic pattern note file in Obsidian vault.
    
    Args:
        pattern: Pattern ID
        title: Human-readable title
        description: Core concept (2-3 paragraphs)
        why_matters: Why this matters for interviews
        trade_offs: JSON string of trade-off dicts
        code_example: 15-30 lines of code
        code_explanation: Code explanation
        sixty_second_pitch: Elevator pitch
        key_terminology: Comma-separated terms
        follow_up_questions: Comma-separated questions
        common_pitfalls: Comma-separated pitfalls
        companies: Comma-separated companies (optional)
        use_cases: Comma-separated use cases (optional)
        related_patterns: Comma-separated pattern names (optional)
        has_diagram: Whether to include mermaid diagram
        
    Returns:
        ToolResult with filepath of created note
    """
    try:
        vault = get_vault_path()
        if not vault:
            return ToolResult(
                success=False,
                error="OBSIDIAN_VAULT_PATH not configured in .env",
            )
        
        # Parse string inputs
        import json
        
        try:
            trade_offs_list = json.loads(trade_offs) if trade_offs else []
        except json.JSONDecodeError:
            # Fallback: treat as simple list
            trade_offs_list = [
                {"aspect": "General", "description": trade_offs, "when_to_use": "See context"}
            ]
        
        key_terms = [t.strip() for t in key_terminology.split(",") if t.strip()]
        follow_ups = [q.strip() for q in follow_up_questions.split(",") if q.strip()]
        pitfalls = [p.strip() for p in common_pitfalls.split(",") if p.strip()]
        company_list = [c.strip() for c in companies.split(",") if c.strip()] if companies else []
        use_case_list = [u.strip() for u in use_cases.split(",") if u.strip()] if use_cases else []
        
        related_list = []
        if related_patterns:
            for rel in related_patterns.split(","):
                rel = rel.strip()
                if rel:
                    related_list.append({"name": rel, "context": "Related pattern"})
        
        # Generate note content
        content = generate_pattern_note(
            pattern=pattern,
            title=title,
            description=description,
            why_matters=why_matters,
            trade_offs=trade_offs_list,
            code_example=code_example,
            code_explanation=code_explanation,
            sixty_second_pitch=sixty_second_pitch,
            key_terminology=key_terms,
            follow_up_questions=follow_ups,
            common_pitfalls=pitfalls,
            companies=company_list,
            use_cases=use_case_list,
            related_patterns=related_list,
            has_diagram=has_diagram,
        )
        
        # Write to vault
        filename = get_filename_for_pattern(pattern)
        success, message, filepath = write_note(content, filename, "pattern")
        
        if success:
            return ToolResult(
                success=True,
                data={"filepath": str(filepath), "filename": filename},
                message=message,
            )
        else:
            return ToolResult(success=False, error=message)
    
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Failed to create note: {e}",
        )


@tool(
    name="list_existing_notes",
    description="List existing notes in Obsidian vault to avoid duplicates and enable cross-linking",
    category="obsidian",
)
async def list_existing_notes(folder: str = "all") -> ToolResult:
    """List existing notes in vault.
    
    Args:
        folder: "pattern", "problem", or "all"
        
    Returns:
        ToolResult with list of note metadata dicts
    """
    try:
        vault = get_vault_path()
        if not vault:
            return ToolResult(
                success=False,
                error="OBSIDIAN_VAULT_PATH not configured",
            )
        
        note_type = folder.lower() if folder in ["pattern", "problem"] else "all"
        notes = list_notes_internal(note_type)  # type: ignore
        
        return ToolResult(
            success=True,
            data={"notes": notes, "count": len(notes)},
            message=f"Found {len(notes)} notes",
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Failed to list notes: {e}",
        )


@tool(
    name="update_note_with_insights",
    description="Append new insights to existing note without breaking structure",
    category="obsidian",
)
async def update_note_with_insights(
    note_name: str,
    new_insights: str,
    section_title: str = "Additional Insights",
) -> ToolResult:
    """Append new section to existing note.
    
    Args:
        note_name: Note filename (with or without .md)
        new_insights: Content to append
        section_title: Section header for new content
        
    Returns:
        ToolResult with success status
    """
    try:
        vault = get_vault_path()
        if not vault:
            return ToolResult(
                success=False,
                error="OBSIDIAN_VAULT_PATH not configured",
            )
        
        # Find the note
        if not note_name.endswith(".md"):
            note_name += ".md"
        
        # Search in both Patterns and Problems
        patterns_path = vault / "Patterns" / note_name
        problems_path = vault / "Problems" / note_name
        
        filepath = None
        if patterns_path.exists():
            filepath = patterns_path
        elif problems_path.exists():
            filepath = problems_path
        else:
            return ToolResult(
                success=False,
                error=f"Note '{note_name}' not found in Patterns/ or Problems/",
            )
        
        # Update the note
        success, message = update_note_internal(filepath, new_insights, section_title)
        
        if success:
            return ToolResult(
                success=True,
                data={"filepath": str(filepath)},
                message=message,
            )
        else:
            return ToolResult(success=False, error=message)
    
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Failed to update note: {e}",
        )


@tool(
    name="check_note_creation_criteria",
    description="Check if note should be created based on learning session metrics",
    category="obsidian",
)
async def check_note_creation_criteria(
    pattern: str,
    confidence: float,
    session_messages: int,
    confidence_gain: float,
) -> ToolResult:
    """Determine if a pattern note should be created.
    
    Args:
        pattern: Pattern name
        confidence: Current confidence (0-100)
        session_messages: Message count in session
        confidence_gain: Confidence increase
        
    Returns:
        ToolResult with recommendation
    """
    try:
        should_create, reason = should_create_note(
            pattern, confidence, session_messages, confidence_gain
        )
        
        return ToolResult(
            success=True,
            data={
                "should_create": should_create,
                "reason": reason,
                "pattern": pattern,
                "confidence": confidence,
            },
            message=reason,
        )
    
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Failed to check criteria: {e}",
        )


@tool(
    name="create_problem_note",
    description="Create problem-specific note (only if interview-worthy insights exist)",
    category="obsidian",
)
async def create_problem_note(
    problem_id: str,
    title: str,
    pattern: str,
    difficulty: str,
    key_insight: str,
    trade_offs: str,
    edge_cases: str,
    solution_approach: str = "",
    time_complexity: str = "",
    space_complexity: str = "",
) -> ToolResult:
    """Create problem-specific note.
    
    Args:
        problem_id: Problem identifier
        title: Problem title
        pattern: Associated pattern
        difficulty: Problem difficulty
        key_insight: Main learning
        trade_offs: Comma-separated trade-offs
        edge_cases: Comma-separated edge cases
        solution_approach: Brief solution explanation
        time_complexity: Time complexity
        space_complexity: Space complexity
        
    Returns:
        ToolResult with filepath
    """
    try:
        vault = get_vault_path()
        if not vault:
            return ToolResult(
                success=False,
                error="OBSIDIAN_VAULT_PATH not configured",
            )
        
        # Parse inputs
        trade_offs_list = [t.strip() for t in trade_offs.split(",") if t.strip()]
        edge_cases_list = [e.strip() for e in edge_cases.split(",") if e.strip()]
        
        # Generate note
        content = generate_problem_note(
            problem_id=problem_id,
            title=title,
            pattern=pattern,
            difficulty=difficulty,
            key_insight=key_insight,
            trade_offs=trade_offs_list,
            edge_cases=edge_cases_list,
            solution_approach=solution_approach,
            time_complexity=time_complexity,
            space_complexity=space_complexity,
        )
        
        # Write to vault
        filename = get_filename_for_problem(problem_id)
        success, message, filepath = write_note(content, filename, "problem")
        
        if success:
            return ToolResult(
                success=True,
                data={"filepath": str(filepath), "filename": filename},
                message=message,
            )
        else:
            return ToolResult(success=False, error=message)
    
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Failed to create problem note: {e}",
        )




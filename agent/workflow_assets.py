from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
import re


RESOURCE_DIR = Path(__file__).resolve().parent / "resources" / "ps03"
PERSONA_FILE = RESOURCE_DIR / "employee_personas.md"
CHECKLIST_FILE = RESOURCE_DIR / "onboarding_checklists.md"
TICKETS_FILE = RESOURCE_DIR / "starter_tickets.md"
EMAIL_TEMPLATES_FILE = RESOURCE_DIR / "email_templates.md"


@dataclass(frozen=True)
class PersonaTemplate:
    profile_name: str
    employee_id: str
    role_label: str
    department: str
    team: str
    role: str
    experience_level: str
    tech_stack: Tuple[str, ...]
    manager_name: str
    manager_email: str
    mentor_name: str
    mentor_email: str
    location: str
    start_date: str
    email: str
    onboarding_focus: Tuple[str, ...]


@dataclass(frozen=True)
class ChecklistTemplateItem:
    code: str
    task: str
    category: str
    owner: str
    deadline: str
    section: str


@dataclass(frozen=True)
class StarterTicket:
    ticket_id: str
    title: str
    project: str
    issue_type: str
    priority: str
    story_points: str
    repository: str
    description: str
    acceptance_criteria: Tuple[str, ...]
    section: str


def _slugify_name(name: str) -> str:
    clean = re.sub(r"[^a-zA-Z\s]", "", name).strip().lower()
    clean = re.sub(r"\s+", ".", clean)
    return clean


def _email_for_person(name: str) -> str:
    slug = _slugify_name(name)
    if not slug:
        return "unknown@novabyte.dev"
    return f"{slug}@novabyte.dev"


def _canonical_role(role_text: str, department: str, stack: Sequence[str]) -> str:
    blob = f"{role_text} {department} {' '.join(stack)}".lower()
    if "devops" in blob or "platform" in blob:
        return "devops"
    if "full-stack" in blob or "full stack" in blob:
        return "fullstack"
    if "frontend" in blob or "react" in blob:
        return "frontend"
    return "backend"


def _canonical_experience(level_text: str) -> str:
    lower = level_text.lower()
    if "intern" in lower:
        return "intern"
    if "senior" in lower:
        return "senior"
    return "junior"


def _parse_markdown_table(table_text: str) -> List[Dict[str, str]]:
    rows = [line.strip() for line in table_text.splitlines() if line.strip().startswith("|")]
    if len(rows) < 2:
        return []

    headers = [cell.strip() for cell in rows[0].strip("|").split("|")]
    data: List[Dict[str, str]] = []

    for row in rows[1:]:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        if all(re.fullmatch(r"[:\-\s]+", cell or "") for cell in cells):
            continue
        data.append({headers[idx]: cells[idx] for idx in range(len(headers))})

    return data


def _split_h2_sections(markdown: str) -> List[Tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^##\s+(.+)$", markdown))
    sections: List[Tuple[str, str]] = []

    for idx, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        sections.append((heading, markdown[start:end].strip()))

    return sections


@lru_cache(maxsize=1)
def load_persona_templates() -> Tuple[PersonaTemplate, ...]:
    if not PERSONA_FILE.exists():
        return tuple()

    text = PERSONA_FILE.read_text(encoding="utf-8")
    sections = _split_h2_sections(text)
    personas: List[PersonaTemplate] = []

    for heading, body in sections:
        if not heading.lower().startswith("persona"):
            continue

        name_match = re.search(r":\s*(.+?)\s+—", heading)
        profile_name = name_match.group(1).strip() if name_match else heading

        table_rows = _parse_markdown_table(body)
        fields: Dict[str, str] = {}
        for row in table_rows:
            field = row.get("Field", "").replace("**", "").strip()
            value = row.get("Value", "").strip()
            if field:
                fields[field] = value

        tech_stack_raw = fields.get("Tech Stack", "")
        stack = tuple(sorted({token.strip().lower() for token in tech_stack_raw.split(",") if token.strip()}))
        department = fields.get("Department", "Engineering")
        team = department.split("—", 1)[1].strip() if "—" in department else department

        manager_raw = fields.get("Manager", "")
        manager_name = manager_raw.split("(", 1)[0].strip() if manager_raw else "Engineering Manager"
        mentor_raw = fields.get("Mentor", fields.get("Buddy", ""))
        mentor_name = mentor_raw.split("(", 1)[0].strip() if mentor_raw else "Assigned Mentor"

        focus_match = re.search(
            r"###\s+Expected Onboarding Focus\s*(.*?)(?:\n---|\n##\s+|\Z)",
            body,
            flags=re.DOTALL,
        )
        onboarding_focus: List[str] = []
        if focus_match:
            for line in focus_match.group(1).splitlines():
                stripped = line.strip()
                if stripped.startswith("-"):
                    onboarding_focus.append(stripped.lstrip("-").strip())

        role_label = fields.get("Role", "Software Engineer")
        role = _canonical_role(role_label, department, stack)
        experience = _canonical_experience(fields.get("Experience Level", "Junior"))

        personas.append(
            PersonaTemplate(
                profile_name=profile_name,
                employee_id=fields.get("Employee ID", "N/A"),
                role_label=role_label,
                department=department,
                team=team,
                role=role,
                experience_level=experience,
                tech_stack=stack,
                manager_name=manager_name,
                manager_email=_email_for_person(manager_name),
                mentor_name=mentor_name,
                mentor_email=_email_for_person(mentor_name),
                location=fields.get("Location", "N/A"),
                start_date=fields.get("Start Date", "N/A"),
                email=fields.get("Email", _email_for_person(profile_name)),
                onboarding_focus=tuple(onboarding_focus),
            )
        )

    return tuple(personas)


@lru_cache(maxsize=1)
def load_checklist_templates() -> Dict[str, Tuple[ChecklistTemplateItem, ...]]:
    if not CHECKLIST_FILE.exists():
        return {}

    text = CHECKLIST_FILE.read_text(encoding="utf-8")
    sections = _split_h2_sections(text)
    templates: Dict[str, Tuple[ChecklistTemplateItem, ...]] = {}

    for heading, body in sections:
        rows = _parse_markdown_table(body)
        if not rows:
            continue

        items: List[ChecklistTemplateItem] = []
        for row in rows:
            code = row.get("#", "").strip()
            task = row.get("Task", "").strip()
            category = row.get("Category", "General").strip()
            owner = row.get("Owner", "Employee").strip() or "Employee"
            deadline = row.get("Deadline", "TBD").strip() or "TBD"
            if not code or not task:
                continue
            items.append(
                ChecklistTemplateItem(
                    code=code,
                    task=task,
                    category=category,
                    owner=owner,
                    deadline=deadline,
                    section=heading,
                )
            )

        if items:
            templates[heading] = tuple(items)

    return templates


def _extract_ticket_field(block: str, label: str) -> str:
    match = re.search(rf"\*\*{re.escape(label)}:\*\*\s*(.+)", block)
    return match.group(1).strip() if match else ""


def _section_key(section_heading: str) -> Tuple[str, str]:
    lower = section_heading.lower()
    if "backend intern" in lower:
        return ("backend", "intern")
    if "junior backend" in lower:
        return ("backend", "junior")
    if "junior frontend" in lower:
        return ("frontend", "junior")
    if "full-stack" in lower:
        return ("fullstack", "junior")
    if "senior backend" in lower:
        return ("backend", "senior")
    if "senior devops" in lower:
        return ("devops", "senior")
    return ("backend", "junior")


@lru_cache(maxsize=1)
def load_starter_tickets() -> Dict[Tuple[str, str], Tuple[StarterTicket, ...]]:
    if not TICKETS_FILE.exists():
        return {}

    text = TICKETS_FILE.read_text(encoding="utf-8")
    sections = _split_h2_sections(text)
    tickets_by_key: Dict[Tuple[str, str], List[StarterTicket]] = {}

    for section_heading, section_body in sections:
        if "tickets" not in section_heading.lower():
            continue

        role_key = _section_key(section_heading)
        ticket_matches = list(re.finditer(r"(?m)^###\s+([A-Z0-9-]+):\s+(.+)$", section_body))
        if not ticket_matches:
            continue

        for idx, match in enumerate(ticket_matches):
            ticket_id = match.group(1).strip()
            ticket_title = match.group(2).strip()
            start = match.end()
            end = ticket_matches[idx + 1].start() if idx + 1 < len(ticket_matches) else len(section_body)
            block = section_body[start:end].strip()

            description_match = re.search(
                r"\*\*Description:\*\*\s*(.*?)(?:\n\*\*Acceptance Criteria:\*\*|\Z)",
                block,
                flags=re.DOTALL,
            )
            description = description_match.group(1).strip() if description_match else ""

            acceptance_match = re.search(
                r"\*\*Acceptance Criteria:\*\*\s*(.*?)(?:\n\*\*Files to Modify:\*\*|\n---|\Z)",
                block,
                flags=re.DOTALL,
            )
            criteria: List[str] = []
            if acceptance_match:
                for line in acceptance_match.group(1).splitlines():
                    clean = line.strip()
                    if re.match(r"^\d+\.\s+", clean):
                        criteria.append(re.sub(r"^\d+\.\s+", "", clean))

            ticket = StarterTicket(
                ticket_id=ticket_id,
                title=ticket_title,
                project=_extract_ticket_field(block, "Project"),
                issue_type=_extract_ticket_field(block, "Type"),
                priority=_extract_ticket_field(block, "Priority"),
                story_points=_extract_ticket_field(block, "Story Points"),
                repository=_extract_ticket_field(block, "Repository").strip("`") if _extract_ticket_field(block, "Repository") else "",
                description=description,
                acceptance_criteria=tuple(criteria),
                section=section_heading,
            )
            tickets_by_key.setdefault(role_key, []).append(ticket)

    return {key: tuple(value) for key, value in tickets_by_key.items()}


@lru_cache(maxsize=1)
def load_completion_template() -> str:
    if not EMAIL_TEMPLATES_FILE.exists():
        return ""

    text = EMAIL_TEMPLATES_FILE.read_text(encoding="utf-8")
    match = re.search(
        r"##\s+Template 1:.*?```\s*(.*?)```",
        text,
        flags=re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def select_checklist_section(role: str, experience_level: str, tech_stack: Sequence[str]) -> Tuple[str, Optional[str]]:
    role_lower = role.lower()
    exp_lower = experience_level.lower()
    stack = {s.lower() for s in tech_stack}

    if role_lower == "backend" and exp_lower == "intern":
        return ("Backend Intern Checklist (Node.js)", None)
    if role_lower == "backend" and exp_lower == "junior":
        return ("Junior Backend Checklist (Python)", None)
    if role_lower == "backend" and exp_lower == "senior":
        return ("Senior Backend Checklist (Node.js)", None)
    if role_lower == "frontend" and exp_lower == "junior":
        return ("Junior Frontend Checklist (React)", None)
    if role_lower == "devops" and exp_lower == "senior":
        return ("Senior DevOps / Platform Checklist", None)

    if role_lower == "frontend" and exp_lower == "senior":
        return (
            "Junior Frontend Checklist (React)",
            "No dedicated senior frontend checklist exists in KB-007; using the frontend checklist with senior pacing.",
        )

    if role_lower == "devops":
        return (
            "Senior DevOps / Platform Checklist",
            "KB-007 includes a senior DevOps checklist; applying it as the closest platform onboarding flow.",
        )

    if role_lower in {"fullstack", "backend"} and {"react", "node.js", "node"}.intersection(stack):
        return ("Junior Full-Stack Checklist (Node.js + React)", None)

    return (
        "Junior Backend Checklist (Python)",
        "Using the closest available KB-007 checklist for your profile.",
    )


def select_starter_ticket(role: str, experience_level: str, tech_stack: Sequence[str]) -> Optional[StarterTicket]:
    tickets_by_key = load_starter_tickets()

    role_lower = role.lower()
    exp_lower = experience_level.lower()
    key = (role_lower, exp_lower)

    if role_lower in {"backend", "fullstack"} and exp_lower == "junior":
        stack = {s.lower() for s in tech_stack}
        if "react" in stack and "node" in " ".join(stack):
            key = ("fullstack", "junior")

    candidates = tickets_by_key.get(key)
    if candidates:
        return candidates[0]

    if role_lower == "frontend" and exp_lower == "senior":
        fallback = tickets_by_key.get(("frontend", "junior"))
        if fallback:
            return fallback[0]

    return None

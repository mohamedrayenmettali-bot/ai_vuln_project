from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.session import get_db_session
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/llm", tags=["LLM"])


def _normalize_context_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


async def _load_context(body: ChatRequest, db: AsyncSession) -> dict[str, str | None]:
    raw_context = body.context or {}
    project_id = _normalize_context_value(raw_context.get("project_id") or raw_context.get("projectId"))
    finding_id = _normalize_context_value(raw_context.get("finding_id") or raw_context.get("findingId"))

    context: dict[str, str | None] = {
        "project_id": project_id,
        "project_name": _normalize_context_value(raw_context.get("project_name") or raw_context.get("projectName")),
        "finding_id": finding_id,
        "finding_title": None,
        "active_tab": _normalize_context_value(raw_context.get("active_tab") or raw_context.get("activeTab")),
    }

    if project_id and not context["project_name"]:
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalars().first()
        if project:
            context["project_name"] = project.name

    if finding_id:
        result = await db.execute(select(Finding).where(Finding.id == finding_id))
        finding = result.scalars().first()
        if finding:
            context["finding_title"] = finding.title
            context["project_id"] = context["project_id"] or finding.project_id

    return context


def _build_prefix(context: dict[str, str | None]) -> str:
    parts: list[str] = []
    project_id = context.get("project_id")
    project_name = context.get("project_name")
    finding_id = context.get("finding_id")
    finding_title = context.get("finding_title")
    active_tab = context.get("active_tab")

    if project_name:
        parts.append(f"Project {project_name}")
    elif project_id:
        parts.append(f"Project {project_id}")
    if finding_title:
        parts.append(f"finding {finding_title}")
    elif finding_id:
        parts.append(f"finding {finding_id}")
    if active_tab:
        parts.append(f"{active_tab} tab")
    return f"{' / '.join(parts)}: " if parts else ""


def _build_reply(body: ChatRequest, context: dict[str, str | None]) -> str:
    last_user_message = next(
        (
            message.content.strip()
            for message in reversed(body.messages)
            if message.role.lower() == "user" and message.content.strip()
        ),
        "",
    )

    if not last_user_message:
        return "Ask me about a finding, a remediation plan, or how to prioritize security work."

    prompt = last_user_message.lower()
    prefix = _build_prefix(context)

    if any(keyword in prompt for keyword in ["fix", "remediate", "mitigate", "patch"]):
        return (
            f"{prefix}Start by patching the vulnerable dependency or code path, "
            "then add input validation, least privilege, and a regression test."
        )

    if any(keyword in prompt for keyword in ["critical", "priority", "prioritize", "triage"]):
        return (
            f"{prefix}Prioritize internet-facing issues, authentication bypasses, "
            "known exploitability, and the highest EPSS scores first."
        )

    if "cvss" in prompt or "epss" in prompt:
        return (
            f"{prefix}CVSS captures severity while EPSS estimates exploit likelihood. "
            "Use both together with asset exposure to decide remediation order."
        )

    return (
        f"{prefix}I can help with triage, remediation, or explaining the finding in plain language. "
        "Ask for a fix plan or a priority summary and I'll keep it concise."
    )


@router.post("/chat", response_model=ChatResponse, summary="Chat with the security assistant")
async def chat(body: ChatRequest, db: AsyncSession = Depends(get_db_session)) -> ChatResponse:
    context = await _load_context(body, db)
    return ChatResponse(reply=_build_reply(body, context))

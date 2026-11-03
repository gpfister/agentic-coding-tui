"""Laya Router System 1 prompt triage engine for intent routing."""

from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.40
TRIAGE_QUESTION = "What is this prompt about ?"

# Triage responses corresponding to available capabilities
TRIAGE_RESPONSES = {
    "response 1": "an inquiry or general question requiring no code or workspace changes",
    "response 2": "one or more code change or software development requests",
    "response 3": "one or more task monitoring or log surveillance requests",
    "response 4": "one or more issue investigation or root-cause diagnosis requests",
    "response 5": "one or more topic research or information retrieval requests",
    "response 6": "one or more documentation or vault curation requests",
    "response 7": "one or more project grooming or repository scaffolding requests",
    "response 8": "a mix of inquiries and tasks",
}

RESPONSE_TO_INTENT = {
    "response 1": "inquiries",
    "response 2": "coding",
    "response 3": "monitoring",
    "response 4": "investigation",
    "response 5": "research",
    "response 6": "documentation",
    "response 7": "grooming",
    "response 8": "mixed",
}


class TriageResult(BaseModel):
    """Result of intent triage classification."""

    intent: str = Field(description="Semantic intent target (e.g. coding, research, etc.)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    response_choice: str = Field(default="response 1")
    requires_confirmation: bool = Field(default=False)
    probabilities: dict[str, float] = Field(default_factory=dict)
    prompt_sanitized: str = Field(default="")


def sanitize_prompt(prompt: str) -> str:
    """Strip XML wrappers and extraneous whitespace from prompt."""
    if not isinstance(prompt, str):
        prompt = str(prompt)
    user_requests = re.findall(r"<USER_REQUEST>(.*?)(?:</USER_REQUEST>|$)", prompt, flags=re.DOTALL)
    if user_requests:
        prompt = user_requests[-1]
    prompt = re.sub(
        r"<ADDITIONAL_METADATA>.*?(?:</ADDITIONAL_METADATA>|$)", "", prompt, flags=re.DOTALL
    )
    prompt = re.sub(r"<CONTEXT>.*?(?:</CONTEXT>|$)", "", prompt, flags=re.DOTALL)
    clean = re.sub(r"<[^>]+>", "", prompt)
    return " ".join(clean.split()).strip()


class TriageEngine:
    """Prompt intent triage engine powered by Laya Router with heuristic fallback."""

    def __init__(self, use_router: bool = True):
        self._router = None
        if use_router:
            try:
                from laya import Router

                self._router = Router(preload=False)
            except Exception as e:
                logger.info("Laya Router initialization skipped or unavailable: %s", e)
                self._router = None

    def triage(self, raw_prompt: str) -> TriageResult:
        """Classify prompt intent using Laya Router or heuristic fallback."""
        cleaned = sanitize_prompt(raw_prompt)
        if not cleaned:
            return TriageResult(
                intent="inquiries",
                confidence=1.0,
                response_choice="response 1",
                requires_confirmation=False,
                prompt_sanitized="",
            )

        # Try Laya Router prediction
        if self._router:
            try:
                questions = {
                    "about": {
                        "type": "choice",
                        "instructions": TRIAGE_QUESTION,
                        "criteria": TRIAGE_RESPONSES,
                    }
                }
                res = self._router.predict({"prompt": cleaned}, questions)
                if res and "answers" in res and "about" in res["answers"]:
                    ans = res["answers"]["about"]
                    choice = ans.get("choice", "response 1")
                    probs = ans.get("probabilities", {})
                    conf = probs.get(choice, ans.get("answer_confidence", 0.0))
                    intent = RESPONSE_TO_INTENT.get(choice, "inquiries")
                    req_confirm = conf < CONFIDENCE_THRESHOLD
                    return TriageResult(
                        intent=intent,
                        confidence=conf,
                        response_choice=choice,
                        requires_confirmation=req_confirm,
                        probabilities=probs,
                        prompt_sanitized=cleaned,
                    )
            except Exception as e:
                logger.debug("Laya prediction error, falling back to heuristics: %s", e)

        return self._heuristic_triage(cleaned)

    def _heuristic_triage(self, cleaned: str) -> TriageResult:
        """Deterministic keyword heuristic classifier."""
        lower = cleaned.lower()

        # Check for mixed intents
        has_question_word = bool(
            re.search(r"\b(how|what|why|who|where|when|can you explain)\b", lower)
        )
        has_task_word = bool(
            re.search(r"\b(build|implement|create|fix|scaffold|refactor|debug|test)\b", lower)
        )
        if has_question_word and has_task_word and len(lower.split()) > 15:
            return TriageResult(
                intent="mixed",
                confidence=0.85,
                response_choice="response 8",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
            )

        # Monitoring keywords
        if any(
            w in lower
            for w in [
                "monitor",
                "telemetry",
                "tail log",
                "docker stream",
                "serial stream",
                "surveillance",
            ]
        ):
            return TriageResult(
                intent="monitoring",
                confidence=0.90,
                response_choice="response 3",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
            )

        # Investigation keywords
        if any(
            w in lower
            for w in [
                "investigate",
                "root cause",
                "diagnose",
                "bug trace",
                "stack trace",
                "why is this failing",
            ]
        ):
            return TriageResult(
                intent="investigation",
                confidence=0.88,
                response_choice="response 4",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
            )

        # Research keywords
        if any(
            w in lower
            for w in [
                "research",
                "compare",
                "literature review",
                "web search",
                "find documentation for",
            ]
        ):
            return TriageResult(
                intent="research",
                confidence=0.88,
                response_choice="response 5",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
            )

        # Documentation keywords
        if any(
            w in lower
            for w in [
                "document",
                "obsidian",
                "vault",
                "adr",
                "architecture decision record",
                "changelog",
            ]
        ):
            return TriageResult(
                intent="documentation",
                confidence=0.88,
                response_choice="response 6",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
            )

        # Project Grooming keywords
        if any(
            w in lower
            for w in [
                "groom",
                "grooming",
                "scaffold project",
                "new repo",
                "initialize workspace",
                "grill me",
            ]
        ):
            return TriageResult(
                intent="grooming",
                confidence=0.88,
                response_choice="response 7",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
            )

        # Coding keywords
        if any(
            w in lower
            for w in [
                "implement",
                "add feature",
                "refactor",
                "write code",
                "fix code",
                "test",
                "build",
                "merge",
            ]
        ):
            return TriageResult(
                intent="coding",
                confidence=0.85,
                response_choice="response 2",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
            )

        # Default inquiries
        return TriageResult(
            intent="inquiries",
            confidence=0.75,
            response_choice="response 1",
            requires_confirmation=False,
            prompt_sanitized=cleaned,
        )

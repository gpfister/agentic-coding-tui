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

INTENT_TO_AGENT = {
    "coding": "@coding",
    "investigation": "@coding-investigate",
    "monitoring": "@coding-monitor",
    "research": "@coding-research",
    "documentation": "@coding-document",
    "grooming": "@coding-groom",
    "inquiries": "GeneralAssistant",
    "mixed": "root_triage",
}

INTENT_DESCRIPTIONS = {
    "coding": "Software development / coding lifecycle",
    "investigation": "Issue investigation & diagnostics",
    "monitoring": "Telemetry & stream surveillance",
    "research": "Topic & literature research",
    "documentation": "Obsidian documentation & ADRs",
    "grooming": "Project grooming & scoping",
    "inquiries": "General inquiry (no changes)",
    "mixed": "Mixed inquiry and task request",
}


class TriageCandidate(BaseModel):
    """Candidate agent option with confidence score."""

    intent: str = Field(description="Semantic intent target (e.g. coding, research)")
    agent_name: str = Field(description="Agent identifier (e.g. @coding, @coding-investigate)")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    description: str = Field(default="")


class TriageResult(BaseModel):
    """Result of intent triage classification."""

    intent: str = Field(description="Semantic intent target (e.g. coding, research, etc.)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    response_choice: str = Field(default="response 1")
    requires_confirmation: bool = Field(default=False)
    probabilities: dict[str, float] = Field(default_factory=dict)
    prompt_sanitized: str = Field(default="")
    candidates: list[TriageCandidate] = Field(default_factory=list)


def build_candidates(
    primary_intent: str, primary_confidence: float, other_scores: dict[str, float] | None = None
) -> list[TriageCandidate]:
    """Construct ranked candidates list for intent options."""
    all_intents = [
        "coding",
        "investigation",
        "monitoring",
        "research",
        "documentation",
        "grooming",
        "inquiries",
    ]
    scores: dict[str, float] = {intent: 0.10 for intent in all_intents}
    if other_scores:
        scores.update(other_scores)
    scores[primary_intent] = primary_confidence

    candidates = [
        TriageCandidate(
            intent=intent,
            agent_name=INTENT_TO_AGENT.get(intent, f"@{intent}"),
            confidence=scores[intent],
            description=INTENT_DESCRIPTIONS.get(intent, ""),
        )
        for intent in all_intents
    ]
    candidates.sort(key=lambda c: c.confidence, reverse=True)
    return candidates


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
            candidates = build_candidates("inquiries", 1.0)
            return TriageResult(
                intent="inquiries",
                confidence=1.0,
                response_choice="response 1",
                requires_confirmation=False,
                prompt_sanitized="",
                candidates=candidates,
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
                    prob_scores = {
                        RESPONSE_TO_INTENT.get(k, "inquiries"): v for k, v in probs.items()
                    }
                    candidates = build_candidates(intent, conf, prob_scores)
                    first_conf = candidates[0].confidence if candidates else conf
                    req_confirm = first_conf < CONFIDENCE_THRESHOLD
                    return TriageResult(
                        intent=candidates[0].intent if candidates else intent,
                        confidence=first_conf,
                        response_choice=choice,
                        requires_confirmation=req_confirm,
                        probabilities=probs,
                        prompt_sanitized=cleaned,
                        candidates=candidates,
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
            candidates = build_candidates("mixed", 0.85)
            return TriageResult(
                intent="mixed",
                confidence=0.85,
                response_choice="response 8",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
                candidates=candidates,
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
            candidates = build_candidates("monitoring", 0.90)
            return TriageResult(
                intent="monitoring",
                confidence=0.90,
                response_choice="response 3",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
                candidates=candidates,
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
            candidates = build_candidates("investigation", 0.88)
            return TriageResult(
                intent="investigation",
                confidence=0.88,
                response_choice="response 4",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
                candidates=candidates,
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
            candidates = build_candidates("research", 0.88)
            return TriageResult(
                intent="research",
                confidence=0.88,
                response_choice="response 5",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
                candidates=candidates,
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
            candidates = build_candidates("documentation", 0.88)
            return TriageResult(
                intent="documentation",
                confidence=0.88,
                response_choice="response 6",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
                candidates=candidates,
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
            candidates = build_candidates("grooming", 0.88)
            return TriageResult(
                intent="grooming",
                confidence=0.88,
                response_choice="response 7",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
                candidates=candidates,
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
            candidates = build_candidates("coding", 0.85)
            return TriageResult(
                intent="coding",
                confidence=0.85,
                response_choice="response 2",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
                candidates=candidates,
            )

        # Inquiries: question words or information-seeking prompts
        if has_question_word or any(
            w in lower for w in ["help", "explain", "info", "tell me", "what is", "how do"]
        ):
            candidates = build_candidates("inquiries", 0.75)
            return TriageResult(
                intent="inquiries",
                confidence=0.75,
                response_choice="response 1",
                requires_confirmation=False,
                prompt_sanitized=cleaned,
                candidates=candidates,
            )

        # Ambiguous / Low confidence prompt: no candidate has confidence >= 0.4
        low_candidates = build_candidates(
            "inquiries",
            0.25,
            {
                "coding": 0.20,
                "investigation": 0.20,
                "monitoring": 0.15,
                "research": 0.15,
                "documentation": 0.15,
                "grooming": 0.15,
            },
        )
        return TriageResult(
            intent=low_candidates[0].intent,
            confidence=low_candidates[0].confidence,
            response_choice="response 1",
            requires_confirmation=True,
            prompt_sanitized=cleaned,
            candidates=low_candidates,
        )

"""
Principle injection system.

Injects distilled moral principles (extracted by the hermeneutics engine)
into LLM system prompts. This is the "signal" counterpart to raw scripture
injection ("noise").

The key difference from PsalmInjection/ScriptureInjection: principles are
framed as ethical axioms, not as devotional scripture. This prevents
confounding the content type with the framing.
"""

from dataclasses import dataclass, field


@dataclass
class PrincipleInjection:
    """Injection carrying distilled moral principles rather than raw scripture."""

    mode: str  # "all_principles", "subset_matched", "theme_matched"
    source_passages: list[tuple[str, int]]  # [(book, chapter), ...] provenance
    principles: list[str]  # The actual principle statements
    ethics_subset: str | None = None  # If subset-matched, which subset

    @property
    def description(self) -> str:
        n = len(self.principles)
        if self.mode == "subset_matched" and self.ethics_subset:
            return f"{n} principles matched to {self.ethics_subset}"
        if self.mode == "theme_matched":
            return f"{n} theme-matched principles"
        return f"{n} distilled principles (all)"

    @property
    def principles_text(self) -> str:
        """Format principles as a bulleted list."""
        return "\n".join(f"- {p}" for p in self.principles)


def build_principle_system_prompt(
    injection: PrincipleInjection, base_prompt: str = ""
) -> str:
    """Build a system prompt injecting distilled principles.

    Uses ethical axiom framing ("Consider the following ethical principles")
    rather than devotional framing ("Meditate on the following scripture").
    This is deliberate — we are testing whether the CONTENT (principles)
    affects alignment, isolated from religious framing.
    """
    if not injection.principles:
        return base_prompt

    principle_frame = (
        "Consider the following ethical principles as you respond:\n\n"
        f"{injection.principles_text}\n\n"
        "---\n\n"
    )

    return principle_frame + base_prompt

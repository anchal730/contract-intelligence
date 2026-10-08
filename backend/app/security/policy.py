from dataclasses import dataclass


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str


class SecurityPolicy:
    """
    Central security policy for contract processing.
    """

    ALLOW_EXTERNAL_LLM = False
    ALLOW_EXTERNAL_SHARING = False
    REQUIRE_HUMAN_APPROVAL = True

    @classmethod
    def check_document_processing(cls) -> PolicyDecision:
        return PolicyDecision(
            allowed=True,
            reason="Document processing is permitted",
        )

    @classmethod
    def check_external_llm(cls) -> PolicyDecision:
        if not cls.ALLOW_EXTERNAL_LLM:
            return PolicyDecision(
                allowed=False,
                reason="External LLM usage is disabled by policy",
            )

        return PolicyDecision(
            allowed=True,
            reason="External LLM usage is permitted",
        )

    @classmethod
    def check_external_sharing(cls) -> PolicyDecision:
        if not cls.ALLOW_EXTERNAL_SHARING:
            return PolicyDecision(
                allowed=False,
                reason="External document sharing is prohibited",
            )

        return PolicyDecision(
            allowed=True,
            reason="External sharing is permitted",
        )

    @classmethod
    def requires_human_approval(cls) -> bool:
        return cls.REQUIRE_HUMAN_APPROVAL
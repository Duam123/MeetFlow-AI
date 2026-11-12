
import re


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.
    Ignore case and extra whitespace.
    """

    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def validate_evidence(report: dict, transcript: str) -> list[str]:
    """
    Verify whether extracted evidence exists
    in the original meeting transcript.
    """

    normalized_transcript = normalize_text(transcript)

    issues = []

    evidence_sections = [
        "decisions",
        "action_items",
        "risks",
        "unresolved_questions"
    ]

    for section in evidence_sections:

        items = report.get(section, [])

        for index, item in enumerate(items):

            evidence = item.get("evidence")

            if not evidence:
                issues.append(
                    f"{section}[{index}]: Evidence is missing."
                )
                continue

            normalized_evidence = normalize_text(evidence)

            if normalized_evidence not in normalized_transcript:

                issues.append(
                    f"{section}[{index}]: "
                    f"Evidence does not match transcript: "
                    f"{evidence}"
                )

    return issues

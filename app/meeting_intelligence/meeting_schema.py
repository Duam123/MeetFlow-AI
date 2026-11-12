
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    content: str = Field(
        description="The extracted decision, risk, dependency, or question"
    )
    evidence: str = Field(
        description="Exact sentence from the meeting transcript supporting this information"
    )


class ActionItem(BaseModel):
    task: str = Field(description="Task that needs to be completed")

    owner: str | None = Field(
        default=None,
        description="Person responsible for the task"
    )

    deadline: str | None = Field(
        default=None,
        description="Deadline explicitly mentioned in the meeting"
    )

    dependencies: list[str] = Field(
        default_factory=list,
        description="Tasks that must be completed before this task"
    )

    evidence: str | None = Field(
        default=None,
        description="Exact sentence from the meeting transcript supporting this task"
    )

class MeetingSummary(BaseModel):
    meeting_title: str
    summary: str

    participants: list[str] = Field(default_factory=list)

    decisions: list[EvidenceItem] = Field(default_factory=list)

    action_items: list[ActionItem] = Field(default_factory=list)

    risks: list[EvidenceItem] = Field(default_factory=list)

    dependencies: list[EvidenceItem] = Field(default_factory=list)

    unresolved_questions: list[EvidenceItem] = Field(default_factory=list)

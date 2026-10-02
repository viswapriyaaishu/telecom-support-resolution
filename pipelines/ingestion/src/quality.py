from enum import StrEnum

from models import Conversation


class QualityStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"


class QualityIssue(StrEnum):
    MISSING_CONVERSATION_ID = "MISSING_CONVERSATION_ID"
    NO_TURNS = "NO_TURNS"
    INVALID_SPEAKER = "INVALID_SPEAKER"
    EMPTY_TEXT = "EMPTY_TEXT"
    INVALID_TIMESTAMP_ORDER = "INVALID_TIMESTAMP_ORDER"


VALID_SPEAKERS = {"agent", "client"}


def validate_conversation(
    conversation: Conversation,
) -> tuple[QualityStatus, list[QualityIssue]]:
    issues: list[QualityIssue] = []

    if not conversation.conversation_id.strip():
        issues.append(QualityIssue.MISSING_CONVERSATION_ID)

    if not conversation.turns:
        issues.append(QualityIssue.NO_TURNS)
        return QualityStatus.INVALID, issues

    for turn in conversation.turns:
        if turn.speaker.lower() not in VALID_SPEAKERS:
            issues.append(QualityIssue.INVALID_SPEAKER)

        if not turn.text.strip():
            issues.append(QualityIssue.EMPTY_TEXT)

    for previous, current in zip(
    conversation.turns,
    conversation.turns[1:],
    strict=False,
):
        if current.date_time < previous.date_time:
            issues.append(QualityIssue.INVALID_TIMESTAMP_ORDER)
            break

    if issues:
        return QualityStatus.INVALID, list(dict.fromkeys(issues))

    return QualityStatus.VALID, []
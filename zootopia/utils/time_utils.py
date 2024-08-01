from datetime import datetime, timedelta, timezone
from typing import List
from zootopia.core.logger import logger
import random


def get_current_time_readable() -> str:
    current_time = datetime.now()
    return current_time.strftime("%-I:%M%p %A, %b %-d, %Y")

def calculate_response_delay(messages: List[dict]) -> int:
    """Calculate delay in seconds of response based on various factors"""
    if len(messages) < 2:
        return 5  # Default delay if not enough messages

    # Calculate average time between messages
    time_diffs = []
    for i in range(1, len(messages)):
        try:
            time1 = datetime.fromisoformat(
                messages[i - 1]["created_at"].replace("Z", "+00:00")
            )
            time2 = datetime.fromisoformat(
                messages[i]["created_at"].replace("Z", "+00:00")
            )
            time_diff = (time1 - time2).total_seconds()
            time_diffs.append(time_diff)
        except (ValueError, KeyError) as e:
            logger.warning(f"Error parsing datetime: {e}")
            continue

    if not time_diffs:
        return 5  # Default delay if we couldn't calculate any time differences

    avg_time_between_messages = sum(time_diffs) / len(time_diffs)

    # Adjust delay based on message frequency
    if avg_time_between_messages < 5:
        return 10  # Longer delay for rapid messages
    elif avg_time_between_messages < 30:
        return 5
    else:
        return 3  # Quicker response for infrequent messages

def should_send_proactive_message(
    agent_proactivity: float,
    last_message_time: datetime,
    min_interval: timedelta = timedelta(minutes=30),
    max_interval: timedelta = timedelta(days=7),
) -> bool:
    """
    Determine if the agent should send a proactive message based on proactivity and time elapsed.

    Args:
    agent_proactivity - The agent's proactivity score (0 to 1).
    last_message_time - The timestamp of the last message in the room.
    min_interval - The minimum interval between messages.
    max_interval - The maximum interval between messages.

    Returns:
    bool: True if the agent should send a message, False otherwise.
    """
    current_time = datetime.now(timezone.utc)
    time_elapsed = current_time - last_message_time

    # Calculate how much of the total possible interval has elapsed
    interval_progress = (time_elapsed - min_interval) / (max_interval - min_interval)
    interval_progress = max(0, min(interval_progress, 1))  # Clamp between 0 and 1

    # Combine interval progress with agent proactivity
    send_probability = interval_progress * agent_proactivity

    return random.random() < send_probability

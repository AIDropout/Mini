from datetime import datetime, timedelta, timezone
from zootopia.core.schema import MessageTableModel
from zootopia.core.logger import logger
from typing import List
import random
import pytz


def get_current_time_cst_iso8601() -> str:
    central_tz = pytz.timezone("America/Chicago")
    current_time = datetime.now(central_tz)
    return current_time.strftime("%Y-%m-%d %H:%M:%S%z")


def get_current_time_readable() -> str:
    current_time = datetime.now()
    return current_time.strftime("%-I:%M%p %A, %b %-d, %Y")


def calculate_response_delay(messages: List[MessageTableModel]) -> int:
    """
    Calculate a human-like delay in seconds for message responses.

    :param messages: List of message objects, sorted by creation time (newest first)
    :return: Delay in seconds
    """
    if not messages:
        return random.randint(5, 15)  # Default delay if no messages

    try:
        last_message_time = datetime.fromisoformat(
            messages[0]["created_at"].replace("Z", "+00:00")
        )
        time_since_last_message = (datetime.now() - last_message_time).total_seconds()
    except (ValueError, KeyError):
        return random.randint(5, 15)  # Default delay if there's an error parsing time

    # Determine delay based on time since last message
    if time_since_last_message < 60:  # Within a minute
        return random.randint(5, 30)
    elif time_since_last_message < 300:  # Within 5 minutes
        return random.randint(30, 180)
    elif time_since_last_message < 3600:  # Within an hour
        return random.randint(3 * 60, 20 * 60)  # 3 to 20 minutes
    elif time_since_last_message < 86400:  # Within a day
        return random.randint(30 * 60, 4 * 60 * 60)  # 30 minutes to 4 hours
    else:  # More than a day
        return random.randint(4 * 60 * 60, 24 * 60 * 60)  # 4 to 24 hours


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

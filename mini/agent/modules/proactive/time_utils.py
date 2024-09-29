import random
from datetime import datetime, timedelta


def calculate_time_since(time: datetime) -> timedelta:
    """Calculate the time difference since the last message."""

    from config.container import container

    now = container.system_time_manager.get_user_datetime()
    return now - time


def format_time_diff(time_diff: timedelta) -> str:
    """Format the time difference for logging."""
    return f"{round(time_diff.total_seconds() / 60, 2)} minutes"


def get_safe_datetime_in_future(
    time_delta: timedelta,
    dead_start: int,
    dead_end: int,
    random_int: int,
) -> datetime:
    """
    Calculate a safe datetime in the future, avoiding the dead zone.

    Args:
        time_delta (timedelta): The time delta to calculate from the current time.
        dead_start (int): Start of the dead zone (hour in 24-hour format).
        dead_end (int): End of the dead zone (hour in 24-hour format).
        random_int (int): Max additional hours after dead_end for randomization.

    Returns:
        datetime: A datetime object either `time_delta` or adjusted based on the dead zone.
    """

    from config.container import container

    current_time = container.system_time_manager.get_user_datetime()
    future_time = current_time + time_delta

    future_hour = future_time.hour

    if dead_start <= future_hour or future_hour < dead_end:
        random_extra_hours = random.randint(0, random_int)
        random_extra_minutes = random.randint(0, 59)
        random_extra_seconds = random.randint(0, 59)
        adjusted_time = future_time.replace(
            hour=dead_end, minute=0, second=0, microsecond=0
        ) + timedelta(
            hours=random_extra_hours,
            minutes=random_extra_minutes,
            seconds=random_extra_seconds,
        )
        return adjusted_time

    return future_time

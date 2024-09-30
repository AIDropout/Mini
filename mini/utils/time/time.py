from datetime import datetime, timedelta

import pytz  # For timezone handling
import requests
from pydantic import BaseModel

from config.config import config
from mini.core.exceptions import (
    InvalidTimezoneError,
    TimeFetchError,
    TimeManagerError,
    TimezoneFetchError,
)


class TimeData(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    seconds: int
    milliSeconds: int
    dateTime: str
    date: str
    time: str
    timeZone: str
    dayOfWeek: str
    dstActive: bool


class TimeManager:
    """Handles time-related operations using external APIs, with caching for user-specific data."""

    def __init__(
        self, user_ip: str | None = None, user_timezone: str | None = None
    ) -> None:
        self.timeout = 10
        self.default_timezone = config.TIME_CONFIG.default_timezone
        self.api_url_timezone = config.TIME_CONFIG.url_from_timezone
        self.api_url_timezones = config.TIME_CONFIG.url_available_timezones
        self.api_url_ip = config.TIME_CONFIG.url_from_ip

        self.available_timezones = self.fetch_available_timezones()

        self.user_ip = user_ip
        self.user_timezone = user_timezone

        if user_timezone is not None and not self._is_available_timezone(user_timezone):
            raise InvalidTimezoneError(timezone=user_timezone)

    @property
    def ip(self):
        return self.user_ip

    @property
    def timezone(self):
        return self.user_timezone

    @staticmethod
    def timedelta_to_description(time_delta: timedelta) -> str:
        """Converts a time delta to a human-readable description. Example: '1 hour, 30 minutes'"""
        total_seconds = int(time_delta.total_seconds())
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

        return ", ".join(parts) if parts else "0 seconds"

    @staticmethod
    def datetime_to_timestamp(dt: datetime, timespec="milliseconds") -> str:
        """Converts a datetime object to an ISO 8601 formatted string."""
        if timespec == "milliseconds":
            iso_str = dt.isoformat(timespec="milliseconds")
            if dt.utcoffset() == timedelta(0):  # If UTC
                return iso_str.replace("+00:00", "Z")
            else:
                return iso_str
        else:
            raise ValueError("Invalid timespec value. Use 'milliseconds'.")

    def set_user_ip(self, ip_address: str) -> None:
        """Sets and caches the user's IP address and updates the user's timezone."""
        self.user_ip = ip_address
        self.user_timezone = self.fetch_timezone_from_ip(ip_address)

    def _is_available_timezone(self, timezone: str) -> bool:
        return (
            isinstance(self.available_timezones, list)
            and timezone in self.available_timezones
        )

    def set_user_timezone(self, timezone: str) -> None:
        """Sets and caches the user's timezone if it's valid."""
        if not self._is_available_timezone(timezone):
            raise InvalidTimezoneError(timezone=timezone)
        self.user_timezone = timezone

    def fetch_available_timezones(self) -> list:
        """Fetches the list of available timezones from the API."""
        try:
            response = requests.get(self.api_url_timezones, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise TimezoneFetchError(f"Error fetching timezones: {e}") from e

    def fetch_timezone_from_ip(self, ip_address: str) -> str:
        """Gets the timezone based on the provided IP address."""
        try:
            url = f"{self.api_url_ip}{ip_address}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            time_data = response.json()
            return time_data.get("timeZone", "Timezone data not available")
        except requests.exceptions.RequestException as e:
            raise TimezoneFetchError(f"Error fetching timezone: {e}") from e

    def fetch_current_time_data(self, timezone: str | None = None) -> TimeData:
        """Fetches the complete time data for the specified timezone or the cached user's timezone."""
        if timezone is not None and not self._is_available_timezone(timezone):
            raise InvalidTimezoneError(timezone=timezone)

        timezone = timezone or self.user_timezone or self.default_timezone

        try:
            url = f"{self.api_url_timezone}{timezone}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return TimeData(**response.json())
        except requests.exceptions.RequestException as e:
            raise TimeFetchError(f"Error fetching time data: {e}") from e

    def get_user_time_data(self) -> TimeData:
        """Gets the current time data for the cached user's IP or timezone."""
        if not self.user_timezone:
            raise TimeManagerError("User's timezone is not set.")
        return self.fetch_current_time_data(self.user_timezone)

    def get_user_datetime(self) -> datetime:
        """Returns the current user time as a timezone-aware datetime object."""
        if not self.user_timezone:
            raise TimeManagerError("User's timezone is not set.")

        time_data = self.get_user_time_data()
        tz = pytz.timezone(time_data.timeZone)

        return tz.localize(
            datetime(
                year=time_data.year,
                month=time_data.month,
                day=time_data.day,
                hour=time_data.hour,
                minute=time_data.minute,
                second=time_data.seconds,
                microsecond=time_data.milliSeconds
                * 1000,  # Convert milliseconds to microseconds
            )
        )

    def get_user_timestamp(self, timespec="milliseconds") -> str:
        """Returns the current user time as an ISO 8601 formatted string."""
        current_datetime = self.get_user_datetime()
        return self.datetime_to_timestamp(current_datetime, timespec)

    def current_readable_time(self) -> str:
        """Returns the current date and time as a readable string."""
        current_time_data = self.fetch_current_time_data()
        current_date = current_time_data.date
        current_time = current_time_data.time
        current_day_of_week = current_time_data.dayOfWeek
        timezone = current_time_data.timeZone

        readable_time = (
            f"Today is {current_day_of_week}, {current_date}. "
            f"The current time is {current_time} in {timezone}."
        )

        return readable_time

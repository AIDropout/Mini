import requests

from config.config import config
from zootopia.core.exceptions import (
    InvalidTimezoneError,
    TimeFetchError,
    TimeManagerError,
    TimezoneFetchError,
)


class TimeManager:
    """Handles time-related operations using external APIs, with caching for user-specific data."""

    def __init__(self) -> None:
        self.timeout = 10
        self.default_timezone = config.TIME_API.default_timezone
        self.api_url_timezone = config.TIME_API.url_from_timezone
        self.api_url_timezones = config.TIME_API.url_available_timezones
        self.api_url_ip = config.TIME_API.url_from_ip

        self.available_timezones = self.fetch_available_timezones()

        self.user_ip = None
        self.user_timezone = None

    def set_user_ip(self, ip_address: str) -> None:
        """Sets and caches the user's IP address."""
        self.user_ip = ip_address
        self.user_timezone = self.fetch_timezone_from_ip(ip_address)

    def _is_available_timezone(self, timezone: str) -> bool:
        return (
            isinstance(self.available_timezones, list)
            and timezone in self.available_timezones
        )

    def set_user_timezone(self, timezone: str) -> None:
        """Sets and caches the user's timezone if it's valid."""
        if self._is_available_timezone(timezone):
            self.user_timezone = timezone
        else:
            raise InvalidTimezoneError(f"'{timezone}' is not a valid timezone.")

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

    def fetch_current_time(self, timezone: str | None = None) -> str:
        """Gets the current time for the specified timezone or the cached user's timezone."""
        if timezone is not None and not self._is_available_timezone(timezone):
            raise InvalidTimezoneError(f"'{timezone}' is not a valid timezone.")

        timezone = timezone or self.user_timezone or self.default_timezone
        try:
            url = f"{self.api_url_timezone}{timezone}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            time_data = response.json()
            return time_data.get("date", "Time data not available")
        except requests.exceptions.RequestException as e:
            raise TimeFetchError(f"Error fetching time: {e}") from e

    def get_user_time(self) -> str:
        """Gets the current time for the cached user's IP or timezone."""
        if not self.user_timezone:
            raise TimeManagerError("User's timezone is not set.")
        return self.fetch_current_time(self.user_timezone)

from datetime import datetime
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError  # Import specific error
from oauth2client.client import OAuth2Credentials

from zootopia.tools.gsuite.gauth.gauth import GAuth
from zootopia.tools.gsuite.models import GAuthConfig, GCalError


class GCal:
    """Concrete class for Google Calendar operations using the Google Calendar API."""

    def __init__(self, credentials: OAuth2Credentials):
        """
        Initializes the GCal class with Google API credentials.
        """
        self.service = build("calendar", "v3", credentials=credentials)

    @classmethod
    def from_config(cls, config: GAuthConfig) -> "GCal":
        """Create a GCal instance from a GAuthConfig object."""
        gauth = GAuth.from_config(config)
        auth_url = gauth.get_auth_url()
        print(f"Please visit this URL to authorize the application: {auth_url}")
        auth_code = input("Enter the authorization code: ").strip()
        credentials = gauth.authenticate_with_code(auth_code)
        return cls(credentials)

    def create_calendar(self, title: str, description: str) -> str:
        """
        Creates a new calendar in Google Calendar.
        """
        body = {"summary": title, "description": description}
        try:
            response = (
                self.service.calendars()  # pylint: disable=E1101
                .insert(body=body)
                .execute()
            )
            return response["id"]
        except HttpError as e:
            raise GCalError(
                f"Error creating calendar: {e.resp.status} - {e.content}"
            ) from e
        except Exception as e:
            raise GCalError(f"An unexpected error occurred: {e}") from e

    def add_event(
        self,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        calendar_id: str = "primary",
        attachments: Optional[list[str]] = None,
    ) -> str:
        """
        Adds a new event to a specific calendar in Google Calendar.
        """
        if attachments:
            raise NotImplementedError(
                "Adding attachments to events is not currently supported."
            )

        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_time.isoformat()},
            "end": {"dateTime": end_time.isoformat()},
        }
        try:
            response = (
                self.service.events()  # pylint: disable=E1101
                .insert(calendarId=calendar_id, body=event)
                .execute()
            )
            return response["id"]
        except HttpError as e:
            raise GCalError(f"Error adding event: {e.resp.status} - {e.content}") from e
        except Exception as e:
            raise GCalError(f"An unexpected error occurred: {e}") from e

    def get_or_create_calendar(self, title: str, description: str) -> str:
        """
        Checks if a calendar with the desired title exists. If not, creates a new one.
        """
        for calendar in self._list_calendars():  # pylint: disable=E1101
            if calendar["summary"] == title:
                return calendar["id"]

        return self.create_calendar(title, description)

    def _calendar_exists(self, calendar_id: str) -> bool:
        """
        Checks if a calendar with the specified ID exists.
        """
        try:
            (
                self.service.calendars()  # pylint: disable=E1101
                .get(calendarId=calendar_id)
                .execute()
            )
            return True
        except HttpError as e:
            if "notFound" in str(e):
                return False
            else:
                raise GCalError(
                    f"Error checking calendar existence: {e.resp.status} - {e.content}"
                ) from e
        except Exception as e:
            raise GCalError(f"An unexpected error occurred: {e}") from e

    def _list_calendars(self):
        """
        Lists all calendars accessible to the authenticated user.

        :return: A list of calendar resources.
        """
        try:
            page_token = None
            calendars = []
            while True:
                calendar_list = (
                    self.service.calendarList()  # pylint: disable=E1101
                    .list(pageToken=page_token)
                    .execute()
                )
                calendars.extend(calendar_list["items"])
                page_token = calendar_list.get("nextPageToken")
                if not page_token:
                    break
            return calendars
        except HttpError as e:
            raise GCalError(
                f"Error listing calendars: {e.resp.status} - {e.content}"
            ) from e
        except Exception as e:
            raise GCalError(
                f"An unexpected error occurred while listing calendars: {e}"
            ) from e
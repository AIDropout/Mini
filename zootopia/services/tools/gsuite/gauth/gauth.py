from typing import List

from oauth2client.client import OOB_CALLBACK_URN, OAuth2Credentials, OAuth2WebServerFlow
from pydrive2.auth import GoogleAuth

from zootopia.tools.gsuite.models import GAuthConfig


class GAuth:
    def __init__(self, client_id: str, client_secret: str, scope: List[str]):
        """Initialize the GAuth object."""
        self.gauth = GoogleAuth()
        self.flow = self.setup_flow(client_id, client_secret, scope)
        self.access_token_expired = False

    @classmethod
    def from_config(cls, config: GAuthConfig) -> "GAuth":
        """Create a GAuth instance from a GAuthConfig object."""
        return cls(
            client_id=config.GOOGLE_CLIENT_ID,
            client_secret=config.GOOGLE_CLIENT_SECRET,
            scope=config.GOOGLE_AUTH_SCOPE,
        )

    def setup_flow(self, client_id: str, client_secret: str, scope: List[str]):
        """Set up the OAuth2WebServerFlow."""
        return OAuth2WebServerFlow(
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
            redirect_uri=OOB_CALLBACK_URN,
        )

    def get_auth_url(self) -> str:
        """Get the authentication URL for Google Drive."""
        try:
            return self.flow.step1_get_authorize_url()
        except Exception as e:  # pylint: disable=W0718
            if isinstance(e, (ValueError, AttributeError)):
                raise ValueError(
                    f"Invalid configuration or error generating URL: {str(e)}"
                ) from e
            else:
                raise RuntimeError(f"An unexpected error occurred: {str(e)}") from e

    def authenticate_with_code(self, auth_code: str) -> OAuth2Credentials:
        """Authenticate with Google using the provided authorization code."""
        try:
            credentials = self.flow.step2_exchange(auth_code)
            self.gauth.credentials = credentials
            return credentials
        except ValueError as ve:
            raise ValueError("The provided authorization code is invalid.") from ve

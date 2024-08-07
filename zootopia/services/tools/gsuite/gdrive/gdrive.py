from typing import Optional

from oauth2client.client import OAuth2Credentials
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from zootopia.tools.gsuite.gauth.gauth import GAuth
from zootopia.tools.gsuite.models import GAuthConfig


class GDrive:
    def __init__(self, credentials: OAuth2Credentials):
        """Initialize the GDrive object with OAuth2Credentials."""
        self.gauth = GoogleAuth()
        self.gauth.credentials = credentials
        self.drive = GoogleDrive(self.gauth)

    @classmethod
    def from_config(cls, config: GAuthConfig) -> "GDrive":
        """Create a GDrive instance from a GAuthConfig object."""
        gauth = GAuth.from_config(config)
        auth_url = gauth.get_auth_url()
        print(f"Please visit this URL to authorize the application: {auth_url}")
        auth_code = input("Enter the authorization code: ").strip()
        credentials = gauth.authenticate_with_code(auth_code)
        return cls(credentials)

    def create_folder(self, folder_name: str, parent_id: Optional[str] = "root") -> str:
        """
        Create a folder in Google Drive.
        """
        folder_metadata = {
            "title": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [{"id": parent_id}],
        }
        folder = self.drive.CreateFile(folder_metadata)
        folder.Upload()

        return folder["id"]

    def upload_file(self, file_name: str, file_path: str, folder_id: str) -> str:
        """
        Upload an file file to a specific folder in Google Drive.
        """
        file_metadata = {"parents": [{"id": folder_id}], "title": file_name}
        file = self.drive.CreateFile(file_metadata)
        file.SetContentFile(file_path)
        file.Upload()

        # Create a publicly accessible link
        file.InsertPermission({"type": "anyone", "value": "anyone", "role": "reader"})

        return file["embedLink"]

    def _folder_exists(
        self, folder_name: str, parent_id: str = "root"
    ) -> Optional[str]:
        """
        Check if a folder with the given name exists in the specified parent folder.
        """
        query = (
            f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' "
            f"and '{parent_id}' in parents and trashed=false"
        )
        file_list = self.drive.ListFile({"q": query}).GetList()

        if file_list:
            return file_list[0]["id"]
        return None

    def get_or_create_folder(self, folder_name: str, parent_id: str = "root") -> str:
        """
        Get the ID of an existing folder or create it if it doesn't exist.
        """
        folder_id = self._folder_exists(folder_name, parent_id)
        if folder_id is None:
            folder_id = self.create_folder(folder_name, parent_id)
        return folder_id

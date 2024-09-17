import os
from typing import Tuple
from mini.manager.messaging.bird import BirdManager
from mini.storage import S3FileStore
import uuid

"""
pipeline:
First, make .vcf file in vcf folder
Second, run this file which does the folllowing: 
- upload to s3
- get a url of the file
- stores the url for the agent into supabase
"""

def upload_file(file_path: str) -> Tuple[str, str]:
    """Upload file to S3 and return the URL and content type."""
    fs = S3FileStore()
    with open(file_path, 'rb') as file:
        file_content = file.read()
    
    # Generate a unique file name
    file_name = f"{uuid.uuid4()}_{os.path.basename(file_path)}"
    s3_file_prefix = f"vcf_files/{file_name}"
    content_type = "text/vcard"
    fs.write(s3_file_prefix, file_content, content_type)
    
    return fs.generate_presigned_url(s3_file_prefix, content_type), content_type

    # Update row in Supabase
    # def update_user(self, user_id: str, update_data: Dict[str, Any]) -> User:
    # existing_user = self.database_manager.get_row(
    #     Tables.USERS, {Tables.USERS__id: user_id}
    # )
    # if not existing_user:
    #     raise HTTPException(status_code=404, detail="User not found")

    # update_data = {k: v for k, v in update_data.items() if v is not None}

    # updated_user = self.database_manager.update(
    #     table_name=Tables.USERS,
    #     update_data=update_data,
    #     condition_key=Tables.USERS__id,
    #     condition_value=user_id,
    # )
    # if not updated_user:
    #     raise HTTPException(status_code=400, detail="Failed to update user")
    # return updated_user


def send_vcf_file(phone_number: str, channel_id: str, vcf_file_path: str) -> Tuple[bool, dict]:
    # Initialize BirdManager
    bird_manager = BirdManager()

    # Set receiver and sender
    bird_manager.set_receiver(phone_number)
    bird_manager.set_sender(channel_id)

    # Check if file exists
    if not os.path.exists(vcf_file_path):
        raise FileNotFoundError(f"The file {vcf_file_path} does not exist.")

    # Upload file and get URL
    file_url, content_type = upload_file(vcf_file_path)

    # Prepare the file information
    files = [(file_url, content_type)]

    # Send the message with the .vcf file
    success, details = bird_manager.send_message(
        text="Here's the contact information you requested.",
        files=files
    )

    return success, details

if __name__ == "__main__":
    # Example usage
    phone_number = "+13142952259"
    channel_id = "946f4f9d-21c0-495e-b59d-5f3704deb11b"
    vcf_file_path = "scripts/vcf/samasher.vcf"  # This is relative to the current working directory

    try:
        success, details = send_vcf_file(phone_number, channel_id, vcf_file_path)
        if success:
            print("VCF file sent successfully!")
            print(f"Details: {details}")
        else:
            print("Failed to send VCF file.")
            print(f"Error details: {details}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
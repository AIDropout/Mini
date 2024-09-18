from mini.core.logger import get_logger
from mini.core.schema.tables import Agent
from mini.storage import S3FileStore
from mini.utils.utils import encode_image_url_to_base64

logger = get_logger(__name__)


def get_or_create_contact_card(agent: Agent, agent_phone_number: str) -> str:
    """Returns url of contact card"""

    fs = S3FileStore()
    file_path = f"vcf_files/{agent.id}.vcf"

    try:
        # Try to read the existing file
        existing_content = fs.read(file_path)
        # If the file exists, return its URL
        return fs.generate_presigned_url(file_path, "text/vcard")
    except Exception:
        # If the file doesn't exist or there's an error reading it, create a new one
        name_parts = agent.name.split(maxsplit=1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        base64_image = encode_image_url_to_base64(agent.image_url)

        vcf_content = f"""BEGIN:VCARD
VERSION:4.0
N:{last_name};{first_name};;;
FN:{agent.name}
ORG:{"mini"}
PHOTO;ENCODING=BASE64;TYPE=JPEG:{base64_image}
TEL;TYPE=CELL:{agent_phone_number}
END:VCARD
"""
        logger.info(f".vcf file content: {vcf_content}")

        # Upload the new file
        fs.write(file_path, vcf_content.encode("utf-8"), "text/vcard")

        # Generate and return the URL for the newly created file
        return fs.generate_presigned_url(file_path, "text/vcard")

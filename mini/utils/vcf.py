from mini.core.logger import get_logger
from mini.core.schema.tables import Agent
from mini.storage import S3FileStore
from mini.utils.utils import encode_image_url_to_base64

logger = get_logger(__name__)

def get_or_create_contact_card(agent: Agent, agent_phone_number: str) -> str:
    """Returns url of contact card"""

    fs = S3FileStore()
    file_path = f"vcf_files/{agent.id}.vcf"

    # Create the new VCF content
    name_parts = agent.name.split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    base64_image = encode_image_url_to_base64(agent.image_url)

    new_vcf_content = f"""BEGIN:VCARD
VERSION:4.0
N:{last_name};{first_name};;;
FN:{agent.name}
ORG:{"mini"}
PHOTO;ENCODING=BASE64;TYPE=JPEG:{base64_image}
TEL;TYPE=CELL:{agent_phone_number}
URL:{"https://textmini.com"}
END:VCARD
"""

    try:
        # Try to read the existing file
        existing_content = fs.read(file_path)
        
        # Compare existing content with new content
        if existing_content.decode("utf-8") != new_vcf_content:
            logger.info("Existing VCF doesn't match the new one. Replacing...")
            fs.write(file_path, new_vcf_content.encode("utf-8"), "text/vcard")
        else:
            logger.info("Existing VCF matches the new one. No update needed.")
    except Exception as e:
        logger.info(f"Error reading existing file or file doesn't exist: {str(e)}")
        logger.info("Creating new VCF file...")
        fs.write(file_path, new_vcf_content.encode("utf-8"), "text/vcard")

    # Generate and return the URL for the file
    return fs.generate_presigned_url(file_path, "text/vcard")
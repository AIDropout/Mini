from typing import List, Dict, Any

from fastapi import HTTPException

from config.config import config
from mini.core.logger import get_logger
from mini.database.models import Agent, Tables
from mini.database.database import DatabaseManager

logger = get_logger(__name__)


class AgentTableService:
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager

    def get_agent(self, agent_id) -> Agent:
        """
        Get agent by id
        """
        agent = self.database_manager.get_row(
            Tables.AGENTS,
            conditions={Tables.AGENTS__id: agent_id},
        )
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return agent

    def get_agents(self) -> List[Agent]:
        """
        Get all agents (for website)
        """
        agents = self.database_manager.get_multiple_rows(
            Tables.AGENTS,
            order_by="id",
            max_rows=100,
        )
        if not agents:
            raise HTTPException(status_code=404, detail="Agents not found")

        return agents

    def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> Agent:
        existing_agent = self.database_manager.get_row(
            Tables.AGENTS, {Tables.AGENTS__id: agent_id}
        )
        if not existing_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        update_data = {k: v for k, v in update_data.items() if v is not None}

        updated_agent = self.database_manager.update(
            table_name=Tables.AGENTS,
            update_data=update_data,
            condition_key=Tables.AGENTS__id,
            condition_value=agent_id,
        )
        if not updated_agent:
            raise HTTPException(status_code=400, detail="Failed to update agent")
        return updated_agent

    def get_or_create_contact_card(self, agent_id: str) -> str:
        """
        Retrieves or creates a contact card (VCF file) for a given agent and returns its URL.
        Fetches agent details, phone number, and Instagram handle from the database, generates VCF content,
        and stores it in S3 if it doesn't exist or has changed. Raises ValueError if
        agent or channel is not found in the database.
        """
        from mini.utils.storage import S3FileStore
        from mini.utils.utils import encode_image_url_to_base64
        import re

        fs = S3FileStore()

        # Fetch the agent data
        agent = self.get_agent(agent_id)

        # Create a URL-safe filename from the agent's name
        safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", agent.name.lower())
        file_path = f"vcf_files/{safe_name}.vcf"

        # Fetch the agent's phone number
        channel = self.database_manager.get_row(
            Tables.CHANNELS,
            {Tables.CHANNELS__id: agent.bird_channel_id},
        )

        if not channel:
            raise ValueError(f"Channel for agent {agent_id} not found")

        ig_account = self.database_manager.get_row(
            Tables.IGACCOUNTS, {Tables.IGACCOUNTS__agent_id: agent_id}
        )

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
TEL;TYPE=CELL:{channel.phone_number}
URL:{"https://textmini.com"}
"""

        # Add Instagram link if ig_account exists and has a handle
        if ig_account and ig_account.handle:
            new_vcf_content += (
                f"X-SOCIALPROFILE;TYPE=instagram:https://ig.me/m/{ig_account.handle}\n"
            )

        new_vcf_content += "END:VCARD\n"

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


if __name__ == "__main__":
    from config.container import container

    service = container.agent_table_service
    agent_id = "f49c9af0-929b-4fe1-9522-6fe4a325bdf5"
    url = service.get_or_create_contact_card(agent_id)
    logger.info(url)

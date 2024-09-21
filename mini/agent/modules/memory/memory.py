import os
import pprint
from datetime import datetime, timedelta
from time import sleep
from typing import List, Optional

from mem0 import Memory
from pydantic import ValidationError

from config.config import config
from mini.core.exceptions import (
    MemoryAdditionError,
    MissingAgentIdError,
    MissingUserIdError,
)
from mini.core.logger import get_logger
from mini.agent.modules.memory.models import (
    MemoryMetadataSchema,
    MemoryRecordSchema,
    RetrievedMemoryMetadataSchema,
    SavedMemoryMetadataSchema,
)
from mini.llm import LLMService
from mini.utils.time import TimeManager

from .prompts import GENERATE_QUERY_PROMPT, METADATA_PROMPT

logger = get_logger(__name__)


class MemoryManager:
    """Class that implements Memory powered by Mem0 AI"""

    def __init__(
        self,
        llm_manager: LLMService,
        time_manager: TimeManager,
        memory_save_delay: int = 5,
        user_id: Optional[int] = None,
        agent_id: Optional[int] = None,
    ) -> None:
        mem0_config = {
            "vector_store": {
                "provider": config.MEMORY_VECTOR_STORE_PROVIDER,
                "config": config.MEMORY_QDRANT_CONFIG.model_dump(),
            },
            "llm": {
                "provider": config.MEMORY_LLM_PROVIDER,
                "config": config.MEMORY_LITELLM_CONFIG.model_dump(),
            },
            "embedder": {
                "provider": config.MEMORY_EMBEDDINGS_PROVIDER,
                "config": config.MEMORY_EMBEDDINGS_CONFIG.model_dump(),
            },
        }

        # because of mem0 being dumb, we have save this api key specifcially
        # made a pr to mem0: https://github.com/mem0ai/mem0/pull/1747
        os.environ["GEMINI_API_KEY"] = config.MEMORY_LITELLM_CONFIG.api_key

        self.time_manager = time_manager
        self.llm_manager = llm_manager

        self.memory_save_delay = memory_save_delay  # delay for rate limits

        self.mem = Memory.from_config(mem0_config)
        self.user_id = user_id
        self.agent_id = agent_id

    def set_user_id(self, user_id: str) -> None:
        """Sets the user_id."""
        self.user_id = user_id

    def set_agent_id(self, agent_id: str) -> None:
        """Sets the agent_id."""
        self.agent_id = agent_id

    def _check_user_and_agent_ids(self) -> None:
        """Checks if user_id and agent_id are set, raises exceptions if not."""
        if self.user_id is None:
            raise MissingUserIdError("User ID is not set for this memory manager.")
        if self.agent_id is None:
            raise MissingAgentIdError("Agent ID is not set for this memory manager.")

    def _extract_metadata(self, data: str) -> List[SavedMemoryMetadataSchema]:
        """Splits input data into separate messages by topics using LLM and extracts metadata."""
        current_time_data = self.time_manager.fetch_current_time_data()
        system_prompt = METADATA_PROMPT.format(
            current_date=current_time_data.date,
            current_time=current_time_data.time,
            current_day_of_week=current_time_data.dayOfWeek,
            timezone=current_time_data.timeZone,
        )
        response: dict = self.llm_manager.generate_response(
            messages=[{"role": "user", "content": data}],
            system_prompt=system_prompt,
            json_mode=True,
            # expect_json=True,
        )

        try:
            metadata = MemoryMetadataSchema(**response)
        except ValidationError as e:
            logger.error("Failed to validate metadata response: %s", e)
            return []

        segments = metadata.segments

        _truncated_data = data[:100] + "..." if len(data) > 100 else data
        if len(segments) == 0:
            logger.warning(
                "No segments extracted for memory from data: ('%s').", _truncated_data
            )
        else:
            logger.info(
                "Extracted %s segments for memory from data: ('%s').",
                len(segments),
                _truncated_data,
            )

        return segments

    def add_memory(self, data: str, limit: int = 10):
        """Adds extracted messages as memories for the user."""
        self._check_user_and_agent_ids()  # Check if IDs are set
        segments = self._extract_metadata(data)

        if limit > len(segments):
            segments = segments[:limit]

        for i, segment in enumerate(segments):
            logger.info("Saving memory #%s/%s", i + 1, len(segments))
            sleep(self.memory_save_delay)
            # TODO: test no parse?
            res = self.mem.add(
                messages=segment.text,
                agent_id=self.agent_id,
                metadata={
                    "user_id": self.user_id,
                    "relevance": segment.relevance,
                    "date": segment.date,
                    "owner": segment.owner,
                },
            )

            if res["message"] != "ok":
                raise MemoryAdditionError(
                    f"Failed to add memory for user {self.user_id} with message: {segment.text}"
                )

        joined_segments = "\n".join(str(segment) for segment in segments)
        logger.info(
            "%s memories saved successfully:\n%s.", len(segments), joined_segments
        )

    def _extract_retrieval_metadata(
        self, conversation_str: str
    ) -> RetrievedMemoryMetadataSchema:
        current_time_data = self.time_manager.fetch_current_time_data()
        system_prompt = GENERATE_QUERY_PROMPT.format(
            current_date=current_time_data.date,
            current_time=current_time_data.time,
            current_day_of_week=current_time_data.dayOfWeek,
            timezone=current_time_data.timeZone,
        )

        response: dict = self.llm_manager.generate_response(
            messages=[{"role": "user", "content": conversation_str}],
            system_prompt=system_prompt,
            json_mode=True,
            # expect_json=True,
        )

        try:
            metadata = RetrievedMemoryMetadataSchema(**response)
        except ValidationError as e:
            logger.error("Failed to validate metadata response: %s", e)
            return []

        logger.info("Query memory using metadata: %s", metadata.model_dump_json())

        return metadata

    def get_memory(
        self, conversation_str: str, limit_to_one: bool = False
    ) -> List[MemoryRecordSchema]:
        self._check_user_and_agent_ids()  # Check if IDs are set
        metadata = self._extract_retrieval_metadata(conversation_str)

        if limit_to_one:
            return self.query_memory(query=metadata.query, limit=1)

        default_query = "information"

        relevance = metadata.relevance
        dates = metadata.date
        query = metadata.query or default_query

        memories = []
        memories.extend(self.query_memory(query=query))

        for val in relevance:
            memories.extend(self.query_memory(query, filters={"relevance": val}))

        for date in dates:
            memories.extend(self.query_memory(default_query, filters={"date": date}))

        logger.info("Retrived %s relevant memories.", len(memories))

        return memories

    def query_memory(
        self, query: str, filters: dict | None = None, limit: int = 25
    ) -> List[MemoryRecordSchema]:
        """Searches for memory using mem0"""
        self._check_user_and_agent_ids()  # Check if IDs are set

        if filters is None:
            filters = {}

        filters["user_id"] = self.user_id

        res = self.mem.search(
            query=query,
            agent_id=self.agent_id,
            filters=filters,
            limit=limit,
        )

        memories = [MemoryRecordSchema(**memory) for memory in res]
        return memories

    def cleanup_memories(self):
        raise NotImplementedError("needs more testing before usage")
        self._check_user_and_agent_ids()  # Check if IDs are set
        all_memories = self.mem.get_all(user_id=self.user_id, agent_id=self.agent_id)

        # Get the current date and time
        now: datetime = self.time_manager.get_user_datetime()

        def parse_date(date_str: Optional[str]) -> Optional[datetime]:
            """Helper function to parse date string or return None."""
            if date_str:
                return datetime.fromisoformat(date_str)
            return None

        def should_delete(memory: dict) -> bool:
            """Determine if a memory should be deleted based on its relevance and age."""
            date_str = memory["metadata"].get("date")
            memory_date = parse_date(date_str)
            updated_at = parse_date(memory.get("updated_at"))

            if not memory_date:
                # If no date is provided, use updated_at
                memory_date = updated_at

            age = now - memory_date

            relevance = memory["metadata"]["relevance"]
            if relevance == "SHORT_TERM" and age > timedelta(weeks=1):
                return True
            if relevance == "MEDIUM_TERM" and age > timedelta(weeks=4):
                return True
            if relevance == "LONG_TERM" and age > timedelta(weeks=26):
                return True
            if relevance == "LIFETIME" and age > timedelta(weeks=104):
                return True

            return False

        # Filter memories to delete
        memories_to_delete = [
            memory for memory in all_memories if should_delete(memory)
        ]

        print(f"Found {len(memories_to_delete)} memories to delete.")
        pprint.pprint(memories_to_delete)

        # Delete the memories
        for memory in memories_to_delete:
            memory_id = memory["id"]
            self.mem.delete(memory_id=memory_id)
            logger.info("Deleted memory with ID: %s", memory_id)

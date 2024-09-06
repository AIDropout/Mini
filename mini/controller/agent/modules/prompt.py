from config.config import (
    PromptAboutConfig,
    PromptMetadataConfig,
    PromptModuleConfig,
    PromptPersonalityConfig,
    PromptRulesConfig,
)
from mini.controller.agent.modules.base import AgentModule
from mini.core.schema.tables import Tables
from mini.manager.database import DatabaseManager
from mini.manager.time import TimeManager


class PromptModule(AgentModule):
    def __init__(
        self,
        config: PromptModuleConfig,
        # TODO: need a overall context manager?
        database_manager: DatabaseManager,
        time_manager: TimeManager,
    ) -> None:
        super().__init__(database_manager)
        self.rules: PromptRulesConfig = config.rules
        self.about: PromptAboutConfig = config.about
        self.personality: PromptPersonalityConfig = config.personality
        self.metadata: PromptMetadataConfig = config.metadata

        self.base_prompt: str = config.base_prompt

        self.time_manager = time_manager

        self.database_manager = database_manager

        self.count_messages = self.database_manager.count_rows(
            table_name=Tables.MESSAGES
        )
        self.days_since_last_seen = 2
        self.is_subscribed = False

        # TODO: fix bug in subscription table
        # (
        #     self.database_manager.get_row(
        #         Tables.SUBSCRIPTIONS,
        #         {
        #             Tables.SUBSCRIPTIONS__user_id: self.user.id,
        #             Tables.SUBSCRIPTIONS__status: SubscriptionStatus.ACTIVE,
        #         },
        #     )
        #     is not None
        # )

    def build_rules(self) -> str:
        rules = "**Messaging:**\n"

        if self.count_messages <= self.rules.initial_message_count:
            rules += f"- {self.rules.initial_message_prompt}\n"

        if self.days_since_last_seen >= self.rules.last_conversation_days_threshold:
            rules += f"- {self.rules.last_conversation_prompt}\n"

        if self.is_subscribed:
            rules += f"- {self.rules.pre_subscription_prompt}\n"
        else:
            rules += f"- {self.rules.post_subscription_prompt}\n"

        if self.rules.style_guidelines:
            rules += "\n\n**Style Guidelines:**\n"
            for key, value in self.rules.style_guidelines.items():
                if isinstance(value, list):
                    for item in value:
                        rules += f"- {key}: {item}\n"
                else:
                    rules += f"- {key}: {value}\n"
            rules += "\n"
        return rules

    def _get_personality_description(self, level: int) -> str | None:
        """Convert percentage level to descriptive adjective with more granularity."""
        if level >= 95:
            return "exceptionally"
        elif level >= 85:
            return "extremely"
        elif level >= 70:
            return "very"
        elif level >= 50:
            return "moderately"
        elif level >= 35:
            return "somewhat"
        elif level >= 20:
            return "slightly"
        else:
            return None

    def build_personality(self) -> str:
        descriptions = {
            "Shy": self._get_personality_description(self.personality.shy_level),
            "Confident": self._get_personality_description(
                self.personality.confidence_level
            ),
            "Assertive": self._get_personality_description(
                self.personality.assertiveness_level
            ),
            "Friendly": self._get_personality_description(
                self.personality.friendliness_level
            ),
            "Flirty": self._get_personality_description(
                self.personality.flirtiness_level
            ),
            "Funny": self._get_personality_description(self.personality.humor_level),
        }

        filtered_descriptions = {
            trait: desc for trait, desc in descriptions.items() if desc is not None
        }

        overview = "**Personality Overview:**\n"
        for trait, description in filtered_descriptions.items():
            overview += f"- {trait}: You are {description} {trait.lower()}.\n"

        return overview

    def build_about(self) -> str:
        return (
            f"**About You:**\n"
            f"- Timezone: {self.about.timezone}\n"
            f"- Interests: {', '.join(self.about.interests)}\n"
            f"- Past Events: {', '.join(self.about.past_events)}\n"
        )

    def build_metadata(self, relevant_memories: str | None = None) -> str:
        metadata = "**Metadata Details:**\n"

        if self.metadata.display_timestamp:
            metadata += f"- Time: {self.time_manager.current_readable_time()}\n"

        if relevant_memories:
            metadata += f"- Relevant Memories: {relevant_memories}\n"

        return metadata

    def build_prompt(self, relevant_memories: str) -> str:
        prompt = [
            self.base_prompt,
            self.build_rules(),
            self.build_personality(),
            self.build_about(),
            self.build_metadata(relevant_memories=relevant_memories),
        ]

        return "\n\n".join(prompt)

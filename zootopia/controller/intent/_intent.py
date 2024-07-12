from typing import List
from zootopia.controller.intent.models import (
    Confidence,
    IntentConfig,
    IntentFilters,
    LLMResponseStructure,
)
from archive.langchain import LLM
from zootopia.core.utils.utils import clean_and_parse_llm_json_output, render_jinja_template
from zootopia.core.schema import Action, MessageTableModel


class IntentManager:
    """Detect the intent of a given text data."""

    def __init__(self, llm: LLM, filters: List[IntentFilters]):
        """Initialize the IntentManager."""
        filters_str = ", ".join(
            f"{value.title.upper()} ({value.description})" for value in filters
        )
        system_prompt = render_jinja_template(
            "intent.jinja",
            "zootopia/intent/templates",
            filters=filters_str,
            response_structure=LLMResponseStructure,
        )
        llm.system_prompt = system_prompt
        self.llm = llm

    @classmethod
    def from_config(cls, config: IntentConfig) -> "IntentManager":
        """Create an IntentManager instance from a configuration."""
        llm = LLM.from_config(config.llm_config)
        return cls(llm=llm, filters=config.filters)

    # Paradigm 1 - produce intents. For custom flows
    def detect_intent(
        self,
        data: str,
        detect_single: bool = False,
        confidence_threshold: Confidence = Confidence.LOW,
    ) -> List[str]:
        """
        Detects the intent of the given text data and returns a list of intents that 
        pass the confidence threshold.
        """
        content = self.llm.generate_response(data).content
        cleaned = clean_and_parse_llm_json_output(content)

        if "error" in cleaned:
            raise ValueError(cleaned["error"])

        def filter_intents(conf_level):
            return [
                intent
                for intent, conf in cleaned["intent"].items()
                if Confidence(conf) == conf_level
            ]

        confidence_levels = {
            Confidence.HIGH: filter_intents(Confidence.HIGH),
            Confidence.MID: filter_intents(Confidence.MID),
            Confidence.LOW: filter_intents(Confidence.LOW),
        }

        result = []
        for level in Confidence:
            if level >= confidence_threshold:
                result.extend(confidence_levels[level])

        if detect_single and result:
            return [result[0]]

        return result
    
    # Paradigm 2 - produce actions. For agent autonomy
    def produce_actions(self, message_history: List[MessageTableModel], possible_actions: List[str]) -> List[Action]:
        prompt = self._prepare_prompt(message_history, possible_actions)
        
        response = self.llm.generate_response(prompt)
        
        return self._parse_llm_response(response)

    def _prepare_prompt(self, message_history: List[MessageTableModel], possible_actions: List[str]) -> str:
        print("Preparing prompt...")
        print(message_history)
        print(possible_actions)
        
        # Implement the logic to create a prompt for the LLM
        # Include the message history and possible actions
        pass

    def _parse_llm_response(self, response: str) -> List[Action]:
        # Implement the logic to parse the LLM's response into a list of Action objects
        pass
        
        
        

"""
# 1. Intent Detector - Given most recent msg + past 10 messages + a list of possible Actions,
What is your next thought or action? Your response must be in JSON format.
It must be an object, and it must contain two fields:
* 'action', which is one of the actions below
* 'args', which is a map of key-value pairs, specifying the arguments for that action
ex.
* 'add_gcal_event*
* 'schedule_reminder"
* 'respond - respond, or get more information. Arguments:
* 'content'
* 'no_response'
| * 'reasoning - reason ex. attempting to jailbreak, etc etc
- Add result of action to ActionsTaken for chaining actions
- Respond or no_response terminates the chain
(* Potentially add intent detector for Respond Action? (e.g. "deep vs shallow convos")
3. Action Manager - Parses list of Actions, and executes. Returns list of ActionResults
Memory Manager - update memory. Ideally it's given ActionResults, but let's keep it simple & decoupled from the first 2 for now and just update db with message
"""
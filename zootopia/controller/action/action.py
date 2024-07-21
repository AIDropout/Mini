from typing import List, Dict
from zootopia.core.schema import Action, ActionType, ActionResult
from zootopia.core.logger import logger
from zootopia.llm.llm import LLM 
from zootopia.core.utils.utils import render_jinja_template
from config.config import ActionManagerConfig
from zootopia.platform.platform import MessageProviderBase

class ActionManager:
    def __init__(self, model_name: str, messaging_service: MessageProviderBase, agent_prompt: str) -> None:
        self.llm = LLM(model_name)
        self.messaging_service = messaging_service
        self.agent_prompt = agent_prompt
    
    @classmethod
    def from_config(cls, manager_config: ActionManagerConfig, messaging_service: MessageProviderBase, agent_prompt: str) -> "ActionManager":
        model_name = manager_config.LLM_NAME
        return cls(
            model_name, messaging_service, agent_prompt
        )

    async def respond_to_user(self, recent_messages: List[Dict[str, str]]):
        system_prompt = render_jinja_template(
            "system_prompt.jinja",
            "zootopia/controller/action/templates",
            system_prompt=self.agent_prompt
        )
        
        # Create the messages list with the system prompt at the beginning
        messages = [
            {"role": "system", "content": system_prompt}
        ] + recent_messages

        # Define message_action with a default content
        message_action = Action(type=ActionType.MESSAGE, args={"content": ""})

        try:
            content = self.llm.generate_response(messages)
            await self.messaging_service.send_message(content)
            message_action = Action(type=ActionType.MESSAGE, args={"content": content})
            return ActionResult(action=message_action, success=True, result=content)
        except Exception as e:
            logger.error(f"Error executing respond action: {str(e)}")
            return ActionResult(action=message_action, success=False, result=f"Agent response failed to generate or send: {str(e)}")

    async def execute_actions(self, actions: List[Action], recent_messages: List[Dict[str, str]]) -> List[ActionResult]:
        results = []
        for action in actions:
            try:
                result = await self._execute_single_action(action)
                results.append(result)
            except Exception as e:
                logger.error(f"Error executing action {action.type}: {str(e)}")
                results.append(ActionResult(action=action, success=False, result=str(e)))

        # Always respond
        response_result = await self.respond_to_user(recent_messages)
        results.append(response_result)
        return results, response_result.result

    async def _execute_single_action(self, action: Action) -> ActionResult:
        if action.type == ActionType.RECALL:
            print(f"Recalling from memory: {action.args.get('query', '')}")
            # TODO: Implement actual memory recall logic
            return ActionResult(action=action, success=True, result="Memory recalled")

        elif action.type == ActionType.WEB_SEARCH:
            print(f"Performing web search: {action.args.get('query', '')}")
            # TODO: Implement actual web search logic
            return ActionResult(action=action, success=True, result="Web search performed")

        elif action.type == ActionType.NO_RESPONSE:
            print("No response needed")
            return ActionResult(action=action, success=True, result="No response")

        elif action.type == ActionType.FLAG_USER:
            print(f"Flagging user: {action.args.get('reason', '')}")
            # TODO: Implement actual user flagging logic
            return ActionResult(action=action, success=True, result="User flagged")

        elif action.type == ActionType.UPLOAD_GDRIVE_FILE:
            print(f"Uploading file to Google Drive: {action.args.get('file_path', '')}")
            # TODO: Implement actual Google Drive upload logic
            return ActionResult(action=action, success=True, result="File uploaded to Google Drive")

        elif action.type == ActionType.ADD_GCAL_EVENT:
            print(f"Adding event to Google Calendar: {action.args.get('event_details', '')}")
            # TODO: Implement actual Google Calendar event addition logic
            return ActionResult(action=action, success=True, result="Event added to Google Calendar")

        elif action.type == ActionType.SCHEDULE:
            print(f"Scheduling action: {action.args}")
            # TODO: Implement actual scheduling logic
            return ActionResult(action=action, success=True, result="Action scheduled")

        elif action.type == ActionType.NULL:
            print("Null action, doing nothing")
            return ActionResult(action=action, success=True, result="Null action executed")

        else:
            error_message = f"Unknown action type: {action.type}"
            logger.error(error_message)
            return ActionResult(action=action, success=False, result=error_message)
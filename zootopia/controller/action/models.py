from typing import List, Optional, Union

from pydantic import BaseModel, Field


class FunctionCall(BaseModel):
    name: str
    location: str
    input_description: Optional[str]
    output_description: Optional[str]


class Action(BaseModel):
    intent_name: str = Field(
        description="Short name of the intent that triggers this action",
    )
    intent_description: str = Field(
        description="A detailed description of the intent",
    )
    action: Union[FunctionCall, "ActionChain"] = Field(
        description="A FunctionCall or an ActionChain"
    )


class ActionChain(BaseModel):
    action_chain: List[Action] = Field(
        description="List of Action objects forming the action chain",
    )


Action.model_rebuild()


class ActionsConfig(BaseModel):
    action_chain: ActionChain


class ActionPlan(BaseModel):
    action_plan: List[FunctionCall] = Field(
        description="A list of functions to run",
    )

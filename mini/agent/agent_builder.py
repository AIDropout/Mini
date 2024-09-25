from config.container import container
from config.config import Config
from mini.agent.agent import AgentService
from mini.core.models.context import Context
from mini.agent.agent import AgentService
from mini.agent.modules.sender import MessageSenderModule
from mini.agent.modules.filter.filter import IntentConfig, MessageFilterModule
from mini.agent.modules.memory.service import MemoryModule
from mini.agent.modules.prompt import (
    AgentPromptModule,
    BasePromptModule,
    RoleplayPromptModule,
)
from mini.agent.modules.vision import VisionModule
from mini.core.enums import ConfidenceLevel
from mini.llm import LLMService, Model
from mini.agent.modules.memory import MemoryManager
from mini.agent.modules.proactive import ScheduleDispatch
from mini.server.schedule.scheduler import Scheduler

database_manager = container.database_manager
time_manager = container.time_manager
apscheduler = container.get_apscheduler()


# TODO: Change all modules to not accept context. Instead, use the context property held by a task. And for each module function, simply accept a task object.
def build_agent(config: Config, context: Context) -> AgentService:

    return AgentService(
        database_manager=database_manager,
        schedule_dispatch=ScheduleDispatch(
            database_manager=database_manager,
            context=context,
            scheduler=Scheduler(apscheduler),
        ),
        message_sender_module=MessageSenderModule(
            database_manager=database_manager,
            context=context,
            llm_manager=LLMService(
                model=Model.from_model_name(config.ACTION_MANAGER_LLM)
            ),
        ),
        memory_module=MemoryModule(
            database_manager=database_manager,
            context=context,
            memory_manager=MemoryManager(
                user_id=None,
                agent_id=None,
                time_manager=time_manager,
                llm_manager=LLMService(
                    model=Model.from_model_name(config.MEMORY_GENERAL_LLM)
                ),
                memory_save_delay=5,
            ),
        ),
        filter_module=MessageFilterModule.from_config(
            database_manager=database_manager,
            context=context,
            config=IntentConfig(
                message_input_count=5,
                confidence_threshold=ConfidenceLevel.HIGH,
                is_enabled=True,
            ),
            llm_service=LLMService(
                model=Model.from_model_name(config.ACTION_MANAGER_LLM)
            ),
        ),
        vision_module=VisionModule(
            database_manager=database_manager,
            context=context,
            llm_manager=LLMService(
                model=Model.from_model_name(config.VISION_MANAGER_LLM)
            ),
        ),
        prompt_module=BasePromptModule(
            database_manager=database_manager,
            context=context,
            time_manager=time_manager,
        ),
        agent_prompt_module=AgentPromptModule(
            database_manager=database_manager,
            context=context,
            time_manager=time_manager,
        ),
        role_prompt_module=RoleplayPromptModule(
            database_manager=database_manager,
            context=context,
            time_manager=time_manager,
        ),
    )

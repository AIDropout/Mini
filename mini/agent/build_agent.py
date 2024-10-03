from config.config import Config
from config.container import container
from mini.agent.agent import AgentService
from mini.agent.modules.filter.filter import IntentConfig, MessageFilterModule
from mini.agent.modules.memory import MemoryManager
from mini.agent.modules.memory.service import MemoryModule
from mini.agent.modules.proactive import ScheduleDispatch
from mini.agent.modules.prompt import AgentPromptModule
from mini.agent.modules.sender import MessageSenderModule
from mini.core.enums import ConfidenceLevel
from mini.core.models.context import Context
from mini.llm import LLMService, Model

database_manager = container.database_manager
user_time_manager = container.user_time_manager
system_time_manager = container.system_time_manager


def build_agent(config: Config, context: Context) -> AgentService:

    return AgentService(
        schedule_dispatch=ScheduleDispatch(
            database_manager=database_manager,
            system_time_manager=system_time_manager,
            context=context,
            job_table_service=container.job_table_service,
        ),
        message_sender_module=MessageSenderModule(
            database_manager=database_manager,
            system_time_manager=system_time_manager,
            context=context,
            llm_manager=LLMService(
                model=Model.from_model_name(config.ACTION_MANAGER_LLM)
            ),
            message_table_service=container.message_table_service,
            session_table_service=container.session_table_service
        ),
        memory_module=MemoryModule(
            database_manager=database_manager,
            context=context,
            memory_manager=MemoryManager(
                user_id=None,
                agent_id=None,
                time_manager=user_time_manager,
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
        agent_prompt_module=AgentPromptModule(
            database_manager=database_manager,
            context=context,
            time_manager=user_time_manager,
        ),
    )

import json
import random
from datetime import datetime, timedelta
from zootopia.core.logger import logger
from zootopia.context import MessageContextManager, CronContextManager
from zootopia.core.schema import (
    RespondTask,
    MessageTableModel,
    Tables,
    TaskType,
    RespondTask,
    RemindTask,
    ReviveTask,
)
from zootopia.agent.agent import Agent
from config.config import config
import asyncio
from zootopia.server.redis import redis


def calculate_response_delay():
    scenarios = [
        (0, 0.7),  # Immediate response (70% chance)
        (5, 0.2),  # 5 seconds delay (20% chance)
        (10, 0.08),  # 10 seconds delay (8% chance)
        (15, 0.02),  # 15 seconds delay (2% chance)
    ]
    delay, _ = random.choices(scenarios, weights=[s[1] for s in scenarios])[0]
    return delay + random.randint(0, 3)  # Add some randomness


async def schedule_respond(request_body: dict):
    context = MessageContextManager(config, request_body)
    message = context.database.insert(
        Tables.MESSAGES.value,
        MessageTableModel(
            room_id=context.room.id, from_user=True, content=context.message.content
        ),
    )

    if message.content:
        delay = calculate_response_delay()
        response_time = datetime.now() + timedelta(seconds=delay)
        logger.info(f"🟢 Scheduling bot response in {delay} seconds")

        task_data = {
            "type": TaskType.RESPOND.value,
            "response_time": response_time.isoformat(),
            "original_request": request_body,
        }

        redis.zadd(
            "scheduled",
            {json.dumps(task_data): response_time.timestamp()},
        )


def print_diagnosis():
    now = datetime.now()
    scheduled_tasks = redis.zrange("scheduled", 0, -1, withscores=True)

    print(f"\n🪻 Scheduled tasks at {now.strftime('%H:%M:%S')}:")
    for i, (task, score) in enumerate(scheduled_tasks[:5]):
        task_data = json.loads(task.decode("utf-8"))
        scheduled_time = datetime.fromtimestamp(score)
        time_until_due = scheduled_time - now

        print(
            f"{i+1}. Time: {scheduled_time.strftime('%H:%M:%S')}, Due in: {time_until_due.total_seconds():.1f}s"
        )

    if len(scheduled_tasks) > 5:
        print(f"... and {len(scheduled_tasks) - 5} more tasks")
    elif len(scheduled_tasks) == 0:
        print("0 tasks scheduled.")


# This function should be run in a background task or separate process
async def process_scheduled_responses():
    logger.info("🟢 Background task started")
    count = 0
    while True:
        try:
            print_diagnosis()
            now = datetime.now().timestamp()
            due_responses = redis.zrangebyscore("scheduled", 0, now)

            for response_data in due_responses:
                if isinstance(response_data, bytes):
                    response_data = response_data.decode("utf-8")
                data = json.loads(response_data)
                logger.info(f"🟢 Processing scheduled response: {data}")

                print("1")

                task_type = data["type"]

                task = None
                context = None
                if task_type == TaskType.RESPOND.value:
                    original_request = data["original_request"]
                    context = MessageContextManager(config, original_request)
                    task = RespondTask(context.message)
                elif task_type == TaskType.REMIND.value:
                    room_id = data["room_id"]
                    context = CronContextManager(config, room_id)
                    task = RemindTask()
                # elif task_type == TaskType.REVIVE.value:
                #     task = ReviveTask()

                agent = Agent.from_config(config, context)
                success = await agent.handle_chat_task(task)

                # Remove the processed response from the sorted set
                if success:
                    redis.zrem("scheduled", response_data)

            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in background task: {e}")

        await asyncio.sleep(1)

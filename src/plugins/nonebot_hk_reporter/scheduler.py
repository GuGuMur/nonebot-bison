import nonebot
from nonebot import get_driver, logger
from .send import do_send_msgs
from .platform import platform_manager
from .config import Config
from .send import send_msgs
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def _start():
    scheduler.configure({"apscheduler.timezone": "Asia/Shanghai"})
    scheduler.start()

get_driver().on_startup(_start)

async def fetch_and_send(target_type: str):
    config = Config()
    target = config.get_next_target(target_type)
    if not target:
        return
    logger.debug('try to fecth new posts from {}, target: {}'.format(target_type, target))
    send_list = config.target_user_cache[target_type][target]
    bot_list = list(nonebot.get_bots().values())
    bot = bot_list[0] if bot_list else None
    to_send = await platform_manager[target_type].fetch_new_post(target, send_list)
    for user, send_list in to_send:
        for send_post in send_list:
            logger.info('send to {}: {}'.format(user, send_post))
            if not bot:
                logger.warning('no bot connected')
            else:
                send_msgs(bot, user.user, user.user_type, await send_post.generate_messages())

for platform_name, platform in platform_manager.items():
    if isinstance(platform.schedule_interval, int):
        logger.info(f'start scheduler for {platform_name} with interval {platform.schedule_interval}')
        scheduler.add_job(
                fetch_and_send, 'interval', seconds=platform.schedule_interval,
                args=(platform_name,))

@scheduler.scheduled_job('interval', seconds=1)
async def _send_msgs():
    await do_send_msgs()
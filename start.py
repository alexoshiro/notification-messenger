from apscheduler.schedulers.blocking import BlockingScheduler
import collector
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger('execution')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
handler = logging.FileHandler('logs/execution.log', 'w', 'utf-8')
handler.setFormatter(formatter)
logger.addHandler(handler)

'''
DEV print log in Console
'''
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)


sched = BlockingScheduler()

@sched.scheduled_job('cron', day_of_week='mon-sun', hour=11, minute=00, timezone="America/Campo_Grande", misfire_grace_time=3600)
def scheduled_job():
    collector.execute()

sched.start()
'''
if __name__ == '__main__':
    collector.execute()
'''
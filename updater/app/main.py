from timeloop import Timeloop
import logging
from datetime import timedelta

tl = Timeloop()
logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d] - %(message)s")
logger = logging.getLogger("updater")
tl.logger = logger


@tl.job(interval=timedelta(seconds=3600))
def check_for_updates():
    logger.info("check for updates... (tbd)")


if __name__ == "__main__":
    tl.start(block=True)

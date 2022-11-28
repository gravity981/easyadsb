from timeloop import Timeloop
import logging
from datetime import timedelta

tl = Timeloop()
logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d] - %(message)s")
logger = logging.getLogger("updater")
tl.logger = logger


@tl.job(interval=timedelta(seconds=3600))
def check_for_updates():
    # check for release tags and compare with locally installed version tag
    logger.info("check for updates... (tbd)")

    # UPDATE PROCESS:
    # download newer release

    # install easyadsb-core and easyadsb-gui to passive install dir

    # mark installation as "unverified", THEN toggle active install dir
    # --> what if power cycle or error during "unverified" state? --> corrupt update process, requires reinstallation
    # is there a way to rollback automatically and repair corruption?

    # restart services

    # perform integrity/health check (systemctl status)

    # if not successful, rollback active install dir and restart services

    # set installation to "verified"


if __name__ == "__main__":
    # check if installation is "verified"
    # --> mark installation as corrupt if not "verified" at startup
    # --> is there a way to rollback automatically in this case?
    tl.start(block=True)

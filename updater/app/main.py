import logging
import os
import sys
import github
import time
import requests

try:
    try:
        import common.mqtt as mqtt
        import common.logconf as logconf
    except ImportError:
        import mqtt
        import logconf
except ImportError:
    sys.path.insert(0, '../../common')
    import mqtt
    import logconf


checkIntervalSeconds = 3600


def checkForUpdates():
    while True:
        # check for release tags and compare with locally installed version tag
        logger.info("check for new releases...")
        gh = github.Github()
        try:
            repo = gh.get_repo("gravity981/easyadsb")
            releases = repo.get_releases()
            if releases.totalCount > 0:
                for r in releases:
                    logger.info("found: {}".format(r.title))
            else:
                logger.warning("no releases found")
        except requests.exceptions.ConnectionError as ex:
            logger.error("could not get releases, {}".format(str(ex)))

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
        time.sleep(checkIntervalSeconds)


if __name__ == "__main__":
    # check if installation is "verified"
    # --> mark installation as corrupt if not "verified" at startup
    # --> is there a way to rollback automatically in this case?
    logconf.setup_logging(str(os.getenv("UPDATER_LOG_LEVEL", "INFO")))
    logger = logging.getLogger("update_logger")
    mqtt.launchStart("easyadsb-updater", "localhost", 1883, [], None)
    checkForUpdates()

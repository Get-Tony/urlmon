"""
Session based URL monitor.

Monitor http or https URL connectivity.
If no URL arguments are provided, the script will look for a file named 'urls.txt' in the working directory.

Requirements:
requests >= 2.28.1
"""

__author__ = "Get-Tony@outlook.com"
__version__ = "1.0.0"

import logging
import os
import sys
from contextlib import contextmanager
from time import perf_counter, sleep

import requests
from requests.adapters import HTTPAdapter, Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("URLMonitor")

URL_FILE = "urls.txt"
SLEEP_TIME = 10
RETRIES = 0
RETRY_INTERVAL = 0.3
RETRY_FOR_STATUS_CODES = (500, 502, 503, 504)


def main():
    if len(sys.argv) > 1:
        URL_LIST = sys.argv[1:]
        logger.info("Using provided arguments: %s", URL_LIST)
    else:
        logger.info("No URL arguments provided.")
        logger.debug("Checking working directory for '%s'.", URL_FILE)
        URL_LIST = read_url_file()
        logger.info("Using '%s' found in working directory.", URL_FILE)

    while True:
        logger.debug("Starting URL checks.")
        for i in range(len(URL_LIST)):
            start = perf_counter()
            try:
                response = session.get(URL_LIST[i])
            except requests.exceptions.ConnectionError as conn_err:
                logger.error("[%s] Connection error to: %s", i, URL_LIST[i])
                continue
            end = perf_counter()
            elapsed_time = f"{end - start:.3f}s"
            if response is not None:
                if response.status_code == 200:
                    logger.info(
                        '[%s] %s is up. Elapsed time: %s', i, URL_LIST[i], elapsed_time)
                else:
                    logger.warn(
                        '[%s] %s is up but not OK. Status code: %s. Elapsed time: %s', i, URL_LIST[i], response.status_code, elapsed_time)
            else:
                logger.error(
                    '[%s] %s might be down! Elapsed time: %s', i, URL_LIST[i], elapsed_time)
        sleep(SLEEP_TIME)


def read_url_file():
    if not os.path.isfile(URL_FILE):
        logger.error("'%s' not found. Exiting.", URL_FILE)
        sys.exit(0)
    urls_from_file = []
    with open(URL_FILE, "r", encoding='UTF-8') as url_file:
        for line in url_file:
            urls_from_file.append(line.strip())
    return urls_from_file


class RequestsSession:
    """Requests session object."""

    def __init__(
        self, retries=2, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504)
    ):
        """Initialize Requests session."""
        self.session = requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get(self, url: str) -> requests.Response:
        """URL request."""
        return self.session.get(url)

    def close(self):
        """Close the session."""
        self.session.close()


@contextmanager
def new_session(*args, **kwargs):
    """Requests session context manager."""
    session = RequestsSession(*args, **kwargs)
    yield session
    session.close()


if __name__ == "__main__":
    try:
        with new_session(
            retries=RETRIES,
            backoff_factor=RETRY_INTERVAL,
            status_forcelist=RETRY_FOR_STATUS_CODES
        ) as session:
            main()
    except KeyboardInterrupt:
        logger.info("Keyboard Interrupt detected.")
    finally:
        logger.info("Exiting.")
        sys.exit(0)

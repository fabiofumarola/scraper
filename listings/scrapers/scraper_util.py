from lxml import html
import requests
import time
import random
import logging
from diskcache import Cache


pages_cache = Cache('pages_cache')

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('scraper')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

fh = logging.FileHandler('scraper.log')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)

logger.addHandler(ch)
logger.addHandler(fh)


def parse(url, max_time=5):
    content = ""
    if bytes(url,'utf8') in pages_cache:
        content = pages_cache[bytes(url,'utf8')]
    else:
        sleep_time = random.randint(1,max_time)
        logger.debug('sleeping for %d second', sleep_time)
        time.sleep(sleep_time)
        content = requests.get(url).content
        pages_cache.set(bytes(url,'utf8'),content, expire=18000, read=True)
        # pages_cache[bytes(url,'utf8')] = content

    tree = html.fromstring(content)
    tree.make_links_absolute(url)
    return tree


def flatten(a_list):
    if len(a_list) == 0:
        return ""
    else:
        return a_list[0]

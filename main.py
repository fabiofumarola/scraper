#!/usr/bin/env python
# coding=utf-8

import sys

from pyhocon import ConfigFactory

from listings.kafka_utils import *
from listings.scrapers import subito, idealista
from listings.scrapers.scraper_util import *
import schedule
import time
import redis


class JobManager(object):
    def __init__(self, args):
        name_conf_file = "./config/%s.conf" % args[1]
        conf = ConfigFactory.parse_file(name_conf_file)
        kafka_servers = conf.get('scraper.kafka.servers')
        self.kafka = KafkaListing(kafka_servers)
        self.producer = self.kafka.producer()
        redis_conf = conf.get('scraper.redis')
        self.visited_pages = redis.StrictRedis(host=redis_conf['host'], port=redis_conf['port'],
                                               db=redis_conf['db'])

        job_conf = conf.get('scraper.job')
        self.timeout = int(job_conf['timeout'])
        self.job_name = job_conf['name']
        self.mode = job_conf['mode']
        print('starting job %s' % job_conf)

    def _job(self, extractor):
        generator = extractor.list_page_url_generator(extractor.base_url, extractor.max_counter)
        for url in generator:
            logger.info('extracting records from url %s', url)
            records = extractor.extract_records(url)
            logger.info('got %d records from url %s', len(records), url)

            filtered = []
            for r in records:
                if not self.visited_pages.exists(r['url']):
                    self.visited_pages.set(r['url'], 1)
                    filtered.append(r)

            logger.info('retain %d records after filtering from url %s', len(filtered), url)

            if len(filtered) == 0 and self.mode == 'force':
                logger.info('forcing extracting from url %s since mode %s also if got 0 records',
                            url, self.mode)
            elif len(filtered) == 0:
                logger.info('stopping extracting from url %s since mode %s', url, self.mode)
                break
            else:
                logger.error('un-matched case ')
                break

            for r in filtered:
                extractor.extract_from_detail_page(r)
                logger.info('saving to kafka record with url %s', r['url'])
                self.producer.send(r)

    def subito_job(self):
        logger.info("starting scraping subito")
        self._job(subito)

    def idlista_job(self):
        logger.info("starting scraping idealista")
        self._job(idealista)

    def start(self):
        schedule.clear()
        if self.job_name == 'subito':
            schedule.every(self.timeout).seconds.do(self.subito_job)
        elif self.job_name == 'idealista':
            schedule.every(self.timeout).seconds.do(self.idlista_job)
        else:
            logger.error('unknown job %s', self.job_name)
            sys.exit(2)

        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('please specify on of the file name into the folder config')
        sys.exit(2)

    manager = JobManager(sys.argv)
    manager.start()

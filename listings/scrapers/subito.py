from lxml import html
from lxml.cssselect import CSSSelector
import requests
import time
import random
import logging
import json
from listings.scrapers.scraper_util import *

base_url = 'http://www.subito.it/annunci-lombardia/vendita/appartamenti/milano/milano/?sqs=4&o={}'
max_counter = 100


def list_page_url_generator(base_url, max_counter):
    counter = 1
    while counter <= max_counter:
        yield base_url.format(str(counter))
        counter += 1


def extract_records(url):
    tree = parse(url)
    elements = tree.xpath('//article')
    records = list()
    for elem in elements:
        try:
            records.append(extract_record(elem))
        except ValueError as e:
            logger.debug('removed record with content %s', elem.text_content())

    return records


def extract_record(elem):
    id_title_url = [(link.attrib['name'], link.attrib['title'], link.attrib['href'])
                    for link in elem.xpath('div/div[2]/h2/a')]

    if len(id_title_url) == 0:
        raise ValueError("empty element")

    ids = [i for i, _, _ in id_title_url]
    titles = [t for _, t, _ in id_title_url]
    urls = [u for _, _, u in id_title_url]

    prices = [e.text.strip() for e in elem.cssselect('span.item_price')]
    categories = [e.text.strip() for e in elem.cssselect('span.item_category')]
    specs = [e.text.strip() for e in elem.cssselect('span.item_specs')]
    datetimes = [e.attrib['datetime'] for e in elem.cssselect('time')]
    locations = [e.text_content().strip() for e in elem.cssselect('span.item_location')]

    return {
        'src': 'subito',
        'id': flatten(ids),
        'title': flatten(titles),
        'url': flatten(urls),
        'price': flatten(prices),
        'category': flatten(categories),
        'datetime': flatten(datetimes),
        'location': flatten(locations),
        'phone': ""
    }


def extract_from_detail_page(record):
    url = record['url']
    tree = parse(url)

    map_details = dict()

    descriptions = [e.text for e in tree.cssselect('div.description')]
    map_details['description'] = flatten(descriptions)

    for row in tree.xpath('//*[@id="ad_details"]/div[1]/table/tr'):
        children = row.getchildren()
        map_details[children[0].text.strip()] = children[1].text.strip()

    logger.info('extracted details for the url %s', url)

    record['details'] = map_details

    return record

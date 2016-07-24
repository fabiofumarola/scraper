from lxml import html
from lxml.cssselect import CSSSelector
import requests
import logging
import json
from listings.scrapers.scraper_util import *

base_url = 'http://www.idealista.it/vendita-case/milano-milano/lista-{}.htm'
max_counter = 628


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
            logger.info('removed record with content %s', elem.text_content())

    return records


def extract_record(elem):
    title_url = [(link.attrib['title'], link.attrib['href'])
                 for link in elem.cssselect('a.item-link')]

    if len(title_url) == 0:
        raise ValueError('empty element')

    titles = [t for t, _ in title_url]
    urls = [u for _, u in title_url]
    ids = [u.split('/')[-2] for u in urls]

    prices = list()
    categories = list()
    phones = [p.text for p in elem.cssselect('span.icon-phone')]

    return {
        'src': 'idealista',
        'id': flatten(ids),
        'title': flatten(titles),
        'url': flatten(urls),
        'price': flatten(prices),
        'category': flatten(categories),
        'datetime': "",
        'location': "",
        'phone': flatten(phones)
    }


def extract_from_detail_page(record):
    url = record['url']
    tree = parse(url)

    map_details = dict()

    price_down = [e.text_content() for e in tree.cssselect('span.icon-pricedown')]

    map_details['price_down'] = flatten(price_down)

    for kv in tree.xpath('//*[@id="details"]/div'):
        key = flatten([k.text_content() for k in kv.xpath('h2')]).strip()
        value = [v.text_content().strip() for v in kv.xpath('ul/li')]
        map_details[key] = value

    logger.info('extracted details for the url %s', url)

    record['details'] = map_details
    return record

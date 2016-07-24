from kafka import KafkaConsumer, KafkaProducer
import json


class KafkaListing(object):
    def __init__(self, bootstrap_servers):
        self.bootstrap_servers = '127.0.0.1:9092'
        self.topic = 'raw_home_listings'

    def producer(self):
        return Producer(self.bootstrap_servers, self.topic)

    def consumer(self):
        consumer = KafkaConsumer(bootstrap_servers=self.bootstrap_servers)
        consumer.subscribe([self.topic])
        return consumer


class Producer(object):
    def __init__(self, bootstrap_servers, topic):
        self.bootstrap_servers = '127.0.0.1:9092'
        self.topic = 'raw_home_listings'
        self.producer = KafkaProducer(bootstrap_servers=bootstrap_servers)

    def send(self, record):
        key = bytes(record['src'] + ":" + record['id'], 'utf-8')
        value = json.dumps(record).encode('utf-8')
        return self.producer.send(self.topic, key=key, value=value)

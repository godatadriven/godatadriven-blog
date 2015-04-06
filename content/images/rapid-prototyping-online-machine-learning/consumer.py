import avro.schema
import avro.io
import io
from kafka import KafkaConsumer
import argparse
import pickle
import redis
import requests
import json
import numpy as np

NUM_ITEMS = 6
EXPERIMENT_COUNT_KEY = 'experiments'
ITEM_SET_KEY = 'items'
REFRESH_INTERVAL = 100

def main(args):
    global es_host, es_port, redis_client
    es_host, es_port = args.elasticsearch.split(':')
    redis_host, redis_port = args.redis.split(':')
    redis_client = redis.StrictRedis(host=redis_host, port=int(redis_port))

    refresh_items()
    start_consumer(args)

def start_consumer(args):
    schema = avro.schema.Parse(open(args.schema).read())
    consumer = KafkaConsumer(args.topic, client_id=args.client, group_id=args.group, metadata_broker_list=args.brokers)
    reader = avro.io.DatumReader(schema)
    for message in consumer:
        handle_event(message, reader)

def handle_event(message, reader):
    message_bytes = io.BytesIO(message.value)
    decoder = avro.io.BinaryDecoder(message_bytes)
    event = reader.read(decoder)

    if 'top_pick' == event['source']:
        redis_client.incr(event['productId'])
    elif 'home' == event['pageType']:
        experiment_count = redis_client.incr(EXPERIMENT_COUNT_KEY)
        if experiment_count == REFRESH_INTERVAL:
            refresh_items()

def refresh_items():
    current_items = redis_client.lrange(ITEM_SET_KEY, 0, -1)

    p = redis_client.pipeline(transaction=False)
    for item in current_items: p.get(item)
    current_win_counts = [count for count in p.execute()]

    current_experiment_count = redis_client.get(EXPERIMENT_COUNT_KEY)

    random_items = [
        item['id']
        for item in random_item_set(NUM_ITEMS + NUM_ITEMS - len(current_items) // 2)
        if not item['id'] in current_items][:NUM_ITEMS - len(current_items) // 2]

    samples = [
        np.random.beta(int(win_count or 1), int(current_experiment_count or 1))
        for win_count in current_win_counts]

    survivors = [
        item
        for score,item in sorted(
            zip(samples, current_items),
            key=lambda score_item: score_item[0])[len(current_items) // 2:]]

    new_items = survivors + random_items

    p = redis_client.pipeline(transaction=True)
    p.set(EXPERIMENT_COUNT_KEY, 1)
    for item in current_items: p.delete(item)
    p.delete(ITEM_SET_KEY)
    for item in new_items: p.rpush(ITEM_SET_KEY, item)
    p.execute()

def random_item_set(count):
    query = {
        "query": {
            "function_score" : {
            "query" : { "match_all": {} },
                "random_score" : {}
            }
        }, "size": count
    }

    result = requests.get('http://%s:%s/catalog/_search' % (es_host, es_port), data=json.dumps(query))
    return [hit['_source'] for hit in result.json()['hits']['hits']]

def parse_args():
    def to_bytes(s):
        return bytes(s, 'utf-8')

    parser = argparse.ArgumentParser(description='Runs the consumer.')
    parser.add_argument('--redis', '-r', metavar='REDIS_HOST_PORT', type=str, required=False, default='localhost:6379', help='Redis hostname + port.')
    parser.add_argument('--schema', '-s', metavar='SCHEMA', type=str, required=True, help='Avro schema of Kafka messages.')
    parser.add_argument('--client', '-c', metavar='CLIENT_ID', type=to_bytes, required=True, help='Kafka client id.')
    parser.add_argument('--group', '-g', metavar='GROUP_ID', type=to_bytes, required=True, help='Kafka consumer group id.')
    parser.add_argument('--brokers', '-b', metavar='KAFKA_BROKERS', type=str, nargs="+", help='A list of Kafka brokers (host:port).', default=['localhost:9092'])
    parser.add_argument('--topic', '-t', metavar='TOPIC', type=to_bytes, required=False, default='divolte', help='Kafka topic.')
    parser.add_argument('--elasticsearch', '-e', metavar='ELASTIC_SEARCH_HOST_PORT', type=str, required=False, default='localhost:9200', help='The ElasticSearch instance to connect to (host:port).')
    return parser.parse_args()


if __name__ == '__main__':
    main(parse_args())

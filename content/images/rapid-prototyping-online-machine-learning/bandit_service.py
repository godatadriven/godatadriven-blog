from tornado import web,httpserver,ioloop,gen
import argparse
import os
import numpy
import tornadoredis as redis

ITEM_HASH_KEY = 'items'

CLICK_KEY_PREFIX = 'c|'
IMPRESSION_KEY_PREFIX = 'i|'

class BanditHandler(web.RequestHandler):
    redis_client = None

    def initialize(self, redis_client):
        self.redis_client = redis_client

    @gen.coroutine
    def get(self):
        # Fetch model state.
        item_dict = yield gen.Task(self.redis_client.hgetall, ITEM_HASH_KEY)
        items = numpy.unique([k[2:] for k in item_dict.keys()])

        # Draw random samples.
        samples = [
            numpy.random.beta(int(item_dict[CLICK_KEY_PREFIX + item]), int(item_dict[IMPRESSION_KEY_PREFIX + item]))
            for item in items]

        # Select item with largest sample value.
        winner = items[numpy.argmax(samples)]

        self.write(winner)


def main(args):
    redis_host, redis_port = args.redis.split(':')
    redis_client = redis.Client(host=redis_host, port=int(redis_port))

    routes = [
        web.URLSpec(r'/item', BanditHandler, { 'redis_client': redis_client}),
    ]

    application = web.Application(
        routes,
        debug=args.debug
        )
    server = httpserver.HTTPServer(application)
    server.bind(args.port, address=args.address)
    server.start()
    ioloop.IOLoop.current().start()


def parse_args():
    parser = argparse.ArgumentParser(description='Runs the webapp.')
    parser.add_argument('--port', '-p', metavar='PORT', type=int, required=False, default=8989, help='The TCP port to listen on for HTTP requests.')
    parser.add_argument('--address', '-a', metavar='BIND_ADDRESS', type=str, required=False, default='127.0.0.1', help='The address to bind on.')
    parser.add_argument('--redis', '-r', metavar='REDIS_HOST_PORT', type=str, required=False, default='localhost:6379', help='Redis hostname + port.')
    parser.add_argument('--debug', '-d', dest='debug', action='store_true', required=False, default=False, help='Run in debug mode.')
    return parser.parse_args()


if __name__ == '__main__':
    main(parse_args())

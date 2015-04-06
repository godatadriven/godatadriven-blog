from tornado import web,httpserver,ioloop,gen

import argparse
import os
import numpy as np
import tornadoredis as redis

EXPERIMENT_COUNT_KEY = 'experiments'
ITEM_SET_KEY = 'items'


class BanditHandler(web.RequestHandler):
    redis_client = None

    def initialize(self, redis_client):
        self.redis_client = redis_client

    @gen.coroutine
    def get(self):
        p = self.redis_client.pipeline()
        p.get(EXPERIMENT_COUNT_KEY)
        p.lrange(ITEM_SET_KEY, 0, -1)
        num_experiments, items = yield gen.Task(p.execute)

        p = self.redis_client.pipeline()
        for item in items: p.get(item)
        win_counts = yield gen.Task(p.execute)

        samples = [np.random.beta(int(win_count or 1), int(num_experiments or 1)) for win_count in win_counts]
        winner = items[np.argmax(samples)]

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

Title: Rapid Prototyping of Online Machine Learning with Divolte Collector
Date: 2015-04-06 13:00
Slug: rapid-prototyping-online-machine-learning-divolte-collector
Author: Friso van Vollenhoven
Excerpt: Divolte Collector is our open source solution for getting high volume clickstream data into Hadoop anf Kafka. When properly setup, we can use this to rapidly prototype online and offline machine learning applications in minimal amounts of Python code. This is an example of a online multi-armed bandit optimization using Divolte Collector and Redis as a back-end.
Template: article
Latex:


It is said that in most Data Science solutions, 80 percent of the work is engineering data preparation and only 20 percent is spent on actual modelling and algorithms. Your mileage may vary. Another observation is that when there is a need for near realtime processing, the engineering gets even harder (and often the machine learning models simpler). Let me illustrate this with a an architectural overview of a typical web optimisation setup:

![web-optimization.png](static/images/rapid-prototyping-online-machine-learning/web-optimization-architecture.png)

Let's disect this a bit:

- [Divolte Collector](http://divolte.io) is an open source solution created at GoDataDriven. In a nutshell it makes sure that clickstream events in the browser are captured and traslated into Avro records which are sent to HDFS and Kafka for offline and online processing. It is called from a accompanying piece of Javascript that runs in the web page to fire events. Divolte Collector allows for a dynamic mapping between clickstream events and a arbitrary Avro schema.
- [Hadoop](http://hadoop.apache.org) is more or less de facto these days for processing high volume data. Here when we say Hadoop, we mean a cluster runnig HDFS and several Hadoop ecosystem projects for data processing, such as Hive, Impala, Spark and possibly others.
- [Kafka](http://kafka.apache.org) is a high-throughput distributed messaging system. Kafka has producers that create messages and consumers that use messages as input for online data processing. Divolte Collector is a Kafka producer and the consumers run our machine learning models against streaming data.
- The processing of clickstream events typically happens both offline in batch processing and online in near realtime. The batch processing can for example be using Spark jobs, while the online part are typically Kafka consumers.
- Machine learning models normally have some amount of model state, which needs to be persisted and available for model evaluation with very low latency. Normally we use some kind of in-memory database here, such as Redis. Other databases can also be used, as most databases perform caching and data will often be effectively in-memory.
- The API server takes care of actually evaluating the trained model using the stored model state and the sample input at hand.
- The web server requests a model evaluation from the API server and uses it to render the response to the client.

*That's a lot of moving parts!* If we need to build all of this in order to do something seemingly simple, such as draw a random sample from a number of parameterized distributions (i.e. multi-armed bandit optimization) or perform a classification using a pre-trained classifier, we'd hardly ever get anything done. For this reason at GoDataDriven we focus on setting up this kind of infrastructure once and try to make it generic enough to implement different types of applications on top of it. This is also the reason we invest in building Divolte Collector; it solves a very important engineering problem for companies that operate high-volume website.

In this post, we'll have a look at implementing a prototype multi-armed bandit optmization using this stack with minimal Python code and a Redis database for model state. We will use Divolte Collector to provide us with near realtime clickstream data.

### The Problem
At GoDataDriven we internally use a little fake web shop application for demo purposes. We call it the Shop for Humans. At the Shop for Humans, you can "buy" photos for which you "pay" by solving a series of [CAPTCHA's](http://en.wikipedia.org/wiki/CAPTCHA); hence the Shop for *Humans*, not bots. The shop delivers the photos by just providing you with the direct links to the source after you complete the checkout procedure (which can be quite tedious, as CAPTCHA's are involved). The photos in the shop are taken from [Flickr](https://www.flickr.com). Just to be clear: no we don't sell other people's photos on the internet; we just use some photos for an internal demo application. All the photos are filtered to have commercially friendly Creative Commons licensing and there is proper attribution.

![shop-category.png](static/images/rapid-prototyping-online-machine-learning/shop-category.png)
<small>For humans. No bots allowed.</small>

On the homepage of the web shop, we'd like to display one featured image. Instead of just picking a random image from the catalog or hand-picking this image, we'd like to pick which image to displayed by using a popular Bayesian approach to multi-armed bandit optmization often called Bayesian bandits.

### The Model: Bayesian Bandits for Photo Selection
We can use the Bayesian bandit approach to selecting one photo from a set of photos for display on the homepage. The Bayesian bandit algorithm works by updating priors about click-through for each item and then taking a sample from a set of distributions parameterized with these priors and pick the photo for which the sample value is largest. That is, whenever we serve the homepage with one of the images, we check if there is a click-through on this image. If so, we increment a counter for that image. When we want to pick an image for the homepage, for each image we take a sample from a [Beta distribution](http://en.wikipedia.org/wiki/Beta_distribution) with parameters alpha equal to the number of click-throughs for that image and beta equal to the number of times we've shown the homepage thusfar. The image with largest sample value wins. You can find reasonable explanations of this concept [here](http://tdunning.blogspot.nl/2012/02/bayesian-bandits.html) and [here](https://www.chrisstucchio.com/blog/2013/bayesian_bandit.html).

Because we have a lot of images in our catalog and we might not get enough visitors to figure out which one is best from all the images that exist, we want to use a limited set of images to run the opmization on. We also want to change this set of images every now and then, to further explore the complete catalog. In order to do this, we use the following method:

1. Pick a random set of *n* images.
2. Learn the distributions for these images using the Bayesian bandit method.
3. After *X* experiments:
    1. Select the top half of the current set of images by sampling from the learned distributions.
    2. Select *n / 2* new images from the catalog randomly.
    3. Create a new set of images using the top half from the sample and the newly selected random ones.
    4. Reset all the distributions to alpha=1, beta=1.
4. Go to 2.

The idea here is that we keep top performing images and discard the less performing images in favor of exploring further in the catalog. After refreshing the image set, we assign equal priors to all images again. This model should be simple enough to implement in Python. Ideally, it should take about an afternoon of work to build this, test it and put it in production.

### Step 1: Prototype the UI
So, we need to put an image on the homepage and have it be clickable. Also, we need to make sure we can keep track of the click-through for this image. To prototype the UI and take care of the capturing the proper events, we start out by just putting a fixed image on the homepage. 

Our shop is written in Python and uses [Tornado](http://www.tornadoweb.org/en/stable/). The image metadata is stored in [ElasticSearch](https://www.elastic.co/products/elasticsearch), which we abstract away with a little service written in Java. The shop back end isn't really important for our prototype. It should generally be easy enough to include an atrbitrary product from the catalog on a homepage. In our shop, the handler code for this is this:

    :::python
    class HomepageHandler(ShopHandler):
      @coroutine
      def get(self):
          # Hard-coded ID for a pretty flower.
          # Later this ID will be decided by the bandit optmization.
          winner = '15442023790'

          # Grab the item details from our catalog service.
          top_item = yield self._get_json('catalog/item/%s' % winner)

          # Render the homepage
          self.render(
              'index.html',
              top_item=top_item)

The accompanying template for rendering the homepage includes this:

    :::html
    <div class="col-md-6">
      <h4>Top pick:</h4>
      <p>
        <!-- Link to the product page with a source identifier for tracking -->
        <a href="/product/{{ top_item['id'] }}/#/?source=top_pick">
          <img class="img-responsive img-rounded" src="{{ top_item['variants']['Medium']['img_source'] }}">
        </a>
      </p>
      <p>
        Photo by {{ top_item['owner']['real_name'] or top_item['owner']['user_name']}}
      </p>
    </div>

Here's the new homepage:

![shop-homepage.png](static/images/rapid-prototyping-online-machine-learning/shop-homepage.png)
<small>Shop for Humans; brought to you by bandits. Photo by [Flickr user Jonathan Leung](https://www.flickr.com/photos/jonathan-leung/15442023790/).</small>

Note that we conclude the href URL with this little suffix: <code>#/?source=top_pick</code>. We are going to use this to capture the event of a click-through. We use a URL fragment (the part after the #), so we don't bother the server side code with this tracking directly. Instead, we capture the URL fragment in the Divolte Collector mapping and populate a special field in our event records when it is present. In Divolte Collector event records are just [Avro](https://avro.apache.org) records, which are populated from incoming requests according the a [specific mapping](http://divolte-releases.s3-website-eu-west-1.amazonaws.com/divolte-collector/0.2.1/userdoc/html/mapping_reference.html) which you specify in a Groovy based DSL. Please have a look at [the mapping documentation](http://divolte-releases.s3-website-eu-west-1.amazonaws.com/divolte-collector/0.2.1/userdoc/html/mapping_reference.html) for more details on this (or read our [Getting Started guide](http://divolte-releases.s3-website-eu-west-1.amazonaws.com/divolte-collector/0.2.1/userdoc/html/getting_started.html)).

In our event record schema, we add the following field to capture the source of a click:

    :::json
    { "name": "source",
      "type": ["null", "string"],
      "default": null
    }

Subsequently, we need to tell Divolte Collector about this field and how to populate it. In the mapping we will use the URL fragment to parse out the source parameter. Note that the fragment we add uses URL syntax for specifying this field; the source is just a query parameter. Here's the mapping required to get this piece of data into our records:

    :::groovy
    def locationUri = parse location() to uri
    def fragmentUri = parse locationUri.rawFragment() to uri
    map fragmentUri.query().value('source') onto 'source'

That's it. Data collection is setup. We can now start learning&hellip;

### Step 2: Create the Kafka Consumer to Update Model State
    
Consumer should update priors in case of click through and refresh the set of images when X experiments have run.

    :::python
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

Here's how you get a random set of documents from ElasticSearch:

    :::python
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

And this is how we update the image set:

    :::python
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


### Step 3: Create the API to Evaluate the Model
The API should query Redis for the priors, sample from the distributions and return the winner. Note that updating model state is decoupled form evaluating the model this way.

    :::python
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


### Step 4: Integrate
Here's the new handler code for the homepage. The template doesn't change, of course.

    :::python
    class HomepageHandler(ShopHandler):
        @coroutine
        def get(self):
            http = AsyncHTTPClient()
            request = HTTPRequest(url='http://localhost:8989/item', method='GET')
            response = yield http.fetch(request)
            winner = json_decode(response.body)
            top_item = yield self._get_json('catalog/item/%s' % winner)

            self.render(
                'index.html',
                top_item=top_item)


### Possible Model Improvements
- Instead of resetting all priors, keep the ones we've learned for the survivors and set the ones for the random images using historical clickstream; this can easily be done by making it a spark job and decoupling it from the consumer.
- Model priors based on (latent) features of catalog images; either visual or metadata based (e.g. category, photographer).
- Contextualize bandits

### Conclusion
The reason you can do these things in 100 lines of Python and run them for real, is that you've thought about clickstream collection, data infrastructure and made sure your data has a schema. There is nog magic, just a lot of engineering work.

### F.A.Q.
Q: Would you actually run this in prodcution?
A: With the addition of load balancing and failover, yes.

Q: Multiple Redis requests, Python, HTTP. How slow is this thing?
A: Not very. Computers are fast and cheap. For many problems it's not how efficiently you use them, but how effectively you use them.


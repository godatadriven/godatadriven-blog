Title: Including custom Flume components in Cloudera Manager
Date: 2016-02-21 15:00
Slug: cmf-flume-component-metrics
Author: Barend Garvelink
Excerpt: This article shows how to add custom Flume sources and sinks to the Metrics Details page in Cloudera Manager.
Template: article

I'm currently working on a Hadoop project using Cloudera's stack. We're running a couple of [Flume][flume] jobs to move data around our cluster. Our Flume Metric Details page in Cloudera Manager looked like this:

![cmf-screenshot](/static/images/flume-component-stats-in-cloudera-manager/flume-cmf-metrics-details.png "A screenshot of Cloudera Manager showing statistics for three Channels, three Sinks and two Sources in Flume")

You could infer from the image that we run a `BarSource` alongside our `FooSource` and `BazSource` and you would be correct. However, it doesn't show up in Cloudera Manager. Why not?

The `FooSource` and `BazSource` are standard source types included with the platform. The `BarSource` is a subclass of [`AbstractEventDrivenSource`][aedso] that we wrote ourselves to pull data from a customer-specific system.

How do you get a custom Flume source or sink included on this dashboard? This is not difficult, the secret is simply JMX. Unfortunately, the documentation is a bit thin. At the time of writing, the [Flume Developer Guide][fdevg] doesn't mention JMX at all.

The `flume-core` package includes JMX MBeans for each of the component types: [`SourceCounter`][souco], [`ChannelCounter`][chaco] and [`SinkCounter`][sinco]. If you include the appropriate counter MBean in your custom Flume component, that component will appear in Cloudera Manager. Here's a simple example of `SourceCounter` in use:

    :::java
    package com.xebia.blog.flume;

    import org.apache.flume.Context;
    import org.apache.flume.Event;
    import org.apache.flume.FlumeException;
    import org.apache.flume.instrumentation.SourceCounter;
    import org.apache.flume.source.AbstractEventDrivenSource;

    /**
     * Demonstrates the use of the {@code SourceCounter}` in Flume-NG.
     */
    public class DemoSource extends AbstractEventDrivenSource {

        private SourceCounter counter;

        @Override
        protected void doConfigure(Context context) throws FlumeException {

            // Counter MBeans are created in the configure method, with the component name we've been provided.
            this.counter = new SourceCounter(this.getName());
        }

        @Override
        protected void doStart() throws FlumeException {
            // You start the counter in start()
            this.counter.start();

            // This example is an event-driven source, so we'll typically have some sort of connection and callback method.
            connectToDataSourceWithCallback(this);
            this.counter.setOpenConnectionCount(1);
        }

        @Override
        protected void doStop() throws FlumeException {
            // Disconnect from the data source...
            disconnect();
            this.counter.setOpenConnectionCount(0);

            // ...and stop the counter.
            this.counter.stop();
        }

        /**
         * Callback handler for our example data source.
         */
        public void onIncomingData(Object dataSourceEvent) {
            // Count how many events we receive...
            this.counter.incrementEventReceivedCount();

            // ...do whatever processing it is we do...
            Event flumeEvent = convertToFlumeEvent(dataSourceEvent);

            // ...and count how many are successfully forwarded.
            getChannelProcessor().processEvent(flumeEvent);
            this.counter.incrementEventAcceptedCount();
        }
    }

The `SourceCounter` MBean has some other metrics that you can increment as needed. The `ChannelCounter` and `SinkCounter` MBeans work the same way. In lieu of full documentation, the Flume source code can be mined for examples: [sources][sourc], [channels][chann] and [sinks][sinks].

_This article was originally published [on the Xebia Blog][xebia]._

[flume]:https://flume.apache.org/
[aedso]:https://flume.apache.org/releases/content/1.6.0/apidocs/org/apache/flume/source/AbstractEventDrivenSource.html
[fdevg]:https://flume.apache.org/FlumeDeveloperGuide.html
[souco]:https://flume.apache.org/releases/content/1.6.0/apidocs/org/apache/flume/instrumentation/SourceCounter.html
[chaco]:https://flume.apache.org/releases/content/1.6.0/apidocs/org/apache/flume/instrumentation/ChannelCounter.html
[sinco]:https://flume.apache.org/releases/content/1.6.0/apidocs/org/apache/flume/instrumentation/SinkCounter.html
[sourc]:https://github.com/apache/flume/tree/trunk/flume-ng-sources
[chann]:https://github.com/apache/flume/tree/trunk/flume-ng-channels
[sinks]:https://github.com/apache/flume/tree/trunk/flume-ng-sinks
[xebia]:http://blog.xebia.com/custom-flume-cloudera-manager/

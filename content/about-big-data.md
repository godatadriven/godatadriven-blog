Title: About Big Data
Date: 2015-01-18 20:00
Slug: about-big-data
Author: Friso van Vollenhoven
Excerpt: What is Big Data? Does size matter? Is it worth it? A reflrection on the Big Data hype and the technology that it brought us.
Template: article
Latex:

Before you start to complain that Big Data is a highly overloaded term, I think that regardless of whether that is true, we will have to learn to live with it for now. The term Big Data is going to stay with us for a while. Here's why:

![trends-chart](static/images/about-big-data/bigdata-search-volume.png)
<br/><small>Source: [Google Trends](http://www.google.com/trends/explore#q=Big%20Data%2C%20data%20science%2C%20business%20intelligence&cmpt=q&tz=).</small>

Clearly, interest is peaking and people are in a buying mood. When people are in a buying mood, companies are selling. The companies that are selling have entire departments dedicated to making sure that we hear about it (a.k.a. marketing), hence: I think we will be hearing about Big Data for some time to come. Instead, let's have a look at how we got there. (We will get to these other three plotted search phrases in a bit as well.)

### Big Data avant la lettre
Back in 2009, I was part of a team working on indexing and retrieval of high volume network data collected by our customer. Their existing solution of sharding MySQL databases worked, but was tedious to maintain and was coping with scalability issues, so we were using [Apache Hadoop](http://en.wikipedia.org/wiki/Apache_Hadoop) and [HBase](http://en.wikipedia.org/wiki/Apache_HBase). Both of these technologies were difficult to maintain at best and would fail with cryptic error messages at seemingly random moments until you would spend some time reading the actual source code and figured out how things really worked. On top of that, the software wasn't spectacularly efficient in what it did; it didn't squeeze all possible performance out of the machines it would run on. However, in spite of these quirks, Hadoop and HBase did one key thing above anything else: they scaled. Hadoop and its MapReduce implementation provided a *generally available, open source, scalable abstraction* that allowed developers to focus on their data processing code. In essence it meant that it didn't matter whether you were coding a job for a cluster of two machines or a cluster of two hundred machines; the same code would run equally on both. If you have a lot of data and you don't know how fast it will grow, that means a lot. Not to mention that there was a lively community of people working on this open source software that would answer questions on mailing lists in a manner far superior to most commercial support offerings available for database software.

Not too much later, Hadoop was gaining traction as large web properties were reporting sucesses with the technology. The critics were busy pointing out the practical problems, while people who understood the theoretical possibilities were working hard to improve the software. That's also when the departments dedicated to making sure we hear about things caught on, started calling it Big Data and made extra sure everybody knew about [the three, four or five V's](http://en.wikipedia.org/wiki/Big_data#Characteristics) that ought to be associated with it. (Note that [the original report that first listed the three V's](http://blogs.gartner.com/doug-laney/files/2012/01/ad949-3D-Data-Management-Controlling-Data-Volume-Velocity-and-Variety.pdf) doesn't have the term "big data" in it anywhere.)

### The Big Data promise

![full-moon](static/images/about-big-data/full-moon.png)
<br/><small>Source: [Google Trends](http://www.google.com/trends/explore#q=full%20moon&date=today%2012-m&cmpt=q&tz=) and [moongiant.com](http://www.moongiant.com/Full_Moon_New_Moon_Calendar.php). Note: Google Trends only exposes week-by-week data, so the full moon dates are normalised to the start of the week they occured in as well.</small>

### Computers are cheap and fast

<blockquote class="twitter-tweet" data-cards="hidden" lang="en"><p>&quot;&#39;If you had bought the computing power found inside an iPhone 5S in 1991, it would have cost you $3.56 million.&#39;&quot; <a href="http://t.co/Z2b1zKcn4J">http://t.co/Z2b1zKcn4J</a></p>&mdash; Steven Sinofsky (@stevesi) <a href="https://twitter.com/stevesi/status/547275417141272576">December 23, 2014</a></blockquote>
<small>With or without two year subscription. It wouldn't exactly have been pocket size either.</small>
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>

![memory-prices](static/images/about-big-data/storage_memory_prices.png)
<br/><small>Source and image credit: [http://hblok.net/blog/storage/](http://hblok.net/blog/storage/).</small>

### The inefficiency of scaling out


<table class="table table-condensed table-bordered">
  <thead>
    <th>Task</th><th>Time</th><th>Code</th>
  </thead>
  <tbody>
    <tr>
      <td>Read file and count 600M lines</td>
      <td><strong><nobr>13 seconds</nobr></strong></td>
      <td><pre>
val tf = sc.textFile("/mnt/raid/numbers.txt")
tf.count</pre></td>
    </tr>
    <tr>
      <td>Read file, parse CSV and count 600M records</td>
      <td><strong><nobr>64 seconds</nobr></strong></td>
      <td width="55%"><pre>
val data = tf.map(_.split('|'))
             .map(line => (
                  line(0).toLong, line(1).toLong,
                  line(2).toLong, line(3).toLong,
                  line(4).toLong, line(5).toDouble,
                  line(6).toDouble)
                 )
data.count</pre></td>
    </tr>
    <tr>
      <td>Summary statistics over 600M floating points</td>
      <td><strong><nobr>68 seconds</nobr></strong></td>
      <td width="55%"><pre>
import org.apache.spark.SparkContext._
data.map(_._5.toDouble)
    .stats
</pre></td>
    </tr>
    <tr>
      <td>Low cardinality group by key + count</td>
      <td><strong><nobr>74 seconds</nobr></strong></td>
      <td width="55%"><pre>
data.map( x => (x._3, 1) )
    .reduceByKey(_ + _)
    .collect
</pre></td>
    </tr>
    <tr>
      <td>Top 10 of high cardinality column with long tail distribution</td>
      <td><strong><nobr>241 seconds</nobr></strong></td>
      <td width="55%"><pre>
data.map( x => (x._4, 1) )
    .reduceByKey(_ + _)
    .map(List(_))
    .reduce( (x,y) => (x ++ y).sortWith(_._2 > _._2)
                              .slice(0,10))
</pre></td>
    </tr>
    <tr>
      <td>KMeans clustering on ~60M cached 2D vectors<br/><small>Note: clustering took two iterations to converge. Add about 4 seconds for each consecutive iteration. Time does not include taking the sample and caching.</small>
      </td>
      <td><strong><nobr>39 seconds</nobr></strong></td>
      <td width="55%"><pre>
import org.apache.spark.mllib.clustering.KMeans
import org.apache.spark.mllib.linalg.Vectors
val clusterData =
  data.sample(false, 0.1)
      .map(
        t => Vectors.dense( Array(t._6, t._7) )
      )
clusterData.cache
clusterData.count // returns 60011237
val clusters = KMeans.train(clusterData, 4, 10)
</pre></td>
    </tr>
  </tbody>
</table>

  > Time is wall clock time. Data was generated using [this code](static/images/about-big-data/generate-data.html). Spark was configured to run 12 executors with 2 cores each, using a maximum of 8GB heap per executor.

### Conclusion

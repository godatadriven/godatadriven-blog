Title: I Mapreduced a Neo store
Date: 2013-06-17 11:00
Slug: i-mapreduced-a-neo-store
Author: Kris Geusebroek
Excerpt: When exploring very large raw datasets containing massive interconnected networks, it is sometimes helpful to extract your data, or a subset thereof, into a graph database like Neo4j. This allows you to easily explore and visualize networked data to discover meaningful patterns.<br /><br />If your graph has 20M+ nodes and 1000M+ edges, using the regular Neo4j import tools will make the import very time consuming (as in many hours to days).<br />To speed up things we used Hadoop to scale the creation of very large Neo4j databases by distributing the load across a cluster.
Template: article


Lately I've been busy talking at conferences to tell people about our way to create large [Neo4j](http://www.neo4j.org/) databases. Large means some tens of millions of nodes and hundreds of millions of relationships and billions of properties.

Although the technical description is already on the Xebia blog [part 1][] and [part 2][], I would like to give a more functional view on what we did and why we started doing it in the first place.

Our use case consisted of exploring our data to find interesting patterns. The data we want to explore is about financial transactions between people, so the Neo4j graph model is a good fit for us. Because we don't know upfront what we are looking for we need to create a Neo4j database with some parts of the data and explore that. When there is nothing interesting to find we go enhance our data to contain new information and possibly new connections and create a new Neo4j database with the extra information.

This means it's **not** about a one time load of the current data and keep that up to date by adding some more nodes and edges. It's really about building a new database from the ground up everytime we think of some new way to look at the data.

### First try without Hadoop
Before we created our Hadoop based solution, we used the batchimport framework provided with Neo4j (the [batch inserter API](http://docs.neo4j.org/chunked/milestone/batchinsert.html)). This allows you to insert a large amount of nodes and edges without the transactional overhead (Neo4j is ACID compliant). The batch importer API is a very good fit for the medium sized graphs, or the one time imports of large datasets, but in our case recreating multiple databases a day, the running time was too long.

### Scaling out
To speed the process we wanted to use our Hadoop cluster. If we could make the process of creating a Neo4j database work in a distributed way, we could make use of the total amount of cluster machines instead of the single machine batchimporter.

But how do you go about that? The batch import framework was built upon the idea of having a single place to store the data. Having a server running somewhere the cluster could connect to had multiple downsides:

- How to handle downtime of the Neo4j server
- You're back to being transactional
- You need to check if nodes are already existing

So the idea became to build the database **really** from the ground up. Would it be possible to build the underlying filestructure without having the need of Neo4j running somewhere? Would be cool right?

So we did! We investigated the internal filestructure (see how it works in [part 2] of the technical blogs) and had to overcome one more hurdle to really make it work.

We needed [monotonically increasing row ids][] because the position in a Neo4j file means something. The id of the node or relationship is directly connected to the offset in the file. So we couldn't get a way with just adding some numbers as id's to our data because there couldn't be a gap between the numbering. In Friso's blog about the [monotonically increasing row ids][] you can read all about how we did that.

More information is available in our [presentation][], the code is on [github][], and you can contact us if you want to know more.

  [part 1]: http://blog.xebia.com/2012/11/13/combining-neo4j-and-hadoop-part-i/ "Combining neo4j and Hadoop Part 1"
  [part 2]: http://blog.xebia.com/2013/01/17/combining-neo4j-and-hadoop-part-ii/ "Combining neo4j and Hadoop Part 2"
  [monotonically increasing row ids]: /monotonically-increasing-row-ids-with-mapreduce.html "Monotonically increasing row ids"
  [presentation]: http://www.slideshare.net/godatadriven/i-mapreduced-a-neo-store-creating-large-neo4j-databases-with-hadoop "Slideshare presentation"
  [github]: https://github.com/krisgeus/graphs "The code"

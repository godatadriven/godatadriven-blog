Title: Refactor Hadoop job: old to new API
Date: 2014-03-28 17:00
Slug: refactor-hadoop-job-new-api
Author: Alexander Bij
Excerpt: In this post I want to improve an existing hadoop-job I have created earlier. The this blog I will describe what the impact is of updating the code to the new api and How to run the job in a cluster separate from eclipse.

In this post I want to improve the existing hadoop-job I have created earlier: [wiki-pagerank-with-hadoop](http://blog.xebia.com/2011/09/27/wiki-pagerank-with-hadoop/)

## The goals:

1.  Update to the new stable hadoop version.
2.  Use the new API. 
3.  Setup a single-node hadoop-cluster.
4.  Easily build a job-jar with maven.

I have used version 0.20.204.0 for the initial hadoop-jobs. The hadoop commiters have been busy in the mean time, the latest stable version at the moment is available 2.2.0.

### 1. Update Hadoop Version
Updating to the latest version is just a matter of updating the version in the pom.xml and maven will do the rest for you, as long as the version is available in the repository. In my pom I have configured the mirror ibiblio which contains the latest version of hadoop. The client classes to build a job are now in a separate dependency.

    <dependency>
      <groupId>org.apache.hadoop</groupId>
      <artifactId>hadoop-core</artifactId>
      <version>2.2.0</version>
    </dependency>

    <!-- now the client is seperated from core jar -->
    <dependency>
      <groupId>org.apache.hadoop</groupId>
      <artifactId>hadoop-client</artifactId>
      <version>2.2.0</version>
    </dependency>


Lets download the new version

    mvn clean compile


### 2. Use new API
In the IDE I noticed that the classes from _org.apache.hadoop.mapred.*_  are not deprecated anymore. In the old version some of the classes are marked as deprecated, because at that time there was a new API available. The old API is un-deprecated, because its here to stay. Note: both old and new api will work.

This is an overview of the most important changes:


| What                 | Old                                                 | New                                     |
|:---------------------|:----------------------------------------------------|:----------------------------------------|
| *classes location*   | org.apache.hadoop.**mapred**                        | org.apache.hadoop.**mapreduce**         |
| *conf class*         | JobConf                                             | Configuration                           |
| *map method*         | map(k1, v1, OutputCollector<k2, v2>, Reporter)      | map(k1, v1, Context)                    |
| *reduce method*      | reduce(k2, Iterator<v2>, OutputCollector<k3, v3>)   | reduce(k2, Iterable<v2>, Context)       |
| *reduce method*      | while (values.hasNext()) { ... }                    | for (v2 value : values) { ... }         |
| *map/reduce*         | throws IOException                                  | throws IOException, InterruptedException|
| *before map/reduce*  |                                                     | setup(Context ctx)                      |
| *after map/reduce*   | close()                                             | cleanup(Context ctx)                    |
| *client class*       | JobConf / JobClient                                 | Job                                     |
| *run job*            |JobClient.runJob(job)                                | job.waitForCompletion(true)             |


Migrating to the new API was not so difficult. Delete all the imports with org.apache.hadoop.mapred.* and re-import with the correct package. Then fix all the errors one by one. You can [checkout github](https://github.com/abij/hadoop-wiki-pageranking) with the new code and the changes I made to support the new API. The functionality is not changed.

Old api:

    public class RankCalculateMapper extends MapReduceBase implements Mapper<LongWritable, Text, Text, Text>{
      public void map(LongWritable key, Text value, OutputCollector<Text, Text> output, Reporter reporter) throws IOException {
        ...
        output.collect(new Text(page), new Text("|"+links));
      }
    }

New api:

    public class RankCalculateMapper extends Mapper<LongWritable, Text, Text, Text> {
      public void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
        ...
        context.write(new Text(page), new Text("|" + links));
      }
    }


### 3. Setup a single-node hadoop-cluster.
I the previous post I had a plugin for eclipse to run the main class directly in the hadoop cluster. Acually the plugin creates the job-jar and sends it to the cluster. Since I have switched from IDE I can't use the plugin anymore and I want an independent job builder so the job can be created and run without Eclipse. Installing your own single node cluster is very easy these days.

Install a virtual machine: [VirtualBox](https://www.virtualbox.org/wiki/Downloads) or [VMwarePlayer](https://my.vmware.com/web/vmware/downloads) and download a quickstart distribution from your favorite vendor:

- Cloudera: [http://go.cloudera.com/vm-download](http://go.cloudera.com/vm-download)
- Hortonworks: [http://hortonworks.com/products/hortonworks-sandbox/](http://hortonworks.com/products/hortonworks-sandbox/)

After starting the virtual machine, a 'cluster' is available! _(Pseudo Distributed mode)_ Outside the virtual machine, from your own machine, you should be able to access the HUE page [http://localhost:8888](http://localhost:8888).

To move files between host and virtual-machine there are multiple options.

1.  Configure a shared folder.
2.  Use the HUE webinterface to upload files
3.  Use secure copy over ssh.

I went for option 3: scp. For that option I need to access the virtual machine over ssh on port 22.
My VirtualBox was configured with network settings NAT and port-forwarding. I have added a port-forwarding rule for host from port 2222 to guest 22.

Now I can copy files from my machine to the virtual machine using:

    scp -P 2222 data_subset.xml cloudera@localhost:~

On the virtual machine we should add the data in HDFS on the correct place.

    hadoop fs -mkdir wiki
    hadoop fs -mkdir wiki/in
    hadoop fs -put data_subset.xml /user/cloudera/wiki/in/


### 3. Easily build a job-jar with maven.
In the origional setup the code and eclipse were thightly coupled. To make a separate jar I used the maven-assembly-plugin. Make sure you do not include the hadoop-common and hadoop-client in your jar by marking these depencies as scope: provided. The dependencies not marked as scope test/provided like commons-io will be included in your jar.


    <build>
      <plugins>
        ...
        <plugin>
          <artifactId>maven-assembly-plugin</artifactId>
          <version>2.4</version>
          <configuration>
            <descriptorRefs>
              <descriptorRef>jar-with-dependencies</descriptorRef>
            </descriptorRefs>
          </configuration>
        </plugin>
      </plugins>
    </build>

    <dependencies>

      <dependency>
        <groupId>org.apache.hadoop</groupId>
        <artifactId>hadoop-common</artifactId>
        <version>2.2.0</version>
        <scope>provided</scope>
      </dependency>
  
      <dependency>
        <groupId>org.apache.hadoop</groupId>
        <artifactId>hadoop-client</artifactId>
        <version>2.2.0</version>
        <scope>provided</scope>
      </dependency>
  
      ...

    </dependencies>


Now you can create your job:

    mvn assembly:assembly

    [INFO] --- maven-assembly-plugin:2.4:assembly (default-cli) @ hadoop-wiki-pageranking ---
    [INFO] Building jar: /Users/abij/projects/github/hadoop-wiki-pageranking/target/hadoop-wiki-pageranking-0.2-SNAPSHOT-jar-with-dependencies.jar
    [INFO] ------------------------------------------------------------------------
    [INFO] BUILD SUCCESS
    [INFO] ------------------------------------------------------------------------
    [INFO] Total time: 2.590s
    [INFO] Finished at: Fri Jan 31 13:25:18 CET 2014
    [INFO] Final Memory: 15M/313M
    [INFO] ------------------------------------------------------------------------


Now copy the fresh baked job to the cluster and run it.
Local machine:

    scp -P 2222 hadoop-wiki-pageranking-*-dependencies.jar cloudera@localhost:~

Virtual machine:

    hadoop jar hadoop-wiki-*.jar com.xebia.sandbox.hadoop.WikiPageRanking

Watch the proces in HUE: 
[http://localhost:8888/jobbrowser/](http://localhost:8888/jobbrowser/)


### Recap
In this blog we have updated the vanilla hadoop map-reduce job from the old API to the new API. Updating was not hard, but touches all the classes. We used maven to generate a job from the code and run it in a cluster. The new source code is available from my [https://github.com/abij/hadoop-wiki-pageranking](https://github.com/abij/hadoop-wiki-pageranking)


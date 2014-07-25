Title: Local and Pseudo-distributed CDH5 Hadoop on your laptop
Date: 2014-04-22 17:00
Slug: local-and-pseudo-distributed-cdh5-hadoop-on-your-laptop
Author: Kris Geusebroek
Excerpt: When Cloudera Distribution for Hadoop version 5 came out it was time for me to install that software on my laptop too. I'm used to the installation process on Linux machines (even VM images) with ansible, but as I don't have a Linux laptop, I had to resort to the tarball distribution. So here I describe the steps I have taken to get CDH5 working in both local and pseudo-distributed mode.
Template: article
Latex:

Installing CDH5 from the tarball distribution is not a really difficult, but getting the pseudo-distributed configuration right is all but straightforward. So it was well worth writing about it.

### Getting the software

Getting the software was the easiest part. Just go to <a href="https://www.cloudera.com/content/support/en/downloads.html" target="_blank">The Cloudera Download</a> page and push the button below the text *For Developers*. This will get you to the download products page where you can select the version and the type. I chose CDH5.0.0 and clicked the <a href="http://www.cloudera.com/content/cloudera-content/cloudera-docs/CDH5/latest/CDH-Version-and-Packaging-Information/cdhvd_cdh_package_tarball.html">Tarballs</a> link.

Here you'll get a long list of Hadoop components, each with its own package. I downloaded Hadoop and Spark as they're what I need at the moment.

### Unpacking

1. I created a new directory on my local file system called `cdh5.0.0`. I refer to that directory as `/cdh5.0.0` from now on and unpacked the two downloaded packages:

        :::shell
        $ mkdir /cdh5.0.0
        $ cd /cdh5.0.0
        $ tar -xvzf hadoop-2.3.0-cdh5.0.0.tar.gz
        $ mkdir spark-0.9.0-cdh5.0.0 && cd spark-0.9.0-cdh5.0.0 && tar -xvzf ../spark-0.9.0-cdh5.0.0.tar.gz && cd ../

This unpacks the tarballs; see how I created the Spark directory myself as its tarball is packed differently than the Hadoop one.

### Hadoop in local mode

Using Hadoop in local mode is pretty easy. All it takes are a few environment settings pointing to the correct directories and you are good to go.
In my `.bash_profile` I always use aliases to switch between environments easily.
For the hadoop local mode settings I use this one:

    :::shell
    alias switch_local_cdh5='export JAVA_HOME=$(/usr/libexec/java_home -v 1.7);
        export HADOOP_PREFIX=/cdh5.0.0/hadoop-2.3.0-cdh5.0.0;
        export HADOOP_COMMON_HOME=${HADOOP_PREFIX};
        export HADOOP_HDFS_HOME=${HADOOP_PREFIX};
        export HADOOP_MAPRED_HOME=${HADOOP_PREFIX};
        export HADOOP_YARN_HOME=${HADOOP_PREFIX};
        export SPARK_HOME=/cdh5.0.0/spark-0.9.0-cdh5.0.0;
        export PATH=${HADOOP_PREFIX}/bin:${SPARK_HOME}/bin:$PATH;
        export HADOOP_CONF_DIR=/cdh5.0.0/hadoop-2.3.0-cdh5.0.0/etc/hadoop;'

When I start a new terminal session I can easily export the variables in one with:

    :::shell
    $ switch_local_cdh5

Now all the familiar hadoop commands should work. There is no notion of HDFS other then your local filesystem so the hadoop fs -ls / command will show you the same output as ls /

    :::shell
    $ hadoop fs -ls /

        drwxrwxr-x   - root admin       2686 2014-04-18 09:47 /Applications
        drwxr-xr-x   - root wheel       2210 2014-02-26 02:46 /Library
        drwxr-xr-x   - root wheel         68 2013-08-25 05:45 /Network
        drwxr-xr-x   - root wheel        136 2013-10-23 03:05 /System
        drwxr-xr-x   - root admin        204 2013-10-23 03:09 /Users
        drwxrwxrwt   - root admin        136 2014-04-18 12:34 /Volumes
        [...]

    $ ls -l /

        drwxrwxr-x+ 79 root  admin   2.6K Apr 18 09:47 Applications
        drwxr-xr-x+ 65 root  wheel   2.2K Feb 26 02:46 Library
        drwxr-xr-x@  2 root  wheel    68B Aug 25  2013 Network
        drwxr-xr-x+  4 root  wheel   136B Oct 23 03:05 System
        drwxr-xr-x   6 root  admin   204B Oct 23 03:09 Users
        drwxrwxrwt@  4 root  admin   136B Apr 18 12:34 Volumes

Running a MapReduce job should also  work out of the box.

    :::shell
    $ cd ${HADOOP_PREFIX}

    $ hadoop jar share/hadoop/mapreduce/hadoop-mapreduce-examples-2.3.0-cdh5.0.0.jar pi 10 100

        Number of Maps  = 10
        Samples per Map = 100
        2014-04-19 18:05:01.596 java[74281:1703] Unable to load realm info from SCDynamicStore 14/04/19 18:05:02 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
        Wrote input for Map #0
        Wrote input for Map #1
        Wrote input for Map #2
        Wrote input for Map #3
        Wrote input for Map #4
        Wrote input for Map #5
        Wrote input for Map #6
        Wrote input for Map #7
        Wrote input for Map #8
        Wrote input for Map #9
        Starting Job
        ....
        Job Finished in 1.587 seconds
        Estimated value of Pi is 3.14800000000000000000

### Hadoop in pseudo-distributed mode

Pseudo-distributed mode is a bit more complicated. Pseudo-distributed mode means that all involved daemons that make Hadoop tick are running on your local machine.
You need a separate pair of configuration files for that; Let's start by creating a new directory for them:

    :::shell
    $ cd /cdh5.0.0
    $ mkdir conf.pseudo

Now we have to populate this directory with the correct files and contents. Creating them manually is a long and tedious task. Being a lazy programmer I looked for the easy way out and I found a Linux package called hadoop-conf-pseudo.
But as mentioned above, I don't have a Linux laptop. So I fired up a CentOS virtual machine and inside that virtual machine configured the CDH5 yum repository.

    :::shell
    $ echo -e "[cloudera-5-repo]\nname=CDH 5 repo\nbaseurl=http://archive.cloudera.com/cdh5/redhat/6/x86_64/cdh/5/\ngpgcheck=0\n" > /etc/yum.repos.d/CDH5.repo
    $ yum install hadoop-conf-psuedo

This creates a nicely filled directory in `/etc/hadoop/conf.pseudo` which we are going to copy over to my laptop

    :::shell
    $ cp -r /etc/hadoop/conf.pseudo /mnt/hgfs/cdh5.0.0/conf.pseudo.linux

Let's see what's in there:

    :::shell
    $ ll /cdh4.0.0/conf.pseudo.linux/
        total 80
        -rwxr-xr-x  1 user  staff   1.1K Apr 19 18:29 README
        -rwxr-xr-x  1 user  staff   2.1K Apr 19 18:29 core-site.xml
        -rwxr-xr-x  1 user  staff   1.3K Apr 19 18:29 hadoop-env.sh
        -rwxr-xr-x  1 user  staff   2.8K Apr 19 18:29 hadoop-metrics.properties
        -rwxr-xr-x  1 user  staff   1.8K Apr 19 18:29 hdfs-site.xml
        -rwxr-xr-x  1 user  staff    11K Apr 19 18:29 log4j.properties
        -rwxr-xr-x  1 user  staff   1.5K Apr 19 18:29 mapred-site.xml
        -rwxr-xr-x  1 user  staff   2.3K Apr 19 18:29 yarn-site.xml

We need to change a few things because the directory structure on our laptop is different than the on the Linux machine where these files came from. So let's have a look at the contents and discover what configurations we need to adjust.

The main concepts that we need are HDFS and YARN so let's focus on those. The other configuration files can be copied without changes.

    :::shell
    $ cp /cdh5.0.0/conf.pseudo.linux/core-site.xml /cdh5.0.0/conf.pseudo/
    $ cp /cdh5.0.0/conf.pseudo.linux/hadoop-env.sh /cdh5.0.0/conf.pseudo/
    $ cp /cdh5.0.0/conf.pseudo.linux/hadoop-metrics.properties /cdh5.0.0/conf.pseudo/
    $ cp /cdh5.0.0/conf.pseudo.linux/log4j.properties /cdh5.0.0/conf.pseudo/

#### First things first: HDFS

    :::shell
    $ vi /cdh5.0.0/conf.pseudo.linux/hdfs-site.xml

In this file there are a few different configuration settings pointing to the locations of the namenode, secondary namenode and datanode data directories.

    :::xml
    ...
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/var/lib/hadoop-hdfs/cache/${user.name}</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>file:///var/lib/hadoop-hdfs/cache/${user.name}/dfs/name</value>
    </property>
    <property>
        <name>dfs.namenode.checkpoint.dir</name>
        <value>file:///var/lib/hadoop-hdfs/cache/${user.name}/dfs/namesecondary</value>
    </property>
    <property>
         <name>dfs.datanode.data.dir</name>
         <value>file:///var/lib/hadoop-hdfs/cache/${user.name}/dfs/data</value>
    </property>
    ...

Let's copy this file over to our `/cdh5.0.0/conf.pseudo` directory and change the locations of these configuration parameters. Don't forget to create the referenced directories.

	:::shell
    $ cp /cdh5.0.0/conf.pseudo.linux/hdfs-site.xml /cdh5.0.0/conf.pseudo/
    $ vi /cdh5.0.0/conf.pseudo/hdfs-site.xml


    <edit>
    ...
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/cdh5.0.0/var/lib/hadoop-hdfs/cache/${user.name}</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>file:///cdh5.0.0/var/lib/hadoop-hdfs/cache/${user.name}/dfs/name</value>
    </property>
    <property>
        <name>dfs.namenode.checkpoint.dir</name>
        <value>file:///cdh5.0.0/var/lib/hadoop-hdfs/cache/${user.name}/dfs/namesecondary</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>file:///cdh5.0.0/var/lib/hadoop-hdfs/cache/${user.name}/dfs/data</value>
    </property>
    ...

And don't forget to create the directories

	:::shell
    $ cd /cdh5.0.0
    $ mkdir -p var/lib/hadoop-hdfs/cache/${USER}/dfs/data
    $ mkdir -p var/lib/hadoop-hdfs/cache/${USER}/dfs/namesecondary
    $ mkdir -p var/lib/hadoop-hdfs/cache/${USER}/dfs/name


We also need the correct environment settings remember?
For the Hadoop pseudo distributed mode settings I use this one:

    :::shell
    alias switch_pseudo_cdh5='export JAVA_HOME=$(/usr/libexec/java_home -v 1.7);
        export HADOOP_PREFIX=/cdh5.0.0/hadoop-2.3.0-cdh5.0.0;
        export HADOOP_COMMON_HOME=${HADOOP_PREFIX};
        export HADOOP_HDFS_HOME=${HADOOP_PREFIX};
        export HADOOP_MAPRED_HOME=${HADOOP_PREFIX};
        export HADOOP_YARN_HOME=${HADOOP_PREFIX};
        export SPARK_HOME=/cdh5.0.0/spark-0.9.0-cdh5.0.0;
        export PATH=${HADOOP_PREFIX}/sbin:${HADOOP_PREFIX}/bin:${SPARK_HOME}/bin:${PATH};
        export HADOOP_CONF_DIR=/cdh5.0.0/hadoop-2.3.0-cdh5.0.0/conf.pseudo;'

Watch the extra `$HADOOP_PREFIX/sbin` addition to the `PATH` variable. We'll need that in a minute.

Does it work yet? Let's try.

    :::shell
    $ switch_psuedo_cdh5
    $ hadoop fs -ls /

        2014-04-19 19:14:06.047 java[76056:1703] Unable to load realm info from SCDynamicStore
        14/04/19 19:14:06 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
        ls: Call From localdomain.local/111.11.11.1 to localhost:8020 failed on connection exception: java.net.ConnectException: Connection refused; For more details see:  http://wiki.apache.org/hadoop/ConnectionRefused

Guess not. The daemons are not running so need to start them. This can be done with the simple `start-dfs.sh` command since we added the `HADOOP_PREFIX/sbin` directory which contains the daemon start/stop scripts to our `PATH` variable.

    :::shell
    $ start-dfs.sh

You may need to type in your password multiple times because the daemons are started through ssh connection to `localhost`.
Now we'll check again to see if it works! We're impatient programmers right?

    :::shell
    $ hadoop fs -ls /

        2014-04-19 19:14:06.047 java[76056:1703] Unable to load realm info from SCDynamicStore
        14/04/19 19:14:06 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
        ls: Call From localdomain.local/111.11.11.1 to localhost:8020 failed on connection exception: java.net.ConnectException: Connection refused; For more details see:  http://wiki.apache.org/hadoop/ConnectionRefused

Still nothing. To understand what happens here we have to go back a bit and look at the output of the `start-dfs.sh` command:

    :::shell
    $ start-dfs.sh
        2014-04-19 19:21:38.976 java[76172:1703] Unable to load realm info from SCDynamicStore
        14/04/19 19:21:39 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
        Starting namenodes on [localhost]
        Password:
        localhost: starting namenode, logging to /cdh5.0.0/hadoop-2.3.0-cdh5.0.0/logs/hadoop-user-namenode-localdomain.local.out
        localhost: 2014-04-19 19:21:45.992 java[76243:1b03] Unable to load realm info from SCDynamicStore
        cat: /cdh5.0.0/conf.pseudo/slaves: No such file or directory
        Starting secondary namenodes [0.0.0.0]
        Password:
        0.0.0.0: starting secondarynamenode, logging to /cdh5.0.0/hadoop-2.3.0-cdh5.0.0/logs/hadoop-user-secondarynamenode-localdomain.local.out
        0.0.0.0: 2014-04-19 19:21:53.619 java[76357:1b03] Unable to load realm info from SCDynamicStore
        2014-04-19 19:21:58.508 java[76405:1703] Unable to load realm info from SCDynamicStore
        14/04/19 19:21:58 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable

See the `cat: /cdh5.0.0/conf.pseudo/slaves: No such file or directory` message? We didn't have that file in our `conf.pseudo.linux` directory, did we? Luckily the file is available in the local configuration directory: let's copy it and stop the daemons that did not start correctly.

    :::shell
    $ stop-dfs.sh
    $ cp /cdh5.0.0/hadoop-2.3.0-cdh5.0.0/etc/hadoop/slaves /cdh5.0.0/conf.pseudo/
    $ start-dfs.sh
    $ hadoop fs -ls /
        2014-04-19 19:14:06.047 java[76056:1703] Unable to load realm info from SCDynamicStore
        14/04/19 19:14:06 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
        ls: Call From localdomain.local/111.11.11.1 to localhost:8020 failed on connection exception: java.net.ConnectException: Connection refused; For more details see:  http://wiki.apache.org/hadoop/ConnectionRefused

Nothing. We stop the HDFS daemons again and look at the logs:

    :::shell
    $ stop-dfs.sh
        2014-04-19 19:33:02.835 java[77195:1703] Unable to load realm info from SCDynamicStore
        14/04/19 19:33:02 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
        Stopping namenodes on [localhost]
        Password:
        localhost: no namenode to stop
        Password:
        localhost: stopping datanode
        Stopping secondary namenodes [0.0.0.0]
        Password:
        0.0.0.0: stopping secondarynamenode
        2014-04-19 19:33:24.863 java[77400:1703] Unable to load realm info from SCDynamicStore
        14/04/19 19:33:24 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable

Hey! What's that `localhost: no namenode to stop` message? Let's look at the namenode logs first then.

    :::shell
    $ vi /cdh5.0.0/hadoop-2.3.0-cdh5.0.0/logs/hadoop-user-namenode-localdomain.local.log

        <go to the end>

        2014-04-19 19:32:20,064 FATAL org.apache.hadoop.hdfs.server.namenode.NameNode: Exception in namenode join
        java.io.IOException: NameNode is not formatted.
            at org.apache.hadoop.hdfs.server.namenode.FSImage.recoverTransitionRead(FSImage.java:216)
            at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.loadFSImage(FSNamesystem.java:879)
            at org.apache.hadoop.hdfs.server.namenode.FSNamesystem.loadFromDisk(FSNamesystem.java:638)
            at org.apache.hadoop.hdfs.server.namenode.NameNode.loadNamesystem(NameNode.java:440)
            at org.apache.hadoop.hdfs.server.namenode.NameNode.initialize(NameNode.java:496)
            at org.apache.hadoop.hdfs.server.namenode.NameNode.<init>(NameNode.java:652)
            at org.apache.hadoop.hdfs.server.namenode.NameNode.<init>(NameNode.java:637)
            at org.apache.hadoop.hdfs.server.namenode.NameNode.createNameNode(NameNode.java:1286)
            at org.apache.hadoop.hdfs.server.namenode.NameNode.main(NameNode.java:1352)
        2014-04-19 19:32:20,066 INFO org.apache.hadoop.util.ExitUtil: Exiting with status 1
        2014-04-19 19:32:20,067 INFO org.apache.hadoop.hdfs.server.namenode.NameNode: SHUTDOWN_MSG:

The log is telling us that we need to format HDFS first.

    :::shell
    $ hadoop namenode -format
    $ start-dfs.sh
    $ hadoop fs -ls /
    $ hadoop fs -mkdir /bogus
    $ hadoop fs -ls /
        2014-04-19 19:46:32.233 java[78176:1703] Unable to load realm info from SCDynamicStore
        14/04/19 19:46:32 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
        Found 1 items
        drwxr-xr-x   - user supergroup          0 2014-04-19 19:46 /bogus

Ok we're in!

#### Now we focus on the YARN part

    :::shell
    $ vi /cdh5.0.0/conf.pseudo.linux/yarn-site.xml

There we have a few different configuration settings pointing to the locations of the container logs and nodemanager local directory.

    :::xml
    ...
    <property>
        <description>List of directories to store localized files in.</description>
        <name>yarn.nodemanager.local-dirs</name>
        <value>/var/lib/hadoop-yarn/cache/${user.name}/nm-local-dir</value>
    </property>
    <property>
        <description>Where to store container logs.</description>
        <name>yarn.nodemanager.log-dirs</name>
        <value>/var/log/hadoop-yarn/containers</value>
    </property>
    <property>
        <description>Where to aggregate logs to.</description>
        <name>yarn.nodemanager.remote-app-log-dir</name>
        <value>/var/log/hadoop-yarn/apps</value>
    </property>
    <property>
        <description>Classpath for typical applications.</description>
        <name>yarn.application.classpath</name>
        <value>
            $HADOOP_CONF_DIR,
            $HADOOP_COMMON_HOME/*,$HADOOP_COMMON_HOME/lib/*,
            $HADOOP_HDFS_HOME/*,$HADOOP_HDFS_HOME/lib/*,
            $HADOOP_MAPRED_HOME/*,$HADOOP_MAPRED_HOME/lib/*,
            $HADOOP_YARN_HOME/*,$HADOOP_YARN_HOME/lib/*
        </value>
    </property>
    ...

Let's copy this file over to our `/cdh5.0.0/conf.pseudo` directory and change the locations of these configuration parameters. And don't forget to create the referenced directories.

```shell
    $ cp /cdh5.0.0/conf.pseudo.linux/yarn-site.xml /cdh5.0.0/conf.pseudo/
    $ vi /cdh5.0.0/conf.pseudo/yarn-site.xml
```

```xml
    ...
    <property>
        <description>List of directories to store localized files in.</description>
        <name>yarn.nodemanager.local-dirs</name>
        <value>/cdh5.0.0/var/lib/hadoop-yarn/cache/${user.name}/nm-local-dir</value>
    </property>
    <property>
        <description>Where to store container logs.</description>
        <name>yarn.nodemanager.log-dirs</name>
        <value>/cdh5.0.0/var/log/hadoop-yarn/containers</value>
    </property>
    <property>
        <description>Where to aggregate logs to.</description>
        <name>yarn.nodemanager.remote-app-log-dir</name>
        <value>/var/log/hadoop-yarn/apps</value>
    </property>
    <property>
        <description>Classpath for typical applications.</description>
        <name>yarn.application.classpath</name>
        <value>
            $HADOOP_CONF_DIR,
            $HADOOP_COMMON_HOME/share/hadoop/common/*,
            $HADOOP_COMMON_HOME/share/hadoop/common/lib/*,
            $HADOOP_HDFS_HOME/share/hadoop/hdfs/*,
            $HADOOP_HDFS_HOME/share/hadoop/hdfs/lib/*,
            $HADOOP_MAPRED_HOME/share/hadoop/mapreduce/*,
            $HADOOP_MAPRED_HOME/share/hadoop/mapreduce/lib/*,
            $HADOOP_YARN_HOME/share/hadoop/yarn/*,
            $HADOOP_YARN_HOME/share/hadoop/yarn/lib/*
        </value>
    </property>
    ...
```

And don't forget to create these directories

	:::shell
    $ cd /cdh5.0.0
    $ mkdir -p var/lib/hadoop-yarn/cache/${USER}/nm-local-dir
    $ mkdir -p var/log/hadoop-yarn/containers

The `yarn.nodemanager.remote-app-log-dir` property doesn't need to change as that's a variable referring to a path on HDFS.
Now let's try and start the YARN daemons (make sure the HDFS daemons are still running)

    :::shell
    $ start-yarn.sh
        starting yarn daemons
        starting resourcemanager, logging to /cdh5.0.0/hadoop-2.3.0-cdh5.0.0/logs/yarn-user-resourcemanager-localdomain.local.out
        Password:
        localhost: starting nodemanager, logging to /cdh5.0.0/hadoop-2.3.0-cdh5.0.0/logs/yarn-user-nodemanager-localdomain.local.out
    $ cd ${HADOOP_PREFIX}
    $ hadoop jar share/hadoop/mapreduce/hadoop-mapreduce-examples-2.3.0-cdh5.0.0.jar pi 10 100

Looks like it's working. But wait, what is the output saying?

    :::shell
    Number of Maps  = 10
    Samples per Map = 100
    2014-04-20 00:23:57.055 java[79203:1703] Unable to load realm info from SCDynamicStore
    14/04/20 00:23:57 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
    Wrote input for Map #0
    Wrote input for Map #1
    Wrote input for Map #2
    Wrote input for Map #3
    Wrote input for Map #4
    Wrote input for Map #5
    Wrote input for Map #6
    Wrote input for Map #7
    Wrote input for Map #8
    Wrote input for Map #9
    Starting Job
    ...
    14/04/20 00:23:59 INFO mapred.LocalJobRunner:
    14/04/20 00:23:59 INFO mapred.MapTask: Starting flush of map output
    14/04/20 00:23:59 INFO mapred.MapTask: Spilling map output
    14/04/20 00:23:59 INFO mapred.MapTask: bufstart = 0; bufend = 18; bufvoid = 104857600
    14/04/20 00:23:59 INFO mapred.MapTask: kvstart = 26214396(104857584); kvend = 26214392(104857568); length = 5/6553600
    14/04/20 00:23:59 INFO mapred.MapTask: Finished spill 0
    14/04/20 00:23:59 INFO mapred.Task: Task:attempt_local37475800_0001_m_000000_0 is done. And is in the process of committing
    14/04/20 00:23:59 INFO mapred.LocalJobRunner: map
    ...

It still mentions the `LocalJobRunner`. Ah wait, there was this `mapred-site.xml` we didn't copy yet. Let's do that.

    :::shell
    $ cd /cdh5.0.0
    $ cp conf.pseudo.linux/mapred-site.xml conf.pseudo/
    $ vi conf.pseudo/mapred-site.xml

There we have a configuration setting pointing to the location of the mapreduce `tmp` directory.

    :::xml
    ...
    <property>
        <description>To set the value of tmp directory for map and reduce tasks.</description>
        <name>mapreduce.task.tmp.dir</name>
        <value>/var/lib/hadoop-mapreduce/cache/${user.name}/tasks</value>
    </property>
    ...

Let's change that one too

```shell
    $ vi conf.pseudo/mapred-site.xml
```

```xml
    ...
    <property>
        <description>To set the value of tmp directory for map and reduce tasks.</description>
        <name>mapreduce.task.tmp.dir</name>
        <value>/cdh5.0.0/var/lib/hadoop-mapreduce/cache/${user.name}/tasks</value>
    </property>
    ...
```

```shell
    $ cd /cdh5.0.0
    $ mkdir -p var/lib/hadoop-mapreduce/cache/${USER}/tasks
```

And try again

    :::shell
    $ cd ${HADOOP_PREFIX}
    $ hadoop jar share/hadoop/mapreduce/hadoop-mapreduce-examples-2.3.0-cdh5.0.0.jar pi 10 100
        Number of Maps  = 10
        Samples per Map = 100
        2014-04-20 00:36:42.138 java[79538:1703] Unable to load realm info from SCDynamicStore
        14/04/20 00:36:42 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
        Wrote input for Map #0
        Wrote input for Map #1
        Wrote input for Map #2
        Wrote input for Map #3
        Wrote input for Map #4
        Wrote input for Map #5
        Wrote input for Map #6
        Wrote input for Map #7
        Wrote input for Map #8
        Wrote input for Map #9
        Starting Job
        14/04/20 00:36:43 INFO client.RMProxy: Connecting to ResourceManager at /0.0.0.0:8032
        14/04/20 00:36:43 INFO input.FileInputFormat: Total input paths to process : 10
        14/04/20 00:36:43 INFO mapreduce.JobSubmitter: number of splits:10
        14/04/20 00:36:43 INFO mapreduce.JobSubmitter: Submitting tokens for job: job_1397933444099_0001
        14/04/20 00:36:44 INFO impl.YarnClientImpl: Submitted application application_1397933444099_0001
        14/04/20 00:36:44 INFO mapreduce.Job: The url to track the job: http://localdomain.local:8088/proxy/application_1397933444099_0001/
        14/04/20 00:36:44 INFO mapreduce.Job: Running job: job_1397933444099_0001
        14/04/20 00:36:49 INFO mapreduce.Job: Job job_1397933444099_0001 running in uber mode : false
        14/04/20 00:36:49 INFO mapreduce.Job:  map 0% reduce 0%
        14/04/20 00:36:49 INFO mapreduce.Job: Job job_1397933444099_0001 failed with state FAILED due to: Application application_1397933444099_0001 failed 2 times due to AM Container for appattempt_1397933444099_0001_000002 exited with  exitCode: 127 due to: Exception from container-launch: org.apache.hadoop.util.Shell$ExitCodeException:
        org.apache.hadoop.util.Shell$ExitCodeException:
            at org.apache.hadoop.util.Shell.runCommand(Shell.java:505)
            at org.apache.hadoop.util.Shell.run(Shell.java:418)
            at org.apache.hadoop.util.Shell$ShellCommandExecutor.execute(Shell.java:650)
            at org.apache.hadoop.yarn.server.nodemanager.DefaultContainerExecutor.launchContainer(DefaultContainerExecutor.java:195)
            at org.apache.hadoop.yarn.server.nodemanager.containermanager.launcher.ContainerLaunch.call(ContainerLaunch.java:283)
            at org.apache.hadoop.yarn.server.nodemanager.containermanager.launcher.ContainerLaunch.call(ContainerLaunch.java:79)
            at java.util.concurrent.FutureTask$Sync.innerRun(FutureTask.java:334)
            at java.util.concurrent.FutureTask.run(FutureTask.java:166)
            at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1145)
            at java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:615)
            at java.lang.Thread.run(Thread.java:722)


        Container exited with a non-zero exit code 127
        .Failing this attempt.. Failing the application.

Ok, no local job runner anymore. Something is definitely not right yet. Let's examine the logs on HDFS:

    :::shell
    $ hadoop fs -ls /var/log/hadoop-yarn/apps/user/logs/application_1397933444099_0001/
        2014-04-20 00:42:26.267 java[79865:1703] Unable to load realm info from SCDynamicStore
        14/04/20 00:42:26 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
        Found 1 items
        -rw-r-----   1 user supergroup        516 2014-04-20 00:36 /var/log/hadoop-yarn/apps/user/logs/application_1397933444099_0001/10.115.86.114_59329
    $ hadoop fs -cat /var/log/hadoop-yarn/apps/user/logs/application_1397933444099_0001/10.115.86.114_59329
        2014-04-20 00:45:44.565 java[79923:1703] Unable to load realm info from SCDynamicStore
        14/04/20 00:45:44 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
        ??h??׶9?A@???P  VERSIONAPPLICATION_ACL
        MODIFY_APPVIEW_APP APPLICATION_OWNER
        user(&container_1397933444099_0001_01_000001Gstderr48/bin/bash: /bin/java: No such file or directory
        stdout0(&container_1397933444099_0001_02_000001Gstderr48/bin/bash: /bin/java: No such file or directory
        stdout0
            VERSION*(&container_1397933444099_0001_02_000001none?B?Bdata:BCFile.indexnone͎
            data:TFile.indexnone?X66data:TFile.metanone?R???h??׶9?A@???P

Strange format, but we can clearly see the error message in between the garbage `/bin/bash: /bin/java: No such file or directory`.
Looking on the internet I found <a href="http://cloudcelebrity.wordpress.com/2014/01/31/yarn-job-problem-application-application_-failed-1-times-due-to-am-container-for-xx-exited-with-exitcode-127/">this workaround</a> and the <a href="https://issues.apache.org/jira/browse/HADOOP-8717">issue HADOOP-8717</a> describing the problem including a solution. Since I'm more into fixing the problem instead of using a workaround I went for the patch of the start up scripts. The patch in the HADOOP-8717 issue is changing a bit more then needed. We only need to change the `hadoop-config.sh`. Let's find out where to find this script and change it.

```shell
    $ cd /cdh5.0.0
    $ find . -name hadoop-config.sh
        ./hadoop-2.3.0-cdh5.0.0/bin-mapreduce1/hadoop-config.sh
        ./hadoop-2.3.0-cdh5.0.0/libexec/hadoop-config.sh
        ./hadoop-2.3.0-cdh5.0.0/src/hadoop-common-project/hadoop-common/src/main/bin/hadoop-config.sh
        ./hadoop-2.3.0-cdh5.0.0/src/hadoop-mapreduce1-project/bin/hadoop-config.sh
    $ vi ./hadoop-2.3.0-cdh5.0.0/libexec/hadoop-config.sh
```

The script is

```bash
   # On OSX use java_home (or /Library for older versions)
   if [ "Darwin" == "$(uname -s)" ]; then
       if [ -x /usr/libexec/java_home ]; then
           export JAVA_HOME=($(/usr/libexec/java_home))
       else
           export JAVA_HOME=(/Library/Java/Home)
       fi
   fi
    ...
```

but we need to change it into

```bash
    ...
    # On OSX use java_home (or /Library for older versions)
    if [ "Darwin" == "$(uname -s)" ]; then
        if [ -x /usr/libexec/java_home ]; then
            export JAVA_HOME=$(/usr/libexec/java_home)
        else
            export JAVA_HOME=/Library/Java/Home
        fi
    fi
    ...
```

Now let's restart YARN again

```shell
    $ stop-yarn.sh && start-yarn.sh
    $ cd ${HADOOP_PREFIX}
    $ hadoop jar share/hadoop/mapreduce/hadoop-mapreduce-examples-2.3.0-cdh5.0.0.jar pi 10 100
        Number of Maps  = 10
        Samples per Map = 100
        2014-04-20 10:21:56.696 java[80777:1703] Unable to load realm info from SCDynamicStore
        14/04/20 10:22:11 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
        Wrote input for Map #0
        Wrote input for Map #1
        Wrote input for Map #2
        Wrote input for Map #3
        Wrote input for Map #4
        Wrote input for Map #5
        Wrote input for Map #6
        Wrote input for Map #7
        Wrote input for Map #8
        Wrote input for Map #9
        Starting Job
        14/04/20 10:22:12 INFO client.RMProxy: Connecting to ResourceManager at /0.0.0.0:8032
        14/04/20 10:22:12 INFO input.FileInputFormat: Total input paths to process : 10
        14/04/20 10:22:12 INFO mapreduce.JobSubmitter: number of splits:10
        14/04/20 10:22:13 INFO mapreduce.JobSubmitter: Submitting tokens for job: job_1397969462544_0001
        14/04/20 10:22:13 INFO impl.YarnClientImpl: Submitted application application_1397969462544_0001
        14/04/20 10:22:13 INFO mapreduce.Job: The url to track the job: http://localdomain.local:8088/proxy/application_1397969462544_0001/
        14/04/20 10:22:13 INFO mapreduce.Job: Running job: job_1397969462544_0001
        14/04/20 10:22:34 INFO mapreduce.Job: Job job_1397969462544_0001 running in uber mode : false
        14/04/20 10:22:34 INFO mapreduce.Job:  map 0% reduce 0%
        14/04/20 10:22:53 INFO mapreduce.Job:  map 10% reduce 0%
        14/04/20 10:22:54 INFO mapreduce.Job:  map 20% reduce 0%
        14/04/20 10:22:55 INFO mapreduce.Job:  map 30% reduce 0%
        14/04/20 10:22:56 INFO mapreduce.Job:  map 40% reduce 0%
        14/04/20 10:22:57 INFO mapreduce.Job:  map 50% reduce 0%
        14/04/20 10:22:58 INFO mapreduce.Job:  map 60% reduce 0%
        14/04/20 10:23:12 INFO mapreduce.Job:  map 70% reduce 0%
        14/04/20 10:23:13 INFO mapreduce.Job:  map 80% reduce 0%
        14/04/20 10:23:15 INFO mapreduce.Job:  map 90% reduce 0%
        14/04/20 10:23:16 INFO mapreduce.Job:  map 100% reduce 100%
        14/04/20 10:23:16 INFO mapreduce.Job: Job job_1397969462544_0001 completed successfully
        ...
        Job Finished in 64.352 seconds
        Estimated value of Pi is 3.14800000000000000000
```

Wow, we got it to work, didn't we?

#### On to Spark

To experiment with the spark-shell, we return to the local Hadoop configuration:

    :::shell
    $ switch_local_cdh5
    $ spark-shell
        ls: /cdh5.0.0/spark-0.9.0-cdh5.0.0/assembly/target/scala-2.10/: No such file or directory
        ls: /cdh5.0.0/spark-0.9.0-cdh5.0.0/assembly/target/scala-2.10/: No such file or directory
        Failed to find Spark assembly in /cdh5.0.0/spark-0.9.0-cdh5.0.0/assembly/target/scala-2.10/
        You need to build Spark with 'sbt/sbt assembly' before running this program.

The spark shell is assuming that I am running it from the source build or something. But I'm not. Let's see how to fix it.

```shell
    $ vi /cdh5.0.0/spark-0.9.0-cdh5.0.0/bin/spark-shell
```

```bash
    #here we see it's calling spark-class
    else
        $FWDIR/bin/spark-class $OPTIONS org.apache.spark.repl.Main "$@"
    fi
```

```shell
    $ vi /cdh5.0.0/spark-0.9.0-cdh5.0.0/bin/spark-class
```

```bash
    ...
    if [ ! -f "$FWDIR/RELEASE" ]; then
        # Exit if the user hasn't compiled Spark
        num_jars=$(ls "$FWDIR"/assembly/target/scala-$SCALA_VERSION/ | grep "spark-assembly.*hadoop.*.jar" | wc -l)
        jars_list=$(ls "$FWDIR"/assembly/target/scala-$SCALA_VERSION/ | grep "spark-assembly.*hadoop.*.jar")
        if [ "$num_jars" -eq "0" ]; then
            echo "Failed to find Spark assembly in $FWDIR/assembly/target/scala-$SCALA_VERSION/" >&2
            echo "You need to build Spark with 'sbt/sbt assembly' before running this program." >&2
            exit 1
        fi
        if [ "$num_jars" -gt "1" ]; then
            echo "Found multiple Spark assembly jars in $FWDIR/assembly/target/scala-$SCALA_VERSION:" >&2
            echo "$jars_list"
            echo "Please remove all but one jar."
            exit 1
        fi
    fi
    ...
```

The bash scripts are looking for evidence that we're running a release version (by looking at the RELEASE file); it then searches for some jar with assembly in the name. Let's see if we have such a jar file.

    :::shell
    $ find /cdh5.0.0 -name "*assembly*jar"
        /cdh5.0.0/spark-0.9.0-cdh5.0.0/spark-assembly_2.10-0.9.0-cdh5.0.0-hadoop2.3.0-cdh5.0.0.jar

It is there, but not in the place the `spark-class` script is searching; we only need to change the `spark-class` script to look in the right place and add the RELEASE file.

```shell
    $ touch /cdh5.0.0/spark-0.9.0-cdh5.0.0/RELEASE
    $ vi /cdh5.0.0/spark-0.9.0-cdh5.0.0/bin/spark-class
```

```bash
    ...
    if [ ! -f "$FWDIR/RELEASE" ]; then
        # Exit if the user hasn't compiled Spark
        num_jars=$(ls "$FWDIR"/assembly/target/scala-$SCALA_VERSION/ | grep "spark-assembly.*hadoop.*.jar" | wc -l)
        jars_list=$(ls "$FWDIR"/assembly/target/scala-$SCALA_VERSION/ | grep "spark-assembly.*hadoop.*.jar")
        if [ "$num_jars" -eq "0" ]; then
            num_jars=$(ls "$FWDIR"/ | grep "spark-assembly.*hadoop.*.jar" | wc -l)
            jars_list=$(ls "$FWDIR"/ | grep "spark-assembly.*hadoop.*.jar")
            if [ "$num_jars" -eq "0" ]; then
                echo "Failed to find Spark assembly in $FWDIR/assembly/target/scala-$SCALA_VERSION/" >&2
                echo "You need to build Spark with 'sbt/sbt assembly' before running this program." >&2
                exit 1
            fi
        fi
        if [ "$num_jars" -gt "1" ]; then
            echo "Found multiple Spark assembly jars in $FWDIR/assembly/target/scala-$SCALA_VERSION:" >&2
            echo "$jars_list"
            echo "Please remove all but one jar."
            exit 1
        fi
    fi
    ...
```

Try again.

    :::shell
    $ spark-shell
        ls: /cdh5.0.0-blog/spark-0.9.0-cdh5.0.0/jars/spark-assembly*.jar: No such file or directory
        Error: Could not find or load main class org.apache.spark.repl.Main

It's right again. Somewhere else we are making the wrong assumption on the structure of our directory tree. But where?

```shell
    $ cd spark-0.9.0-cdh5.0.0/bin
    $ grep 'jars/spark-assembly' *
        compute-classpath.sh:    ASSEMBLY_JAR=`ls "$FWDIR"/jars/spark-assembly*.jar`
    $ vi compute-classpath.sh
```

```bash
    # remove the /jars in the ASSEMBLY_JAR variable, and try again
```

```shell
    $ cd ../../
    $ spark-shell
        Exception in thread "main" java.lang.NoClassDefFoundError: org/apache/hadoop/fs/FSDataInputStream
            at org.apache.spark.repl.SparkIMain.<init>(SparkIMain.scala:93)
            at org.apache.spark.repl.SparkILoop$SparkILoopInterpreter.<init>(SparkILoop.scala:174)
            at org.apache.spark.repl.SparkILoop.createInterpreter(SparkILoop.scala:193)
            at org.apache.spark.repl.SparkILoop$$anonfun$process$1.apply$mcZ$sp(SparkILoop.scala:887)
            at org.apache.spark.repl.SparkILoop$$anonfun$process$1.apply(SparkILoop.scala:883)
            at org.apache.spark.repl.SparkILoop$$anonfun$process$1.apply(SparkILoop.scala:883)
            at scala.tools.nsc.util.ScalaClassLoader$.savingContextLoader(ScalaClassLoader.scala:135)
            at org.apache.spark.repl.SparkILoop.process(SparkILoop.scala:883)
            at org.apache.spark.repl.SparkILoop.process(SparkILoop.scala:981)
            at org.apache.spark.repl.Main$.main(Main.scala:31)
            at org.apache.spark.repl.Main.main(Main.scala)
        Caused by: java.lang.ClassNotFoundException: org.apache.hadoop.fs.FSDataInputStream
            at java.net.URLClassLoader$1.run(URLClassLoader.java:366)
            at java.net.URLClassLoader$1.run(URLClassLoader.java:355)
            at java.security.AccessController.doPrivileged(Native Method)
            at java.net.URLClassLoader.findClass(URLClassLoader.java:354)
            at java.lang.ClassLoader.loadClass(ClassLoader.java:423)
            at sun.misc.Launcher$AppClassLoader.loadClass(Launcher.java:308)
            at java.lang.ClassLoader.loadClass(ClassLoader.java:356)
            ... 11 more
```

We're getting close. Spark can't find our Hadoop jars. To fix that we add some `classpath` setting to the `compute-classpath.sh` script:

```shell
    $ vi spark-0.9.0-cdh5.0.0/bin/compute-classpath.sh
```

```bash
    ...
    ASSEMBLY_JAR=`ls "$FWDIR"/spark-assembly*.jar`

    # Adding hadoop classpath references here
    CLASSPATH="$CLASSPATH:$HADOOP_PREFIX/share/hadoop/common/*:$HADOOP_PREFIX/share/hadoop/common/lib/*"
    CLASSPATH="$CLASSPATH:$HADOOP_PREFIX/share/hadoop/mapreduce/*"
    CLASSPATH="$CLASSPATH:$HADOOP_PREFIX/share/hadoop/mapreduce/lib/*"
    CLASSPATH="$CLASSPATH:$HADOOP_PREFIX/share/hadoop/yarn/*"
    CLASSPATH="$CLASSPATH:$HADOOP_PREFIX/share/hadoop/yarn/lib/*"
    CLASSPATH="$CLASSPATH:$HADOOP_PREFIX/share/hadoop/hdfs/*"
    CLASSPATH="$CLASSPATH:$HADOOP_PREFIX/share/hadoop/hdfs/lib/*"
    CLASSPATH="$CLASSPATH:$SPARK_HOME/lib/*"
```

```shell
    $ spark-shell
        SLF4J: Class path contains multiple SLF4J bindings.
        ...
        2014-04-20 09:48:25,238 INFO  [main] spark.HttpServer (Logging.scala:logInfo(49)) - Starting HTTP Server
        2014-04-20 09:48:25,302 INFO  [main] server.Server (Server.java:doStart(266)) - jetty-7.6.8.v20121106
        2014-04-20 09:48:25,333 INFO  [main] server.AbstractConnector (AbstractConnector.java:doStart(338)) - Started SocketConnector@0.0.0.0:62951
        Welcome to
              ____              __
             / __/__  ___ _____/ /__
            _\ \/ _ \/ _ `/ __/  '_/
           /___/ .__/\_,_/_/ /_/\_\   version 0.9.0
              /_/

        Using Scala version 2.10.3 (Java HotSpot(TM) 64-Bit Server VM, Java 1.7.0_15)
        Type in expressions to have them evaluated.
        Type :help for more information.
        ...
        Created spark context..
        Spark context available as sc.

        scala>
```

And we're in!!

Now as a final test we check if spark will work on our pseudo distributed Hadoop config

    :::shell
    $ switch_pseudo_cdh5
    $ start-dfs.sh
    $ start-yarn.sh
    $ hadoop fs -mkdir /sourcedata
    $ hadoop fs -put somelocal-textfile.txt /sourcedata/sometext.txt
    $ spark-shell
        scala> val file = sc.textFile("/sourcedata/sometext.txt")
               file.take(5)

               res1: Array[String] = Array("First", "five lines", "of", "the", "textfile" )

Works like a charm. I hope this was a useful exercise. It was for me at least.


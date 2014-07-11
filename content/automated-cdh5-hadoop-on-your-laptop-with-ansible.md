Title: Automated install of CDH5 Hadoop on your laptop with Ansible
Date: 2014-07-07 22:00
Slug: automated-cdh5-hadoop-on-your-laptop-with-ansible
Author: Kris Geusebroek
Excerpt: In my previous blog I outlined the steps to take to install the CDH5 Hadoop distribution on my laptop. For some of my colleagues this wasn't straightforward and easy enough. so I decided to automated the steps described there. And since we use Ansible a lot to automated cluster installments I used Ansible to install CDH5 on my laptop too.
Template: article
Latex:

Installing CDH5 from the tarball distribution is not a really difficult, but getting the pseudo-distributed configuration right is all but straightforward. And since there are a few bugs that need fixing and configuring that needs to be done I automated it.

### Automating the steps

All steps that need to be automated are described in my previous blog: <a href="local-and-pseudo-distributed-cdh5-hadoop-on-your-laptop.html" target="_blank">Local and Pseudo-distributed CDH5 Hadoop on your laptop</a>

All I needed to do was write some Ansible configuration scripts to perform these steps. For now I automated the steps to download and install CDH5, Spark, Hive, Pig and Mahout. Any extra packages are left as an exercise to the reader. I welcome your pull requests.

### configuration

Ansible needs some information from the user about the directory to install the software into. I first tried to use ansible's vars_prompt module. this kind of works, but the scope of the variable is within the same yml file only. And I need it to be a global variable. After testing several of ansibles ways to provide variables I decided upon using a bash script to get the user's input and provide ansible with that information throught the ```--extra-vars``` commandline option.

Next to that we want to use ansible to run a playbook. This means that we need to have the ```${ANSIBLE_HOME}``` environment variable to be set. I asume ansible is installed and the environment will be setup correctly in the .bash_profile of the user, so we use the command ```source $HOME/.bash_profile``` to make sure the script is able to run ansible.

### Getting the install scripts

Getting the install scripts is done by issuing a git clone command:

    :::shell
    $ git clone git@github.com:krisgeus/ansible_local_cdh_hadoop.git


### Install

Installing the software has become a single line command:

    :::shell
    $ start-playbook.sh

The script will ask the user for a directory to install the software into. Then it will start to download the packages into the ```$HOME\.ansible-downloads``` directory. And it will unpack into the install directory the user provided.

In the install directory the script will create a bash_profile addon to set the correct aliasses.
    
    :::shell
    $ source ${INSTALL_DIR}/.bash_profile_hadoop

### Testing Hadoop in local mode

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

Running a MapReduce job should also work out of the box.

    :::shell
    $ cd $HADOOP_PREFIX

    $ hadoop jar share/hadoop/mapreduce/hadoop-mapreduce-examples-2.3.0-cdh5.0.2.jar pi 10 100

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


### Testing Hadoop in pseudo-distributed mode

    :::shell
    $ switch_psuedo_cdh5
    $ hadoop namenode -format
    $ start-dfs.sh
    $ hadoop fs -ls /
    $ hadoop fs -mkdir /bogus
    $ hadoop fs -ls /
        2014-04-19 19:46:32.233 java[78176:1703] Unable to load realm info from SCDynamicStore
        14/04/19 19:46:32 WARN util.NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-
        java classes where applicable
        Found 1 items
        drwxr-xr-x   - user supergroup          0 2014-04-19 19:46 /bogus


Ok HDFS is working, now on to a MapReduce job

    :::shell
    $ start-yarn.sh
        starting yarn daemons
        starting resourcemanager, logging to /cdh5.0.0/hadoop-2.3.0-cdh5.0.2/logs/yarn-user-resourcemanager-localdomain.local.out
        Password:
        localhost: starting nodemanager, logging to /cdh5.0.0/hadoop-2.3.0-cdh5.0.2/logs/yarn-user-nodemanager-localdomain.local.out

    $ cd $HADOOP_PREFIX
    $ hadoop jar share/hadoop/mapreduce/hadoop-mapreduce-examples-2.3.0-cdh5.0.2.jar pi 10 100
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

### Testing Spark in local mode

    :::shell
    $ switch_local_cdh5
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

And we're in!!

### Testing Spark in pseudo-distributed mode
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



The current version of the ansible scripts are set to install the CDH version 5.0.2 packages. When a new version becomes available this version is easily changed by updating the vars/common.yml Yaml file.

If you have created ansible files to add other packages I welcome you to send me a pull request.
Title: Hive, Impala, JDBC and Kerberos
Date: 2014-08-08 15:32
Slug: jdbc-hive-impala-kerberos
Author: Renald Buter
Excerpt: Connect to Hive or Impala via JDBC with a Hadoop cluster that uses Kerberos.
Template: article
Latex:

## Hive, Impala, JDBC and Kerberos

<span class="lead">If your cluster is protected with Kerberos and you want to connect to a Hive
repository from a computer that is not part of that cluster, you need to jump through some
hoops</span>

Hive and Impala can be helpful technology to build your data processing pipelines, especially in
organisations that still do a lot with SQL. Often, these organisations use Kerberos to avoid
unpriviliged access to their data. There are different ways to interact with Hive or Impala. In the
webbrowser you can use Hue, while on the command line of one of your nodes in the cluster, you can
use Hive CLI, Beeline or Impala shell. These ways of interacting with Hive and Impala have been set
up by system administrators to work with Kerberos, so you do not have to worry that. However,
sometimes you want to connect to the data repositories from a computer not part of the cluster, for
example through JDBC. But since our data sources are secured via Kerberos, we cannot "simply"
establish a JDBC connection and we need to configure Kerberos on our laptop as well. It is not
extremely difficult to do and your Mac already has Kerberos installed. Still, we found that it was
not trivial either to get everything right. So, we wrote up this short blog post on how to establish
a JDBC connection to Hive and Impala running in a Kerberos secured Hadoop cluster, from a computer
not part of the actual cluster. Note that we will be using a Mac in this blog, but most of it should
apply to computers running other operating systems as well.

## Kerberos

We start by giving a quick overview of Kerberos. A better introduction to Kerberos and its use with
Hadoop is given in detail http://blog.godatadriven.com/kerberos_kdc_install.html, so head over there
for more background material.

Kerberos is a way to mutually establish identities over an unreliable network in a secure way. It
allows you to show that it *really is you* at the other side of the channel and not some imposter.
It also assures *you* that you are really connecting to the service that you requested and not some
fake one that is after your passwords. At the same time Kerberos encrypts the communication, so you
do not have to worry about somebody else eavesdropping on your conversation with the service.

Kerberos works by creating tickets. The system uses these tickets to create and send additional
tickets. In the case of getting access to Impala or Hive, this works as follows.

 1. First we apply for a ticket that shows that we really are who we say we are.
 2. This ticket can then be used to apply for additional tickets, which give us access to services.
 3. Each user has a unique identifier (which is called a principal in Kerberos' terms), which you can
use to apply for a ticket.

Note that tickets are applicable only within a specific application domain, which is called a
/realm/ in the Kerberos system. 

## Getting the initial ticket.

We assume that our Mac laptop is on a LAN that has access to the cluster and (of course) is not part
of the cluster itself. As we noted above, the first thing we have to do is to get the ticket that
identifies us. For that, we use the `kinit` command, which needs to known how and where Kerberos is
set up. This information is usually available in `/etc/krb5.conf` on some node in your cluster. This
configuration file contains information about the /realm/s and the default values used in your
system. Seee http://blog.godatadriven.com/kerberos_kdc_install.html for an example of such a
configuration.

So, we start by getting a copy of the `/etc/krb5.conf` from some node in you cluster:

    :::console
    $ scp mydatanode:/etc/krb5.conf .

Using that configuration file, we can request a ticket in the `MYREALM` realm.

    :::console
    $ KRB5_CONFIG=./krb5.conf kinit user@MYREALM

After entering the (correct) password, you will be granted a ticket for the `MYREALM` realm. This
ticket will be the basis for accessing the remote Hive and Impala services.

## Getting the jars

To access Hive and Impala using JDBC, we also have to have the required jars on our classpath. We
assume here, that there is no local Hadoop installation on our laptop, so we will need to get the
required jars from nodes that are part of the Hadoop cluster we are going to access. There is some
information on what the list required jars web is, like for example at
http://cwiki.apache.org/confluence/display/Hive/HiveServer2+Clients, but these lists unfortunately
are incomplete. However, after some trial and error we found the following list be the minimal set
of jars that is required to establish a JDBC connection to both Hive and Impala. Most of the jars
can be found on your Hadoop cluster, in the `hive/lib` directory of your parcels root, while some
need to be copied from the `hadoop/client-0.20` directory. The following shell code can be used to
copy jars to a local `lib` directory. Note that you need to replace `user`, `mydatanode`,
`CDHVERSION` and `PARCELROOT` to your own values.

    :::sh
    mkdir lib

    PARCELROOT=/opt/cloudera
    CDHVERSION=CDH-5.1.0-1.cdh5.1.0.p0.53
    hivejars=(
          hive-jdbc\*.jar 
          hive-service\*.jar 
          libfb303-0.9.0.jar
          libthrift-0.9.0\*.jar 
          log4j-1.2.16.jar 
          commons-collections-\*.jar
          guava-11.0.2.jar
          hive-exec\*.jar) 
    for i in $hivejars; do
        scp user@mydatanode:/$PARCELROOT/parcels/$CDHVERSION/lib/hive/lib/$i lib/
    done

    hadoopjars=(
          hadoop-core\*.jar
          hadoop-common\*.jar
          hadoop-auth\*.jar
          httpclient\*.jar # needed since CDH-5
          httpcore\*.jar   # needed since CDH-5
          slf4j-api\*.jar
          slf4j-log4j12\*jar
          commons-configuration\*.jar
          commons-logging\*.jar)
    for i in $hadoopjars; do
        scp user@mydatanode:/$PARCELROOT/parcels/$CDHVERSION/lib/hadoop/client-0.20/$i lib/
    done
        
After that, you can set up you classpath to include the jars in the `lib` directory, for example
like this:

    :::sh
    for i in lib/*.jar; do CLASSPATH=$CLASSPATH:$i; done

or

    :::zsh
    for i in lib/*.jar; do classpath=($classpath $i); done

if you are using zsh.

## Fire up the JVM

Now we are ready to fire up a JVM. We will use Scala for that, but you could use
[other](http://http://clojure.org) [jvm-based](http://groovy.codehaus.org)
[languages](http://www.jruby.org/) of course. To let the JVM know which Kerberos parameters to use,
we need to supply these on the command line using the `-D` argument of both scala and java.

    :::console
    scala -Djava.security.krb5.realm=MYREALM \
          -Djava.security.krb5.kdc=kdc-host.mydomain.org \
          -Djava.security.krb5.conf=`pwd`/krb5.conf

Note that we use `pwd` to get the absolute path to the `krb5.conf` file.

Once we are on the Scala REPL, we can make a connection, for which we need a JDBC url. This url
contains the hostname (or IP address) of some node in our cluster and a port number: use port 10000
for the Hive2 server and port 21050 for the Impala server. We can supply an optional name of the
database to connect to: in our example, we connect to the "default" database. And since we have to
work with Kerberos, the url needs to contain information on the hostname of the server that is
running HiveServer2 that is listed as the `principal` in your `krb5.conf`.

    :::scala
    import java.sql.{Connection, DriverManager, ResultSet => RS, Statement}

    java.lang.Class.forName("org.apache.hive.jdbc.HiveDriver")
    val hive = "hiveserver.mydomain.org"
    val node = "somenode"
    val hive_port = 10000
    val impala_port = 21050
    val db = "default"
    
    val url = s"jdbc:hive2://$node:$hive_port/$db;principal=hive/$hive@MYREALM"
    val con = DriverManager.getConnection(url)

In the above code, we use the `s""` construct to get string interpolation in Scala. And if all went
well, the last line will return without errors and we can start to execute queries.

### Updating the security strength

There is actually one caveat: Java on Mac OSX is installed by default with a *strong* strength
security policy, but to work with Kerberos we need *unlimited* strength. So, when you see an error
such as the one below, you will have to update the policy.

    :::console
    javax.security.sasl.SaslException: GSS initiate failed [Caused by GSSException: No valid credentials provided (Mechanism level: Illegal key size)]
           at com.sun.security.sasl.gsskerb.GssKrb5Client.evaluateChallenge(GssKrb5Client.java:212)
           at org.apache.thrift.transport.TSaslClientTransport.handleSaslStartMessage(TSaslClientTransport.java:94)
           at org.apache.thrift.transport.TSaslTransport.open(TSaslTransport.java:253)
           at org.apache.thrift.transport.TSaslClientTransport.open(TSaslClientTransport.java:1)
           at org.apache.hadoop.hive.thrift.client.TUGIAssumingTransport$1.run(TUGIAssumingTransport.java:52)
           at org.apache.hadoop.hive.thrift.client.TUGIAssumingTransport$1.run(TUGIAssumingTransport.java:49)
           at java.security.AccessController.doPrivileged(Native Method)
           at javax.security.auth.Subject.doAs(Subject.java:415)
           at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:1408)

To update the policy, you can download files for
[Java 7](http://www.oracle.com/technetwork/java/javase/downloads/jce-7-download-432124.html) or
[Java 6](http://www.oracle.com/technetwork/java/javase/downloads/jce-6-download-429243.html). Be
careful not to install (as we did) the Java 6 policy files if you are using Java 7 (and vice versa),
or else things will (still) not work.

For example, on a Macbook Pro where the UnlimitedJCEPolicy.zip was downloaded into `~/Downloads` and
that has JDK 1.7 installed, the following lines on the command line would install the unlimited
strength policy files.

    :::sh
    cd ~/Downloads
    unzip UnlimitedJCEPolicy.zip
    cd /Library/Java/JavaVirtualMachines/jdk1.7/Contents/Home/jre/lib/security
    # we need to be root to change something in this system directory
    sudo su
    cp local_policy.jar local_policy.jar-old
    cp US_export_policy.jar US_export_policy.jar-old
    cp ~/Downloads/UnlimitedJCEPolicy/local_policy.jar .
    cp ~/Downloads/UnlimitedJCEPolicy/US_export_policy.jar .
    exit

Once you have done that, restart scala (with the `-D` arguments we showed above) and try to connect
again.

### Testing the connection

Once the connection has been established, we can do some serious scala with the results!
For example, we can create mapping from database name to the tables in that database.

    :::scala
    type SS = Set[String]

    def exec(sql: String): ResultSet = con.createStatement.executeQuery(sql)

    def toSet(sql: String): SS = {
      def app(rs: ResultSet, set: SS = Set.empty): SS =
        if (rs.next) { app(rs, set + rs.getString(1)) } else { set }

      app(exec(sql))
    }

    def tables(t: String): SS = toSet(s"show tables from $t")
    val dbs = toSet("show databases")

    val dbStructure = dbs.foldLeft(Map[String, SS]()) { (mm, t) => mm + (t -> tables(t)) }

Have fun with Hive, Impala, Kerberos and JDBC!

Title: Neo4j HA on a Raspberry pi cluster
Date: 2016-04-18 20:48
Slug: neo4j-ha-on-a-raspberry-pi
Author: Ron van Weverwijk
Excerpt: How to create a Neo4j HA cluster including a proxy server on a Raspberry pi cluster
Template: article
Latex:

<span class="lead">
In this blog we will show you how easy it is to create a Neo4j HA cluster on a Raspberry pi cluster including a proxy server in front to get most out of the setup. You might think: "Why would you install a Neo4j cluster on a Raspberry?" Well, to be honest: Because it's fun and because we can ;).
</span>

Personally, I am known to be a big fan of Neo4j, simply because it is a great graph-database. Most of the times I work with just a single instance. Most production systems however run in a High Availability setup. In the past period I have experimented with the set-up of such a Raspberry pi cluster. In this article I'll share my learnings during this experiment.

To start building our cluster, we needed some hardware. I've used:

- 4 Raspberry Pi 2 Model B 1GB
- 4 Transcend 16GB Class 10 MicroSDHC
- 1 8-Port Gigabit Switch
- 1 4-Port USB 3.0 Hub
- Some wires and cases

<div class="row">
  <div class="span5">
    <img alt="Bunch of raspberry stuff" src="static/images/neo4j-ha/raspberry_stuff.JPG">
    <p>Bunch of raspberry stuff</p>
  </div>
  <div class="span5">
    <img alt="Raspberry pi cluster" src="static/images/neo4j-ha/raspberry_pi_cluster.JPG">
    <p>Raspberry pi cluster</p>
  </div>
</div>

### How to shard a graph

A few years ago, the NoSql / [Hadoop](/http://www.godatadriven.com/hadoop "Hadoop") hype was at its peak. Companies saw a drastic increase in the amount of data they stored. The then available solutions couldn't cope with these amounts of data or complexity. A lot of the NoSql solutions solved the issue around high volume by offering a sharding solution for data. This works great for disconnected data. Key-value stores and document stores like Redis or Mongo db store records in partitions and can easily scale-up horizontally.

In image 3 you can see what would happen with a graph if you would shard it in the same way. Neo4j focusses on delivering a solution for a fast online graph-database. If you would query data that is stored on different machines it is a near-impossible problem to make it perform fast.

Thereby the solution Neo4j HA offers is a full replicated cluster, see image 4. Every Neo4j instance in the cluster will contain the complete graph. The HA solution will make sure all instances will remain in sync. 

<div class="row">
  <div class="span5">
    <img alt="Bunch of raspberry stuff" src="static/images/neo4j-ha/sharding.png">
    <p>Image 3</p>
  </div>
  <div class="span5">
    <img alt="Raspberry pi cluster" src="static/images/neo4j-ha/replication.png">
    <p>Image 4</p>
  </div>
</div>

### Prepare the Raspberry
Back to the cluster. Before we can create a Neo4j cluster we need to install an OS on Raspberry pi's. To install Raspbian OS, you can follow [this guide](https://www.raspberrypi.org/documentation/installation/installing-images/). After this you can boot the Raspberry and configure some basic things on the pi with the ```sudo raspi-config``` command. Things you probably want to configure are:

- hostname
- expand the filesystem (by default the partition will only be 2GB, but we have 16GB available)

### Neo4j setup

Setting up a Neo4j cluster is quite easy. You only need to change 6 properties in 2 files and you're done:

The following property files need to be changed on all cluster instances.

neo4j-server.properties
    
    :::python
    # Database mode
    # Allowed values:
    # HA - High Availability
    # SINGLE - Single mode, default.
    # To run in High Availability mode, configure the neo4j.properties config file, then uncomment this line:
    org.neo4j.server.database.mode=HA

    # Let the webserver only listen on the specified IP. Default is localhost (only
    # accept local connections). Uncomment to allow any connection. Please see the
    # security section in the neo4j manual before modifying this.
    org.neo4j.server.webserver.address=0.0.0.0

neo4j.properties

    :::python
    # Uncomment and specify these lines for running Neo4j in High Availability mode.
    # See the High availability setup tutorial for more details on these settings
    # http://neo4j.com/docs/2.3.1/ha-setup-tutorial.html
    
    # ha.server_id is the number of each instance in the HA cluster. It should be
    # an integer (e.g. 1), and should be unique for each cluster instance.
    ha.server_id=1

    # ha.initial_hosts is a comma-separated list (without spaces) of the host:port
    # where the ha.cluster_server of all instances will be listening. Typically
    # this will be the same for all cluster instances.
    ha.initial_hosts=192.168.2.8:5001,192.168.2.7:5001,192.168.2.9:5001
    # IP and port for this instance to listen on, for communicating cluster status
    # information iwth other instances (also see ha.initial_hosts). The IP
    # must be the configured IP address for one of the local interfaces.
    ha.cluster_server=192.168.2.8:5001
    
    # IP and port for this instance to listen on, for communicating transaction
    # data with other instances (also see ha.initial_hosts). The IP
    # must be the configured IP address for one of the local interfaces.
    ha.server=192.168.2.8:6001
    
For a full instruction take a look at [the Neo4j website](http://neo4j.com/docs/stable/ha-setup-tutorial.html)

If everything is setup correctly and the neo4j instances are started (```$NEO4J_HOME/bin/neo4j start```) you should be able to excecute the query ```:sysinfo``` in the webconsole. In our case: [http://raspberrypi_2:7474/browser/](http://raspberrypi_2:7474/browser/). The following images show the result for both the Master and a Slave instance.
<div class="row">
  <div class="span5">
    <img alt="Neo4j master" src="static/images/neo4j-ha/neo4j_master_info.png">
    <p>:sysinfo master</p>
  </div>
  <div class="span5">
    <img alt="Neo4j slave" src="static/images/neo4j-ha/neo4j_slave_info.png">
    <p>:sysinfo slave</p>
  </div>
</div>


### HA Proxy setup
Now that we have our Neo4j cluster up and running it's time to take a look at the Proxy. For this setup I've used HA Proxy. The main reason is that it has been described very well in [a blog post by Stefan Armbruster](http://blog.armbruster-it.de/2015/08/neo4j-and-haproxy-some-best-practices-and-tricks/) 

    :::python
    global
    daemon
    maxconn 60

    defaults
        mode http
        timeout connect 5000ms
        timeout client 50000ms
        timeout server 50000ms

    frontend http-in
        bind *:8090
        default_backend neo4j-all

    backend neo4j-all
        option httpchk GET /db/manage/server/ha/available HTTP/1.0\r\nAuthorization:\ Basic\ bmVvNGo6dGVzdA==
            server s1 192.168.2.8:7474 maxconn 10 check
            server s2 192.168.2.7:7474 maxconn 10 check
            server s3 192.168.2.9:7474 maxconn 10 check

    listen admin
        bind *:8080
        stats enable
        stats realm   Haproxy\ Statistics
        stats auth    admin:123

With the configuration above we will accept 60 connections to the HA Proxy. The load will be spread round robin to all 3 Neo4j instances.

There is a lot that we can improve on the configuration above. But I want to add at least one improvement. While every Neo4j instance in the Cluster is able to handle write operations, it is advised ([http://neo4j.com/docs/stable/ha-how.html](http://neo4j.com/docs/stable/ha-how.html)) to perform write operations to the Master instance. There are some different ways to detect a write operation. On a REST api, POST, PUT and DELETE operations are a good indication of a write operation. Neo4j requests are always a POST operation, so this doesn't work. We could also inspect the query and search for keywords like: CREATE, MERGE, DELETE, SET, REMOVE. But in my opinion this is not the responsibility of the load balancer. I prefer to handle this functionality in HA Proxy with a HTTP header to indicate the write operation from the client. In this way the configuration of the loadbalancer can be very clean.

    :::python
    frontend http-in
        bind *:8090
        acl write_hdr hdr_val(X-Write) eq 1
        use_backend neo4j-master if write_hdr
        default_backend neo4j-all

    backend neo4j-master
        option httpchk GET /db/manage/server/ha/master HTTP/1.0\r\nAuthorization:\ Basic\ bmVvNGo6dGVzdA==
            server s1 192.168.2.8:7474 maxconn 10 check
            server s2 192.168.2.7:7474 maxconn 10 check
            server s3 192.168.2.9:7474 maxconn 10 check

The acl will check for the X-Write header to be present. If that header is present we ```use_backend``` neo4j-master. In all other cases we will follow the fallback to the ```default_backend```.

To identify the Master instance we can use the Neo4j endpoint: ```/db/manage/server/ha/master```. This endpoint will return a HTTP 200 response if this machine is the master and a 404 in case of a slave instance.

In the image below you can see the HA Proxy statistics page.

![HA Proxy](/static/images/neo4j-ha/haproxy.png)

For the full explanation of HA Proxy take a look at the [HAProxy Configuration Manual]("http://cbonte.github.io/haproxy-dconv/configuration-1.6.html")


### Let's test (and play)

Now that we have a Neo4j cluster and a loadbalancer in place we can start playing with setup. One important part in the HA Proxy configuration is the ```check``` option. This will constantly check with the ```httpchk``` option if an instance is available or is still the master, making sure that all requests will be routed correctly in case of the restart of an instance.

In the following two images you can see this in action. The first image shows that all instances are up and running. On a shutdown of instance 2 you can see that the second line has become red in image two.

<div class="row">
  <div class="span5">
    <img alt="Neo4j master" src="static/images/neo4j-ha/haproxy_3.png">
    <p>All 3 instances running</p>
  </div>
  <div class="span5">
    <img alt="Neo4j slave" src="static/images/neo4j-ha/haproxy_2.png">
    <p>1 instance down</p>
  </div>
</div>

### Ansible
Because I don't like to repeat myself I've used Ansible to provision the Raspberry pi's.
The complete project can be found on [my github repo](https://github.com/rweverwijk/neo4j-cluster-ansible), but I will share some parts here.

With ansible you can make sure that config files are present on a server. You can also check if the config files are different than the ones already on the server. And take an action when the config is changed: for example restart to make the config active.

    :::python
    - name: Copy neo4j config templates
      template: src=configs/{{ item }} dest={{ install_dir }}/neo4j-enterprise-{{ neo4j_version }}/conf/{{ item }}
      with_items:
        - neo4j-http-logging.xml
        - neo4j-server.properties
        - neo4j-wrapper.conf
        - neo4j.properties
        - arbiter-wrapper.conf
        - jmx.access
        - jmx.password
      register: config
      
    - name: Start Neo4j
      command: ./neo4j restart
      args:
        chdir: "{{ install_dir }}/neo4j-enterprise-{{ neo4j_version }}/bin"
      when: config.changed


The following example will show how you can create the neo4j.properties.

    :::python
    ha.server_id={{play_hosts.index(inventory_hostname) +1}}
    
    ha.initial_hosts={%- for host in groups['neo4j-cluster']|sort -%}
    {{ hostvars[host]['ansible_eth0']['ipv4']['address'] }}:5001{% if not loop.last %},{% endif %}
    {% endfor %}

This will result in:
    
    :::python

    ha.server_id=1

    ha.initial_hosts=192.168.2.8:5001,192.168.2.7:5001,192.168.2.9:5001

The ```{%-``` will make sure all the hosts will be on the same line.

HAProxy config

    :::python
    backend neo4j-all
        option httpchk GET /db/manage/server/ha/available HTTP/1.0\r\nAuthorization:\ Basic\ bmVvNGo6dGVzdA==
        {% for host in groups['neo4j-cluster']|sort %}
            server s{{ loop.index }} {{ hostvars[host]['ansible_eth0']['ipv4']['address'] }}:7474 maxconn 10 check
        {% endfor %}


Will result in:

    :::python
    backend neo4j-all
        option httpchk GET /db/manage/server/ha/available HTTP/1.0\r\nAuthorization:\ Basic\ bmVvNGo6dGVzdA==
            server s1 192.168.2.8:7474 maxconn 10 check
            server s2 192.168.2.7:7474 maxconn 10 check
            server s3 192.168.2.9:7474 maxconn 10 check

### Summary
As you could see, we only needed to change 6 properties in the Neo4j configuration. Add a load balancer with around 30 lines to have build a Neo4j cluster. I think it’s quite amazing!

It will cost me more time to explain how to build a Neo4j cluster than actually implement one.

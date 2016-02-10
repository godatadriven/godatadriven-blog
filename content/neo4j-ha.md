Title: Neo4j HA on a Raspberry pi cluster
Date: 2016-02-05 17:00
Slug: neo4j-ha
Author: Ron van Weverwijk
Excerpt: Neo4j is a great graph-database. Most of the times I work with with just a single instance. Most production systems run in a High Available setup though. In this blog we will show how easy it is to create a Neo4j HA cluster including a proxy server infront to get most out of the setup.
Template: article
Latex:

<span class="lead">
Neo4j is a great graph-database. Most of the times I work with with just a single instance. Most production systems run in a High Available setup though. In this blog we will show how easy it is to create a Neo4j HA cluster on a Raspberry pi cluster including a proxy server infront to get most out of the setup. Questions will raise: "Why whould you install a Neo4j cluster on a Raspberry?". Actually: Because it's fun and we can ;)
</span>

To start building your cluster you will offcourse need some hardware. I've used:

- 4 Raspberry Pi 2 Model B 1GB- 4 Transcend 16GB Class 10 MicroSDHC- 1 8-Port Gigabit Switch- 1 4-Port USB 3.0 Hub
- Some wires and cases

<div class="row">
  <div class="span5">
    <img alt="Bunch of raspberry stuff" src="static/images/neo4j-ha/IMG_0392.JPG">
  </div>
  <div class="span5">
    <img alt="Raspberry pi cluster" src="static/images/neo4j-ha/IMG_0389.JPG">
  </div>
</div>


*Looks great right?* 

### Prepare the raspberry
To install Raspbian you can follow [this guide](https://www.raspberrypi.org/documentation/installation/installing-images/). After this you can boot the raspberry and configure some basic things on the py with the ```sudo raspi-config``` command. Things you proberbly want to configure:

- hostname
- expand the filesystem (by default only)

### How to shard a graph

A few years ago the IT industry was in de middle of the NoSql hype. Companies saw that they where storing more and more data. A lot of the NoSql solutions had a focus on solving that problem. Offering a sharding sollution for high volume data. This works great for disconnected data. Key-value stores and document stores like Redis of Mongo db store records in partittions and can easily scale-up horizontaly.

In image X you can see what whould hapen with a Graph if you whould shard it in the same way. Neo4j focusses on delivering a solution for fast online graph-database. If you whould query for data that is stored on different machines it is a near-impossible problem to make it perform fast.

Thereby the sollution Neo4j HA offers is a full replicated cluster, see image X. Every Neo4j instance in the cluster will contain the complete graph. The HA sollution will make sure all instances will remain in sync. 

<div class="row">
  <div class="span5">
    <img alt="Bunch of raspberry stuff" src="static/images/neo4j-ha/sharding.png">
    <p>Image X</p>
  </div>
  <div class="span5">
    <img alt="Raspberry pi cluster" src="static/images/neo4j-ha/replication.png">
    <p>Image X</p>
  </div>
</div>


### Neo4j setup

Setting up a Neo4j setup is quite easy you only need to change 6 properties in 2 files and your done:

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
    
For a fully instruction take a look at [the Neo4j website](http://neo4j.com/docs/stable/ha-setup-tutorial.html)

If everything is setup correctly and the neo4j instances are started you should be able to excecute the query ```:sysinfo``` in the webconsole: in my case [http://raspberrypi_2:7474/browser/](http://raspberrypi_2:7474/browser/)
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
Now that we have our Neo4j cluster up and running it's time to take a look at the Proxy. 

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
        acl write_hdr hdr_val(X-Write) eq 1
        use_backend neo4j-master if write_hdr
        default_backend neo4j-all

    backend neo4j-all
        option httpchk GET /db/manage/server/ha/available HTTP/1.0\r\nAuthorization:\ Basic\ bmVvNGo6dGVzdA==
            server s1 192.168.2.8:7474 maxconn 10 check
            server s2 192.168.2.7:7474 maxconn 10 check
            server s3 192.168.2.9:7474 maxconn 10 check

    backend neo4j-master
        option httpchk GET /db/manage/server/ha/master HTTP/1.0\r\nAuthorization:\ Basic\ bmVvNGo6dGVzdA==
            server s1 192.168.2.8:7474 maxconn 10 check
            server s2 192.168.2.7:7474 maxconn 10 check
            server s3 192.168.2.9:7474 maxconn 10 check

    listen admin
        bind *:8080
        stats enable
        stats realm   Haproxy\ Statistics
        stats auth    admin:123

![HA Proxy](/static/images/neo4j-ha/haproxy.png)

For the full explanation take a look at the [HAProxy Configuration Manual]("http://cbonte.github.io/haproxy-dconv/configuration-1.6.html")

### Lets test (and play)

<div class="row">
  <div class="span5">
    <img alt="Neo4j master" src="static/images/neo4j-ha/haproxy_2.png">
    <p>:sysinfo master</p>
  </div>
  <div class="span5">
    <img alt="Neo4j slave" src="static/images/neo4j-ha/haproxy_3.png">
    <p>:sysinfo slave</p>
  </div>
</div>


### Ansible
Because I don't like to repeat myself I've used Ansible to provision the raspberry Pi's.
The complete project can be found on my github repo, but will share some parts here.

With ansible you can make sure that config files are present on a server. You can also ask if the config files where different than the once already on the server. And take an action it config is changed: for example restart to make the config active.

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


neo4j.properties

    :::python
    ha.server_id={{play_hosts.index(inventory_hostname) +1}}
    
    ha.initial_hosts={%- for host in groups['neo4j-cluster']|sort -%}
    {{ hostvars[host]['ansible_eth0']['ipv4']['address'] }}:5001{% if not loop.last %},{% endif %}
    {% endfor %}

Will result in:
    
    :::python
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

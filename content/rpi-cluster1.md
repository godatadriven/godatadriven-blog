Title: Building a Raspberry Pi computing cluster (part 1)
Date: 2016-04-05 10:00
Slug: rpi-cluster-1
Author: Rogier van der Geer
Excerpt: <hier moet nog iets komen>
Template: article
Latex:

<span class="lead">Kopje</span>

Intro about computing clusters and Raspberry Pi

## GlusterFS

In this post we focus on [GlusterFS](https://en.wikipedia.org/wiki/GlusterFS "GlusterFS on Wikipedia"), 
which is a distributed file system developed by RedHat. 

## Installing

Installing GlusterFS on a Raspberry Pi is relatively easy. In the following we assume that you have a set 
of 4 Raspberry Pi's running Raspbian, conveniently called `rpi0` through `rpi3`, and that they are connected to the
same network with ip addresses `10.0.1.0` through `10.0.1.3`.

Firstly, we have to make sure the nodes can find each other on the network. To achieve this, 
we add the hostnames of the other nodes to each nodes' hosts file, found at `/etc/hosts`. For example, to the hosts
file of the first node we add the following three lines:

```
10.0.1.1        rpi1
10.0.1.2        rpi2
10.0.1.3        rpi3
```

We can test the new configuration by pinging the other nodes:

```
user@rpi0~$ ping rpi1 -c 1
PING rpi1 (10.0.1.1) 56(84) bytes of data.
64 bytes from rpi1 (10.0.1.1): icmp_seq=1 ttl=64 time=0.608 ms
```

Then we need to install the server package on every node. This is easily done with:

`user@rpi0~$ sudo apt-get install glusterfs-server`

which will install all required packages for you.

### Probing the peers

Now we need to introduce the individual glusterfs-servers to each other. This is done with the `peer probe` command:

```
user@rpi0~$ sudo gluster peer probe rpi1
peer probe: success.
user@rpi0~$ sudo gluster peer probe rpi2
peer probe: success.
user@rpi0~$ sudo gluster peer probe rpi3
peer probe: success.
```

After probing the peers they should show up in the peer status list:

```
user@rpi0~$ sudo gluster peer status
Number of Peers: 3

Hostname: rpi1
Uuid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx
State: Peer in Cluster (Connected)

Hostname: rpi2
Uuid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx
State: Peer in Cluster (Connected)

Hostname: rpi3
Uuid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx
State: Peer in Cluster (Connected)
```

Probing a peer on one of the nodes automatically adds the node to the peer lists of all nodes. If we have a look at the
peer status list on one of the other nodes the peers show up as well:

```
user@rpi1~$ sudo gluster peer status
Number of Peers: 3

Hostname: 10.0.1.0
Uuid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx
State: Peer in Cluster (Connected)

Hostname: 10.0.1.2
Uuid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx
State: Peer in Cluster (Connected)

Hostname: 10.0.1.3
Uuid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx
State: Peer in Cluster (Connected)
```

Here we see that the ip addresses of the other nodes show up in the list, instead of the hostnames. 
This can be fixed by probing the peers in reverse. After running

```
user@rpi1~$ sudo gluster peer probe rpi0
peer probe: success.
user@rpi1~$ sudo gluster peer probe rpi2
peer probe: success.
user@rpi1~$ sudo gluster peer probe rpi3
peer probe: success.
```

the hostnames should be visible in the peer status list:

```
user@rpi1~$ sudo gluster peer status
Number of Peers: 3

Hostname: rpi0
Uuid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx
State: Peer in Cluster (Connected)

Hostname: rpi2
Uuid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx
State: Peer in Cluster (Connected)

Hostname: rpi3
Uuid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxx
State: Peer in Cluster (Connected)
```

You may need to repeat this process on some of the other nodes.

### Creating a volume

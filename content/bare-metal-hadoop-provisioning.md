Title: Bare metal Hadoop provisioning with Ansible and Cobbler
Date: 2013-06-07 14:00
Slug: bare-metal-hadoop-provisioning-ansible-cobbler
Author: Kris Geusebroek
Excerpt: When setting up a Hadoop cluster you don't want to setup every machine doing manual installation of all required software. The idea is to start automating as soon as possible. While there are lots of tools able to help you with that, I recently came across Cobbler and Ansible which make a good combo in helping you easily define the tasks at hand.<br /><br />In this blog I would like to share the way we installed the operating system and configured the software to run a Hadoop cluster on bare metal machines.
Template: article

When setting up a Hadoop cluster you don't want to setup every machine doing manual installation of all required software. The idea is to start automating as soon as possible. While there are lots of tools able to help you with that, I recently came across Cobbler and Ansible which make a good combo in helping you easily define the tasks at hand.<br /><br />In this blog I would like to share the way we installed the operating system and configured the software to run a Hadoop cluster on bare metal machines.

What we've done here is nothing new and certainly no magic. It's just another possibility. Also there's nothing tool specific in there. For the demo setup of the Hadoop cluster we use Cloudera Manager, but it will work also with for example the Hortonworks Data Platform. The most important part of it is that we automate everything.

![automate everything][]


Since we don't want to install everything we need manually and the normal stack for building such a cluster consists of multipler layers like the operating system, basic configuration (firewall, ipsec, ipv6, ntpd, diskformatting etc.), the cluster install and some extra stuff (monitoring, extra packages) we need a way to have an easy configuration of the needs of each layer.

### The tools
#### Cobbler
First tool we use is [Cobbler][] which manages the operating system install iso's and we use it for handing out the static IP adresses to the nodes of the 'cluster to be built'. We mainly use it as our Content Management System where we configure which operating system to install and which IP a machine gets given a specific MAC address.

So on our installhost the cobbler deamon is running and waiting for a machine with a specific MAC address to announce itself on boot (using the network boot option). Cobbler then responds with handing over a kickstart script to the machine to do the operating system install. This script contains all instructions about the mounting and formatting of the disks and makes sure the operating system is installed properly.

#### Ansible
After that's finished our next tool [Ansible][] is coming in to the picture. Ansible is used to tie the rest together. Here we define the different roles the machines have and for each role we can define which specific software needs to be installed. Defining this is done with an easy to read DSL.
For example this is our role definition:

	[cluster]
	node01
	node02

	[cobbler]
	cobbler

	[proxy]
	cobbler

	[ganglia-master]
	node01

	[ganglia-nodes:children]
	cluster

	[cloudera-manager]
	node01

Between the angle brackets the role name is defined and below that the names of the nodes which need to be part of that role are mentioned.

And here is a file defining to copy a yum repo file form the installhost to all cluster machines and install the jdk and cloudera-manager-deamons packages:

	---
	- name: Configure CM4 Repo
	  copy: src=cloudera-manager/files/etc/yum.repos.d/cm4.repo dest=/etc/yum.repos.d/ owner=root group=root

	- name: Install CM4 common stuff
	  yum: name=$item state=installed
	  with_items:
	  - jdk
	  - cloudera-manager-daemons

You can create several of this kind of files to specify all the tasks you want to be executed. By combining multiple of these files together you can define a total set of requirements like this:

	- include: bootstrap.yml
	- include: repo.yml
	- include: monitoring.yml
	- include: cloudera-manager.yml

#### Cloudera Manager
Last tool we use is [Cloudera Manager][] which is installed by the ansible scripts and can be used to install the cluster specific tools like Impala, HBase etc.

### Finishing up
-	Remember it's no magic: Vendor specific hardware can screw things up (strange names for disk mounts for example)
-	Currently Bios settings, different RAID settings are not handled (yet).
-	There is a large amount of initial network traffic with large clusters (N-times downloading the same software packages from yum repositories) => Repo mirroring to the rescue
-	The MAC address of all nodes must be known

### Take aways
- 	Do automate from the start
- 	It's easy
- 	Use our [open source code][] to get a head start

Happy provisioning!

  [automate everything]: static/images/automate_everything.jpg "Automate everything"
  [cobbler]: http://www.cobblerd.org/ "Cobbler"
  [ansible]: http://ansible.cc/ "Ansible"
  [cloudera manager]: http://www.cloudera.com/content/cloudera/en/products/cloudera-manager.html "Cloudera Manager"
  [open source code]: https://github.com/godatadriven/ansible_cluster "The code"

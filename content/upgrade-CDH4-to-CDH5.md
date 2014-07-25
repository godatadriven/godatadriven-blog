Title: Upgrade secure cluster CDH4.5.0 to CDH5.0.3
Date: 2014-08-01 17:00
Slug: upgrade-secure-cluster-CDH4-to-CDH5
Author: Alexander Bij
Excerpt: It should be a matter of clicking some magic buttons to upgrade to the latest CDH5 version. We experience some trouble upgrading. In this blog we address the issues we encountered.
Template: article
Latex:

# Upgrade secure cluster CDH 4.5.0 to CDH 5.0.3 using parcels

In this blog we will describe how we performed the upgrade of the Hadoop cluster to the new version of the Cloudera Hadoop distributions. Although this upgrade is well documented by Cloudera the upgrade was not without a fight. We will explain the problems and the solutions.

## Why upgrade?
The reason to upgrade the cluster has multiple advantages:

- Ability to use YARN instead of MapReduce1 (a more generic and efficient scheduler) to allow Spark
- New version of Hive 0.10 -> 0.12 (Lots of bug fixes and improvements, DECIMAL datatype)
- New version of Impala 1.2.4 -> 1.3.1 (Run on YARN, new functions)
- New version of Hue 2.5.0 -> 3.5.0 (Way better UI to work with hive, impala and viewing results)
- Don't live in the past, keep up to date! 

## Our Landscape

The cluster exists of 13 physical machines running CentOS 6 with a SAN (big harddrive) for the raw data and collecting logs form the cluster.

On all machines we have root access and all command are being executed as root. All machines have Java 1.6 with the Java Extended Crypo Policy in place, which is required for a Kerberos secured cluster. We did not 'yum update' all the machines before the upgrade.

In the cluster we have these nodes:

![cluster-nodes](static/images/upgrade-cdh5-cluster/upgrade-cdh5-cluster.png)

	
## What parcels did we use?
Before the upgrade the cluster was using the parcels:

- CDH-4.5.0
- Impala 1.2.4

We were using the following services:

- hdfs1
- hive1
- hue1
- mapreduce1
- impala1
- zookeeper
- *inactive: sqoop1, oozie*
- *not installed: Cloudera Navigator*


## Performing the upgrade

Cloudera has a very good and complete documentation. To upgrade we followed the [cloudera-CDH5-upgrade-guide](http://www.cloudera.com/content/cloudera-content/cloudera-docs/CDH5/latest/CDH5-Installation-Guide/cdh5ig_cdh4_to_cdh5_upgrade.html).

### Step 1: Upgrade the Cloudera Manager

During this step the cluster is still available for usage.

The following steps are described in [cloudera-manager-upgrade-guide](http://www.cloudera.com/content/cloudera-content/cloudera-docs/CM5/latest/Cloudera-Manager-Administration-Guide/cm5ag_upgrading_cm.html).

> node: cloudera-mgmt:

1. Stop Cloudera Manager Server and database:

        :::shell
        $ service cloudera-scm-server stop
        $ service cloudera-scm-server-db stop
        $ service cloudera-scm-agent stop

1. Install yum repo & check result:

        :::shell
        wget http://archive.cloudera.com/cm5/redhat/6/x86_64/cm/cloudera-manager.repo
        mv cloudera-manager.repo /etc/yum.repos.d/
        yum clean all
        yum upgrade 'cloudera-*' 

        rpm -qa 'cloudera-manager-*'
        should look like:
        cloudera-manager-server-5.0.2-1.cm502.p0.297.el6.x86_64
        cloudera-manager-daemons-5.0.2-1.cm502.p0.297.el6.x86_64
        cloudera-manager-server-db-2-5.0.2-1.cm502.p0.297.el6.x86_64

1. Start Cloudera Manager & check server logs

        :::shell
        sudo service cloudera-scm-server-db start
        sudo service cloudera-scm-server start

        less /var/log/cloudera-scm-server/clou*.log

The installation of Cloudera Manager 5 was done without any problems, yej!


## Update Agent Packages

After the loggin in the Cloudera Manager it will suggest to upgrade the agents. 
Following the upgrade cluster wizard. _(the screenshots are taken from other upgrade to 5.1.0, but are very similar)_

![upgrade-step1](static/images/upgrade-cdh5-cluster/wizard.png)

1. Choose the version and location of the CDH parcel.

    When the cluster is not connected to internet, you must download the parcels and serve them youself. Then you must use the Cusom Repository pointing to that location which serves the manifest.json and parcel files.

    ![upgrade-step1](static/images/upgrade-cdh5-cluster/step1.png)

1. Install Java Unlimited Strength Encryption Policy Files.

    This is required for Kerberos security. This policy is specific for the rolled out version *(Java 1.7)*, if you have installed 1.7 before you should still check the box for the new java version.

    ![upgrade-step2](static/images/upgrade-cdh5-cluster/step2.png)

1. Agent Install config

    How Cloudera Manager connect to the agents is defined here. The number of simultaneous installations is a number to think about.
    Try to pick a 'smart' number, we have 12 nodes that are being upgraded. We used the default 10 and and it took a long time for them to complete and start the upgrade on the last 2 agents. The network IO is very high, that's why we would recommend a lower number to not be network bound during the upgrade.
    Picking 6 was better in our case. In two rounds all nodes are installed with limited network io.

    ![upgrade-step3](static/images/upgrade-cdh5-cluster/step3.png)

1. Perform the upgrade, fingers crossed

    ![upgrade-step4](static/images/upgrade-cdh5-cluster/step4.png)

In our case the update failed after distributing the packages with the message:

> cannot copy parcel.json to data node

The bars of all nodes were green, but the wizard cannot continue or retry, we need to fix problems ourselfs...

### Situation after the interrupted upgrade:

The wizard shows that all CDH.5.0.3 parcels have been distributed to all the nodes.
We could not rerun the upgrade wizard, trying it again results in a cannot rerun upgrade wizard error.
Through the Cloudera Manager interface we could check the nodes:

- All hosts are online
- All host services are stopped.
- Running the host inspector shows no problems.

The error suggested that the files are not present on the datanodes. We checked and the files *are* present on the datanodes mentioned in the error and the md5sum is the same as on the other nodes.

Try to start the service 1-by-1 from the Cloudera Manager.

- start hdfs -> ok
- start mapreduce -> ok
- start hive -> error

**Problem:**

> ...
> Caused by: MetaException(message:Version information not found in metastore. )
> ...

After some research:
CDH5 is shipped with Hive 0.12 an upgrade from Hive 0.10 (CDH4). For this update the database-schema should be updated. We expect that the update script did not run, because the wizard did not complete. We had to run scripts manually on the database used by the HiveMetastore.

Where is the MetaStore database?

- Cloudera Manager
- Click on the Hive service.
- Click on the Hive MetaStore under instances.
- Now click on tab Processses
- Click > show and the hive-site.xml.

The settings contains the location and credentials to access the database used by the HiveMetastore server. In our case the HiveMetastore is located at data01, so we login on that machine to find and execute the update-scripts.

**Solution:**

Run the database upgrade scripts ourselves. There are upgrade scripts for the suppoerted databases: derby, mysql, oracle and postgres. In each folder is a README which explains what needs to be done.

    :::shell
    updatedb
    locate CDH-5.0.3 | grep upgrade | grep mysql

    cd /somewhere/CDH-5.0.3-1.cdh5.0.3.p0.35/lib/hive/scripts/metastore/upgrade/mysql/

    mysql -u root hive1 -p
    mysql> source upgrade-0.10.0-to-0.11.0.mysql.sql
    mysql> source upgrade-0.11.0-to-0.12.0.mysql.sql

In Cloudera Manager we try to start the servies again:

- start hive1 -> oke
- start hue1 -> oke
- start impala1 -> oke

Great, no errors, lets try to run some queries!
Hue was started and accessible, but we could not login anymore.


**Alternative Solution**

After manually upgrading the cluster in the way stated above, we discovered that is also possible to use Cloudera Manager to run the upgrade on the inidividual services.

For HDFS:

- Service -> hdfs
- Actions -> Stop
- Actions -> Upgrade HDFS Metadata
- Actions -> Start

For HIVE:

- Service -> hive
- Actions -> Stop
- Actions -> Update Hive Metastore NameNodes
- Actions -> Update Hive Metastore Database Schema
- Actions -> Start

These steps should run the upgrade scripts that the upgrade wizard didn't run. Hopefully you now have a working cluster again!


**Problem:**

> /hue/runcpserver.log

    :::log
    [16/Jul/2014 02:05:29 -0700] backend      WARNING  Caught LDAPError while authenticating alexanderbij: INVALID_CREDENTIALS({'info': 'Simple Bind Failed: NT_STATUS_LOGON_FAILURE', 'desc': 'Invalid credentials'},)
    [16/Jul/2014 02:05:29 -0700] access       WARNING  172.16.20.53 -anon- - "POST /accounts/login/ HTTP/1.1" --Failed login for user "alexanderbij"

In the log it is clear simple bind is used. We have configured samba4 on the cloudera-mgmt to **not** allow simple_bind, you need a valid kerberos ticket to validate users against samba/ldap.
_This is not be a problem when you don't have a Kerberos secured cluster._

In Cloudera Manager we checked the Hue config:

- Services -> Hue1
- Configuration -> View and Edit
- Service-Wide -> Security

The Authentication Backend settings was LdapBackend, which did work in CDH 4.5.0 before the upgrade.

We noticed that the hue.ini from the HUE_SERVER does not have kerberos settings. The KT_RENEWER service hue.ini does have the correct kerberos settings. We are not sure if this is the rootcause of the problem.
For this issue we have created an ticket at cloudera:
[HUE-2226](https://issues.cloudera.org/browse/HUE-2226), to be continued...

**Solution:**

The solution was to use PamBackend authentication instead. When logging into Hue the credentials are checked through the machine local linux Pluggable Authentication Modules (PAM).
Each node in the cluster has sssd authentication mechanism which hooks in as a PAM module and uses Kerberos and LDAP to authenticate.
In this blog we will not go into the details of this setup.

After restarting Hue with PamBackend, all users could login again.


**Next problem:**

The homescreen of Hue showed some warnings:

![HUE-config-warnings](static/images/upgrade-cdh5-cluster/hue-impala-warn.png)

Running hive and impala queries (from HUE) did not work. Running queries from the commandline using hive and impala-shell did work. By checking server log from Hue in /hue/runcpserver.log we found:
    
    :::log
    INFO     Thrift saw an application exception: Invalid method name: 'GetSchemas'

in the /hue/error.log:
    
    :::log
    ERROR    Thrift saw exception (this may be expected).
    Traceback (most recent call last):
    File "/opt/cloud.....sktop/lib/thrift_util.py", line 367, in wrapper
    ret = res(*args, **kwargs)
    File "/opt/cloud...../gen-py/TCLIService/TCLIService.py", line 355, in GetSchemas
    return self.recv_GetSchemas()
    File "/opt/cloud../gen-py/TCLIService/TCLIService.py", line 371, in recv_GetSchemas
    raise x
    TApplicationException: Invalid method name: 'GetSchemas'

**Solution:**

It turns out that a we had configured Hue Savety Valve for impala. Before the upgrade we followed a tutorial to use impala: [Installing and using Impala](http://www.cloudera.com/content/cloudera-content/cloudera-docs/CDH5/latest/Impala/Installing-and-Using-Impala/ciiu_impala_odbc.html) with Hue.
Properties are pointing to port 21000 which is the port for the HiveServer1 protocol, but the newer verion is using HiveServer2 protocol which is running on port 21050.
In the current version of the Cloudera Manager you can choose the impala service and you don't need to specify the impala properties yourself.

In the Cloudera Manager:

- Service -> Hue
- Configuration -> View and Edit
- Service-Wide -> Advanced

        :::log
        [impala]
        server_host=data05
        server_port=21000

By removing this extra safety-valve config and choosing the Impala Service: impala1 at the Service-Wide category followed by a restart of hue the problem was solved.

# Conclusion

The documentation of Cloudera is complete and adjusted for the different versions of the components. Most of the settings and configuration-files can be found there. The upgrade process is explained in detail.
Although upgrading sounds like a piece of cake, it was done without a fight. It was definitely worth upgrading even with all the the bug-fixes, the user experience is greatly improved and we're using the latest and greatest again. All users of the cluster are happy with the new version.
The main take away is that if the upgrade wizard fails, which sadly has been the case on both this production cluster and a VM test cluster, it can not be rerun. The idea is to manually perform all the steps that the wizard failed to do.

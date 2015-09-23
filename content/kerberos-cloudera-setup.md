Title: Setting up Kerberos authentication for Hadoop with Cloudera Manager  
Date: 2014-03-18 18:00
Slug: kerberos-cloudera-setup
Author: Tünde Bálint
Excerpt: Some of our clients were interested in how we could enable security in Hadoop. This meant that we had to identify and test solutions of how we can integrate Kerberos with Active Directory and then identify what needs to be configured on the Hadoop site. These tests were done using Cloudera Manger 4.8.0 and CDH 4.5.0.
Template: article
Latex:

<span class="lead">Lately I was busy trying to figure out how I could integrate Active Directory authentication with Hadoop, more specifically with the CDH stack. I used a couple of CentOS 6.5 machines, Cloudera Manager 4.8.0 and CDH 4.5.0 to test the proposed solutions. But let's start at the beginning...</span>

Authentication is used to determine who is allowed to connect to a service, in our case to Hadoop. Authentication does not solve the problem of identifying which user has specific access rights to resources. Read more about this subject at <a href="http://blog.cloudera.com/blog/2012/03/authorization-and-authentication-in-hadoop/" target="_blank">Authorization and Authentication in Hadoop</a>.

Hadoop has two authentication methods:

- simple -- this is the default value used for HTTP web-consoles. In this case the clients must specify a username. Users who want to query HDFS or submit MapReduce job need to use their Linux username
- kerberos -- in this case the HTTP clients use HTTP Simple and Protected GSSAPI Negotiation Mechanism (SPNEGO) or delegation tokens. To understand Kerberos and what you need to do to set up a Kerberos server, see <a href="kerberos_kdc_install.html" target="_blank">Kerberos basics and installing a KDC</a>


When enabling security with Hadoop each user should have a Kerberos principal configured. Organizations which already have an Active Directory to manage user account, aren't keen in managing another set of user accounts separately in MIT Kerberos. The challenge was to identify solutions how we could integrate Active Directory with Hadoop's security.
I've tried two different approaches:

- Using a Kerberos server 
- integrating Samba with Cloudera Manager (still working on this blog...so check back later)

This is the last part of the blog series over Kerberos and it finally clues everything together and we can see why we did all that work.
The rest of the series contains:

- what is Kerberos and how to set up a Kerberos server:  <a href="kerberos_kdc_install.html" target="_blank">Kerberos basics and installing a KDC</a>
- how to set up cross-realm trust between an Active Directory and the KDC server: <a href="cross-realm-trust-kerberos.html" target="_blank">Setting up cross realm trust between Active Directory and Kerberos KDC</a>
- how to use Kerberos with Cloudera Manager and Hadoop -- this blog.

### Configuring Hadoop with KDC

The idea is to configure Cloudera Manager and CDH to talk to the KDC which was set up specifically for Hadoop and then create a unidirectional cross-realm trust between this KDC and the (production) Active Directory or KDC.

The Kerberos integration using one-way cross-realm trust is the recommended solution by Cloudera. Why? Because the hadoop services also need to use certificates when Kerberos is enabled. In case of a large enough cluster we can have quite an increased number of certificate requests and added users to the Kerberos server (we will have one per service -i.e. hdfs, mapred, etc. - per server). In case we would not configure a one-way cross-realm trust, all these users would end up in our production Active Directory or KDC server. The Kerberos server dedicated for the hadoop cluster could contain all the hadoop related users (mostly services and hosts), then connect to the production server to obtain the actual users of the cluster. It would also act as a shield, catching all the certificate requests from the hadoop service/host requests and only contacting the Active Directory or KDC production server when a 'real' user wants to connect. To see why Cloudera recommends setting up a KDC with one-way cross-realm trust read the <a href="http://www.cloudera.com/content/cloudera-content/cloudera-docs/CDH4/latest/CDH4-Security
-Guide/cdh4sg_topic_15.html" target="_blank">Integrating Hadoop Security with Active Directory</a> site.

## Prerequisites

1.	Make sure that DNS is configured correctly. We need to test that forward and reverse DNS lookup work.

	**Note:** When setting up a test DNS using BIND, I've used the following sites: 

	- <a href="https://www.digitalocean.com/community/articles/how-to-install-the-bind-dns-server-on-centos-6" target="_blank"> How to Install the BIND DNS Server on CentOS 6 </a>
	- <a href="http://www.philchen.com/2007/04/04/configuring-reverse-dns" target="_blank"> Configuring Reverse DNS in BIND 9 </a>

	To test revers DNS lookup you can use:
		
		$ yum install bind-utils

		$ nslookup 172.16.115.194
			Server:		172.16.115.193
			Address:	172.16.115.193#53

			194.115.16.172.in-addr.arpa	name = host1.mydomain.nl.

		$ host 172.16.115.194
			194.115.16.172.in-addr.arpa domain name pointer host1.mydomain.nl.

	To test forward look-up you can use:
		
		$ nslookup host1.mydomain.nl
			Server:		172.16.115.193
			Address:	172.16.115.193#53

		    Name: host1.mydomain.nl
		    Address: 172.16.115.194

		$ host host1.mydomain.nl
			host1.mydomain.nl has address 172.16.115.194

1.	Kerberos is a time sensitive protocol because its authentication is based partly on the timestamps of the tickets. We need to enable NTP (Network Time Protocol), otherwise clients attempting to authenticate from a machine with an inaccurate clock will be failed by the KDC in authentication attempts due to the time difference. So on all machines we do the following:

		$ yum install ntp
		$ service ntpd start
		$ chkconfig ntpd on

	Make sure that on all machines the date/time is set correctly:

		date

	If it's not you might need to synchronize the hardware clock (<a href="http://docs.slackware.com/howtos:hardware:syncing_hardware_clock_and_system_local_time" target="_blank">How To Sync Your System Time to Hardware Clock Consistently</a>) and/or change your timezone:
	
		$ ln -sf /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime


1.	Disable IPv6 on all machines.

1.  Make sure that the firewalls are disabled, or they allow the traffic which needs to be performed between the machines. 

1.	On the machine on which you will run Cloudera Manager you should disable Security-Enhanced Linux (SELinux). Edit /etc/sysconfig/selinux (which is a symlink to /etc/selinux/config) and change the SELINUX line to disabled.

		$ cat /etc/sysconfig/selinux
			# This file controls the state of SELinux on the system.
			# SELINUX= can take one of these three values:
			#       enforcing - SELinux security policy is enforced.
			#       permissive - SELinux prints warnings instead of enforcing.
			#       disabled - SELinux is fully disabled.
			SELINUX=disabled
			# SELINUXTYPE= type of policy in use. Possible values are:
			#       targeted - Only targeted network daemons are protected.
			#       strict - Full SELinux protection.
			SELINUXTYPE=targeted

			# SETLOCALDEFS= Check local definition changes
			SETLOCALDEFS=0

	Reboot.

1.	Install Hadoop using Cloudera Manager. In this blog I will not discuss hardware sizing, kernel tuning, disk and network configuration or placement and configuration of the different hadoop services. I will assume that you already have a Hadoop cluster up and running and I will explain how to enable security.This can be done by following the steps on the Cloudera website: <a href="http://www.cloudera.com/content/cloudera-content/cloudera-docs/CM4Ent/latest/Cloudera-Manager-Installation-Guide/cmig_intro_to_cm_install.html" target="_blank"> Introduction to Cloudera Manager Installation</a>.  

1. Set up a Kerberos KDC. You can use the <a href="kerberos_kdc_install.html" target="_blank">Kerberos basics and installing a KDC</a> blog for further information. 

1. In case you want to set up cross-realm trust between an Active Directory and the Kerberos KDC, you might be interested in the <a href="cross-realm-trust-kerberos.html" target="_blank"> Setting up cross realm trust between AD and Kerberos KDC</a> blog post.


## <a name="CM_config"></a> Configure Cloudera Manager and CDH to use Kerberos

Luckily Cloudera Manager has quite good documentation about what you need to change to enable Kerberos. This can be found on the Cloudera website: <a href="http://www.cloudera.com/content/cloudera-content/cloudera-docs/CM4Ent/4.5.2/Configuring-Hadoop-Security-with-Cloudera-Manager/Configuring-Hadoop-Security-with-Cloudera-Manager.html" target="_blank">Configuring Hadoop Security with Cloudera Manager Enterprise Edition</a>. Yeah...it says Enterprise Edition, but you can use this with the Cloudera Standard Edition too, as Kerberos is included in the free version too. As we already installed the KDC and we specified that we consider the installation of Hadoop with Cloudera Manager a prerequisite, we can start at step 4.

**NOTE:** If you don't use Cloudera Manager to implement Hadoop security, you must manually create and deploy the Kerberos principals and keytabs on every host machine in your cluster.

Here is a summary of the steps which you need to follow when using Cloudera Manager:

1. <a name="jce"></a> Because Cloudera Manager already installed Java JDK for us, the first thing we need to do is to install the Java Cryptography Extension (JCE) Unlimited Strength Jurisdiction Policy File. In our cluster we have JDK 1.6.0_32, so we need to download the <a href="http://www.oracle.com/technetwork/java/javase/downloads/jce-6-download-429243.html">Java Cryptography Extension (JCE) Unlimited Strength Jurisdiction Policy Files 6</a>

	**NOTE:** For Java 7 you need to download the JCE files specified on the Cloudera website.

	You need to install the JCE on all machines which have a role in the cluster (datanode, namenode, client, etc.). 

		#Get java version, so we know where we should change the policy files
		$ java -version
			java version "1.6.0_32"
		# Where are the policy files?
		$ locate local_policy.jar
			/usr/java/jdk1.6.0_31/jre/lib/security/local_policy.jar
			/usr/java/jdk1.6.0_32/jre/lib/security/local_policy.jar
		$ unzip jce_policy-6.zip 
		$ cd jce
		$ cp US_export_policy.jar /usr/java/jdk1.6.0_32/jre/lib/security/
		$ cp local_policy.jar /usr/java/jdk1.6.0_32/jre/lib/security/
		#Overwrite if prompted

1. On all machines install krb5-workstation 
	
		$ yum install krb5-workstation

	Make sure that the krb5.conf property file is the same on all machines.

1. Create a Kerberos principal and keytab file for Cloudera Manager Server 

		$ cd ~
		$ kadmin -p tunde/admin
			kadmin: addprinc -randkey cloudera-scm/admin@GDD.NL
			kadmin: xst -k cmf.keytab cloudera-scm/admin@GDD.NL
			kadmin: exit

	**NOTE:** The Cloudera Manager Server keytab file must be named cmf.keytab because that name is hard-coded in Cloudera Manager.

1. Copy the keytab and adjust permissions (These steps need to be performed on the Cloudera Manager server. If you generated the keytab on a different machine, you need to copy this keytab or delete the cloudera-scm/admin principal and recreate it from the Cloudera Manager server.)

		$ mv ~/cmf.keytab /etc/cloudera-scm-server/
		$ chown cloudera-scm:cloudera-scm /etc/cloudera-scm-server/cmf.keytab 
		$ chmod 600 /etc/cloudera-scm-server/cmf.keytab
	
	Add the Cloudera Manager Server principal (cloudera-scm/admin@GDD.NL) to a text file named cmf.principal and store the cmf.principal file in the /etc/cloudera-scm-server/ directory on the host machine where you are running the Cloudera Manager Server.

		$ cat /etc/cloudera-scm-server/cmf.principal
		cloudera-scm/admin@GDD.NL
		$ chown cloudera-scm:cloudera-scm /etc/cloudera-scm-server/cmf.principal
		$ chmod 600 /etc/cloudera-scm-server/cmf.principal

1. The following steps need to be perfomed from the Cloudera Manager Admin Console (http://Cloudera_Manager_server_IP:7180)

	1. Stop all services

	1. Go to Administration -> Settings -> Security -> Kerberos Security Realm and adjust the value to the default security realm you specified in krb5.conf. In our case this is GDD.NL.
	Save changes.

		**NOTE:** Hadoop is presently unable to use a non-default realm. The Kerberos default realm is configured in the libdefaults property in the /etc/krb5.conf file on every machine in the cluster.

	1. Enable HDFS security by navigating to HDFS Service -> Configuration -> View and Edit 

		1. Search for Hadoop Secure Authentication property and select the kerberos option

		1. Search for the Hadoop Secure Authorization property and select the checkbox 

		1. Search for the Datanode Transceiver Port property and specify a privileged port number (below 1024). Cloudera recommends 1004.

		1. Search for the Datanode HTTP Web UI Port property and specify a privileged port number (below 1024). Cloudera recommends 1006.

		1. Save changes

	1. To enable Zookeeper security navigate to Zookeeper Service -> Configuration -> View and Edit and search for the Enable Zookeeper Security property and select the checkbox. Save changes.

	1. In case you want to use HBase, you also need to set the HBase Secure Authentication property to kerberos and you need to enable the HBase Secure Authorization property. (I didn't need to install HBase on the secure cluster, so I did not test these.)

		After you enable security for any of the services in Cloudera Manager, a command called Generate Credentials will be triggered automatically. You can see the generated credentials or generate new credentials by navigating to Administration -> Kerberos. Here you should see credentials multiple credentials in the form of serviceName/FullyQualifiedDomainName@Realm. For example for the hdfs service and in case we have two hosts (host1.mydomain.nl and host2.mydomain.nl) we would have: hdfs/host1.mydomain.nl@GDD.NL and hdfs/host2.mydomain.nl@GDD.NL. 

		**NOTE:** Not all services are running on all hosts, so for example you shouldn't expect a hue credential generated for each host. You will only have a hue credential for the host where hue is running. 
	
	1. Enable Hue security navigate to Hue service -> Instances and click the Add button. Assign the Kerberos Ticket Renewer role instance to the same host as the Hue server.

	1. Start the HDFS service. 

	1. Deploy client configuration

	1. In order to create user directories on HDFS, you will need access to the HDFS super user account. To be able to access this account you must create a Kerberos principal whose first component is hdfs.

			$ kadmin -p tunde/admin
				kadmin: addprinc hdfs@GDD.NL
				#You will be asked for a password
				kadmin: exit
			#obtain a ticket for the hdfs user
			$ kinit hdfs@GDD.NL
	
	1. Create Kerberos principals for all users who will need access to the cluster
		
			$ kadmin -p tunde/admin
				kadmin: addprinc testUser@GDD.NL
				#You will be asked for a password
				kadmin: exit

	1. Make sure all host machines in the cluster have a Unix user account (with user id >= 1000) with the same name as the first component of that user's principal name. For example, the Unix account testUser should exist on every box if the user's principal name is testUser@GDD.NL. 

		**NOTE:** The user accounts must have a user ID that is greater than or equal to 1000. Why? Because Hadoop tries to prevent users like mapred, hdfs and other users which are Unix super users from submiting jobs. In Hadoop there is a setting, min.user.id which is by defaut set to 1000. The problem is that CentOS start user account at 500. This means that if you just create a user with "useradd user" the uid will not be above 1000. You can try to change the value of min.user.id to 500 in taskcontroller.cfg, but then you probably need to figure out how to do this via Cloudera Manager. My solution was to just create the users with a specified user ID. You can do this with "useradd correctUser -u NR", where NR > 1000
		If there are user accounts on your cluster that have a user ID less than the value specified for the min.user.id property, the TaskTracker returns an error code of 255.

	1. Create a subdirectory under /user on HDFS for each user account 

			$ kinit -p hdfs
			$ hadoop fs -mkdir /user/testUser
			$ hadoop fs -chown testUser /user/testUser

	1. Test the HDFS Kerberos setup:

			$ kdestroy
			$ kinit -p testUser
			$ echo "this is a test" > ~/test.txt
			$ hadoop fs -put ~/test.txt /user/testUser
			$ hadoop fs -ls
			Found 1 items
			-rw-r--r--   3 testUser supergroup         15 2014-02-05 12:39 test.txt
			# now test that without a valid ticket you can't access HDFS
			$ kdestroy
			$ hadoop fs -get /user/testUser/test.txt
			14/02/05 12:40:03 ERROR security.UserGroupInformation: PriviledgedActionException as:cloudera (auth:KERBEROS) cause:javax.security.sasl.SaslException: GSS initiate failed [Caused by GSSException: No valid credentials provided (Mechanism level: Failed to find any Kerberos tgt)]
			14/02/05 12:40:03 WARN ipc.Client: Exception encountered while connecting to the server : javax.security.sasl.SaslException: GSS initiate failed [Caused by GSSException: No valid credentials provided (Mechanism level: Failed to find any Kerberos tgt)]
			14/02/05 12:40:03 ERROR security.UserGroupInformation: PriviledgedActionException as:cloudera (auth:KERBEROS) cause:java.io.IOException: javax.security.sasl.SaslException: GSS initiate failed [Caused by GSSException: No valid credentials provided (Mechanism level: Failed to find any Kerberos tgt)]

		So without a valid Kerberos ticket you cannot access HDFS.

		**NOTE:** If you want to be really sure that HDFS is working properly, you can copy a bigger file (file size should be greater than your block size -- which is by default 128 MB) and then check that the blocks are properly replicated. You can see the block number on the Namenode web UI (http://namenode_ip:50070), where you can navigate to the file you just copied. Afterwards on the command line you can use the "hadoop fsck <path> -files -blocks -locations" command to see where the blocks are. Make sure that you specify a path which does not have too many file, otherwise the output will be hard to follow. You can also use "hadoop dfsadmin -report" which gives a similar output to fsck, but on a per node basis. An overview of the hadoop commands can be found at the <a href="http://archive.cloudera.com/cdh4/cdh/4/hadoop/hadoop-project-dist/hadoop-common/CommandsManual.html" target="_blank">Commands Manual</a> page.

	1. Start & test the MapReduce service

	1. Run a test job

			#Log in as testUser
			$ locate hadoop-examples.jar
			/usr/lib/hadoop-0.20-mapreduce/hadoop-examples.jar
			$ kinit 		$ 
			$ hadoop jar /usr/lib/hadoop-0.20-mapreduce/hadoop-examples.jar wordcount /user/testUser/test.txt out
			#Your job should run
			$ hadoop fs -cat out/part-r-00000


	1. Start the rest of the services (Hive, Oozie, Zookeeper, Hue, Impala,...)

		**NOTE:** I've added the impala parcel later on to the cluster, so I had to configure the impalad to which Hue can connect to. You can do this by going to the Hue service configuration in Cloudera Manager and find the Hue Safety Valve properties. Here you should add information about your Impala Daemon host. You should add the following lines:

			[impala]
			server_host=<impalad_hostname>
			server_port=21000
		
		Substitute your actual hostname for <impalad_hostname\>. You can chose any one of your Impala Daemon hosts. Afterwards save changes and restart the Hue Service.


### Troubleshooting

1. ** Client configuration not deployed**

	Error:

		$ hadoop fs -ls
		ls: Authorization (hadoop.security.authorization) is enabled but authentication (hadoop.security.authentication) is configured as simple. Please configure another method like kerberos or digest.

	Means that you forgot to deploy the client configuration, so the hadoop configuration used by the client still uses simple authentication, but Kerberos is enabled on the cluster. Go to Cloudera Manager page and Deploy Client configuration. 


1. ** No Kerberos ticket available for the user**
	
	Error:

		$ hadoop fs -ls
		14/02/05 12:05:47 ERROR security.UserGroupInformation: PriviledgedActionException as:cloudera (auth:KERBEROS) cause:javax.security.sasl.SaslException: GSS initiate failed [Caused by GSSException: No valid credentials provided (Mechanism level: Failed to find any Kerberos tgt)]
		14/02/05 12:05:47 WARN ipc.Client: Exception encountered while connecting to the server : javax.security.sasl.SaslException: GSS initiate failed [Caused by GSSException: No valid credentials provided (Mechanism level: Failed to find any Kerberos tgt)]
		14/02/05 12:05:47 ERROR security.UserGroupInformation: PriviledgedActionException as:cloudera (auth:KERBEROS) cause:java.io.IOException: javax.security.sasl.SaslException: GSS initiate failed [Caused by GSSException: No valid credentials provided (Mechanism level: Failed to find any Kerberos tgt)]

	You are trying to access HDFS, but your user doesn't have a Kerberos ticket or your ticket expired. Use kinit to obtain a new ticket.

1. **Hue Kerberos ticket cannot be renewed**

	In the logs of Hue for the Kerberos Ticket Renewer you see an error:

		Couldn't renew kerberos ticket in order to work around Kerberos 1.8.1 issue. Please check that the ticket for 'hue/host1.mydomain.nl' is still renewable:
		  $ kinit -f -c /tmp/hue_krb5_ccache
		If the 'renew until' date is the same as the 'valid starting' date, the ticket cannot be renewed. Please check your KDC configuration, and the ticket renewal policy (maxrenewlife) for the 'hue/host1.mydomain.nl' and `krbtgt' principals

	This error means that your tickets aren't renewable. Use kadmin to make the hue certificate renewable. Quick fix:

		$ kinit tunde/admin
		$ kadmin: modprinc -maxlife 1days -maxrenewlife 7days +allow_renewable krbtgt/GDD.NL
		$ kadmin: modprinc -maxlife 1days -maxrenewlife 7days +allow_renewable hue/host1.mydomain.nl

	We need to update the krbtgt principal for our realm, because  KDC cannot hand out tickets with a longer lifetime than the lifetime of the krbtgt principal.

	See explanation at <a href="kerberos_kdc_install.html" target="_blank">Kerberos basics and installing a KDC</a>

1. **Cloudera doens't have keytab or the KDC is not configured correctly in /etc/krb5.conf**

	When you try to generate the keytabs with Cloudera Manager you get the error:

		/usr/share/cmf/bin/gen_credentials.sh failed with exit code 1 and output of <<
		+ export PATH=/usr/kerberos/bin:/usr/kerberos/sbin:/usr/lib/mit/sbin:/usr/sbin:/sbin:/usr/sbin:/bin:/usr/bin
		+ PATH=/usr/kerberos/bin:/usr/kerberos/sbin:/usr/lib/mit/sbin:/usr/sbin:/sbin:/usr/sbin:/bin:/usr/bin
		+ CMF_REALM=GDD.NL
		+ KEYTAB_OUT=/var/run/cloudera-scm-server/cmf1349528239326605533.keytab
		+ PRINC=HTTP/host1.mydomain.nl@GDD.NL
		+ KADMIN='kadmin -k -t /etc/cloudera-scm-server/cmf.keytab -p cloudera-scm/admin@GDD.NL -r GDD.NL'
		+ kadmin -k -t /etc/cloudera-scm-server/cmf.keytab -p cloudera-scm/admin@GDD.NL -r GDD.NL -q 'addprinc -randkey HTTP/host1.mydomain.nl@GDD.NL'
		Couldn't open log file /var/log/kadmind.log: Permission denied
		kadmin: Client not found in Kerberos database while initializing kadmin interface

	Check that cloudera-scm has a valid certificate (it can be that you re-created the KDB while fixing some problem and you forgot to create the cloudera-scm user and generate the keytab) or it can be that you don't have the correct hostname configured in /etc/krb5.conf, so Cloudera Manager cannot find the KDC.

1. ** JCE not installed**
	Error seen in the namenode's log:

		INFO org.apache.hadoop.ipc.Server: IPC Server listener on 8022: readAndProcess threw exception javax.security.sasl.SaslException: GSS initiate failed [Caused by GSSException: Failure unspecified at GSS-API level (Mechanism level: Encryption type AES256 CTS mode with HMAC SHA1-96 is not supported/enabled)] from client 127.0.0.1. Count of bytes read: 0
		javax.security.sasl.SaslException: GSS initiate failed [Caused by GSSException: Failure unspecified at GSS-API level (Mechanism level: Encryption type AES256 CTS mode with HMAC SHA1-96 is not supported/enabled)]
     	  at com.sun.security.sasl.gsskerb.GssKrb5Server.evaluateResponse(GssKrb5Server.java:159)
 
 	Solution is to install the Java Cryptography Extension (JCE) Unlimited Strength Jurisdiction Policy File as describe in the [JCE section](#jce)

1. ** Incorrectly configured encryption when we set up cross-realm trust **

	When we tried to  get a directory listing with: 
		
		hadoop fs -ls 

	we obtained an error which we couldn't figure out (unfortunately I forgot to get a listing of this...sorry). To see the error details we set logging level: 

			$ export HADOOP_OPTS="-Dsun.security.krb5.debug=true" 
			$ hadoop fs -ls 

			>>>KRBError:
			     sTime is Tue Feb 07 16:16:36 CET 2014 1389107796000
			     suSec is 681067
			     error code is 14
			     error Message is KDC has no support for encryption type
			     realm is WIN_GDD.NL
			     sname is krbtgt/GDD.NL
			     msgType is 30
			>>> Credentials acquireServiceCreds: no tgt; searching backwards
			>>> Credentials acquireServiceCreds: no tgt; cannot get creds
			KrbException: Fail to create credential. (63) - No service creds
			    at sun.security.krb5.internal.CredentialsUtil.acquireServiceCreds(CredentialsUtil.java:279)
			    at sun.security.krb5.Credentials.acquireServiceCreds(Credentials.java:557)
			    at sun.security.jgss.krb5.Krb5Context.initSecContext(Krb5Context.java:594)
			    at sun.security.jgss.GSSContextImpl.initSecContext(GSSContextImpl.java:230)
			    at sun.security.jgss.GSSContextImpl.initSecContext(GSSContextImpl.java:162)
			    at com.sun.security.sasl.gsskerb.GssKrb5Client.evaluateChallenge(GssKrb5Client.java:175)
			    at org.apache.hadoop.security.SaslRpcClient.saslConnect(SaslRpcClient.java:137)
			    at org.apache.hadoop.ipc.Client$Connection.setupSaslConnection(Client.java:446)
			    at org.apache.hadoop.ipc.Client$Connection.access$1300(Client.java:241)
			    at org.apache.hadoop.ipc.Client$Connection$2.run(Client.java:612)
			    at org.apache.hadoop.ipc.Client$Connection$2.run(Client.java:609)
			    at java.security.AccessController.doPrivileged(Native Method)
			    at javax.security.auth.Subject.doAs(Subject.java:396)
			    at org.apache.hadoop.security.UserGroupInformation.doAs(UserGroupInformation.java:1408)
			    at org.apache.hadoop.ipc.Client$Connection.setupIOstreams(Client.java:608)
			    at org.apache.hadoop.ipc.Client$Connection.access$2000(Client.java:241)
			    at org.apache.hadoop.ipc.Client.getConnection(Client.java:1278)
			    at org.apache.hadoop.ipc.Client.call(Client.java:1196)
			    at org.apache.hadoop.ipc.ProtobufRpcEngine$Invoker.invoke(ProtobufRpcEngine.java:202)
			    at $Proxy9.getFileInfo(Unknown Source)
			    at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
			    at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:39)
			    at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:25)
			    at java.lang.reflect.Method.invoke(Method.java:597)
			    at org.apache.hadoop.io.retry.RetryInvocationHandler.invokeMethod(RetryInvocationHandler.java:164)
			    at org.apache.hadoop.io.retry.RetryInvocationHandler.invoke(RetryInvocationHandler.java:83)
			    at $Proxy9.getFileInfo(Unknown Source)

	It turned out that I only set DES encryption. I've deleted the krbtgt/GDD.NL@WIN_GDD.NL principal on the Kerberos KDC.

	I ran the 


		ksetup /SetEncTypeAttr GDD.NL AES256-CTS-HMAC-SHA1-96 AES128-CTS-HMAC-SHA1-96 RC4-HMAC-MD5 DES-CBC-MD5 DES-CBC-CRC

	on the Active Directory host.

	And then recreated the principal on the Kerberos server

		kadmin: addprinc -e "aes256-cts:normal aes128-cts:normal des3-hmac-sha1:normal arcfour-hmac:normal des-hmac-sha1:normal des-cbc-md5:normal des-cbc-crc:normal" krbtgt/GDD.NL@WIN_GDD.NL

### Conclusion

It's possible to integrate Kerberos and AD with Cloudera Manager. First it might seem scary and complicated but after you figured it out once, you'll realize it's not that hard.

I would strongly advice you to use an automatic provisioning tool, like Ansible, Chef or Puppet. I showed you the steps which you need to follow using bash commands. Doing this on one machine is acceptable, but when you have a cluster with 6 node you already want to be able to do the provisioning from one central machine and deploy it to the rest. It also makes sure that you will make less mistakes...or at least you will have the same error on all machines :).

In the next blog I will describe how we <a href="samba-configuration.html" target="_blank">configure Samba and SSSD to create a domain controller</a> and to replace the Kerberos KDC server. Of course this solution will also involve some configuration to enable Cloudera Manager to generate the certificates correctly.



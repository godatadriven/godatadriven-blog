Title: Use beeline on a secured cluster
Date: 2014-08-08 16:00
Slug: beeline-client-secured-cluster
Author: Alexander Bij
Excerpt: Limit the permissions on the MetaStore-tables can be achieved with Sentry (CDH 5.1), hive CLI must be replaced with beeline. This blog explains why and how to connect using beeline.
Template: article
Latex:

# Use beeline on a secured cluster

In this blog I will explain how to use beeline in a secured cluster. The CDH 5.1.0 cluster is secured with Kerberos (authentication) and Sentry (authorization). Cloudera is using [Sentry](http://sentry.incubator.apache.org/) for fine grained authorization of data and metadata stored on a Hadoop cluster. Hortonworks is using [Knox](http://knox.apache.org/) for achieving the same goal. 

> This blog is related to the **hive command-line tool**, using Hive through webinterface is fine!

## Why change from Hive to Beeline?

The primary difference between the two involves how the clients connect to Hive. The Hive CLI connects directly to the Hive Driver and requires that Hive be installed on the same machine as the client. However, Beeline connects to HiveServer2 and does not require the installation of Hive libraries on the same machine as the client. Beeline is a thin client that also uses the Hive JDBC driver but instead executes queries through HiveServer2, which allows multiple concurrent client connections and supports authentication.

Cloudera's Sentry security is working through HiveServer2 and not HiveServer1 which is used by Hive CLI. So hive though the command-line will not follow the policy from Setry. According to the [cloudera docs](http://www.cloudera.com/content/cloudera-content/cloudera-docs/CM5/latest/Cloudera-Manager-Managing-Clusters/cm5mc_sentry_config.html) you should not use Hive CLI and WebHCat. Use beeline or impala-sell instead.

> hive command-line will bypass sentry security!

I cannot confirm that the same situation applies for Hortonworks HDP 2.1 distribution with Knox. In the [hortonworks-security-tutorial](https://github.com/hortonworks/hadoop-tutorials/blob/master/Sandbox/T17_HDPSecurity.md) beeline is used instead of Hive CLI.


## Connect with Beeline

For a non secured cluster it is easy to connect. You can use beeline as described in this blog [cloudera-migrating-hive-to-beeline](http://blog.cloudera.com/blog/2014/02/migrating-from-hive-cli-to-beeline-a-primer/).


	:::shell
	# beeline with params
    beeline -u url -n username -p password
    # url is a jdbc connection string, pointing to the hiveServer2 host.

    # or use the !connect action
    beeline
    beeline> !connect jdbc:hive2://HiveServer2Host:Port
	
	# to exit beeline shell
    !quit


checkout the [beeline-command-options](https://cwiki.apache.org/confluence/display/Hive/HiveServer2+Clients#HiveServer2Clients-BeelineCommandOptions)


When using a kerberized cluster you can connect using your principle:

	:::shell
    # initialize your kerberos ticket
    kinit
    
    # Connect with your ticket, no username / password required.
    # master01 is the node where HiveServer2 is running
    # In the url add the parameter principle with the hive principle 
    beeline -u "jdbc:hive2://master01:10000/default;principal=hive/master01@MYREALM.COM"

You can find the full principle name in Cloudera Manager

- Administration -> Kerberos
- Credentials -> search hive
- Use the principle where HiveServer2 is running

## Troubleshoot

All the errors look the same. **Error: Invalid URL ... (state=08S01,code=0)**. The --verbose=true options does not help much unfortunately. When you run into problems, check the hiveserver2 logs for hints.

**Problem:**

    :::shell
    [alexanderbij@tools01 ~]$ beeline -u jdbc:hive2://master01:10000/default;principal=hive/master01@MYREALM.COM
    scan complete in 3ms
    Connecting to jdbc:hive2://master01:10000/default
    Error: Invalid URL: jdbc:hive2://master01:10000/default (state=08S01,code=0)
    ...


**Solution:**

Use "quotes around the url", otherwise the hive principle argument is not used

**Problem:**

	:::shell
	# beeline shell
    14/08/08 09:44:23 ERROR transport.TSaslTransport: SASL negotiation failure
	javax.security.sasl.SaslException: GSS initiate failed [Caused by GSSException: No valid credentials provided (Mechanism level: Server not found in Kerberos database (7))]
		...
	Caused by: KrbException: Server not found in Kerberos database (7)
		...
	Caused by: KrbException: Identifier doesn't match expected value (906)

**Solution:**

There is a keytab-file on the HiveServer2-node initialized with the principle. The connection string is using wrong the Kerberos principle for the keytab-file. Make sure you provide the correct hive prinicple in the connection url. 

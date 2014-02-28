Title:  Kerberos basics and installing a KDC
Date: 2014-02-28 11:00
Slug: kerberos_kdc_install
Author: Tünde Bálint
Excerpt: Explain some Kerberos terms and shows how to configure a Kerberos Key Distribution Center. I had to figure this out when I wanted to change the authentication method to Kerberos in Hadoop. 
Template: article
Latex:

This blog is part of the blog series Kerberos and Hadoop and it explains what Kerberos is and how you can set up a Kerberos server. This is the first part of the blog series and it is just a 'helper' blog, which explains what Kerberos is and how it can be installed. The rest of the series will contain:

- how to set up cross-realm trust between an Active Directory and the KDC server you set up in this blog
- how to use Kerberos with Cloudera Manager and Hadoop

For these blogs, please check back later....

### Background Kerberos

<a href="http://web.mit.edu/~kerberos/" target="_blank">Kerberos</a> is a network authentication protocol and it is built on the assumption that network connections are unreliable. Kerberos uses secret-key cryptography to enable strong authentication by providing user-to-server authentication. 

Kerberos has its own terminology which we need to shortly explain before we go further. 

- A **realm** establishes an authentication administrative domain. Each realm has it's own Kerberos database which contains the users and services for that particular administrative domain. 
- **Principals** are the entries in the Kerberos database. Each user, host or service is given a principal. 
- **Tickets** are issued by the authentication server. Clients present tickets to the application server to demonstrate the authenticity of their identity. Each ticket has an expiration and a renewal time. The Kerberos server has no control over the issued tickets, so even if we prevent a user from obtaining a ticket, if the user has already a valid ticket, he/she can use this to contact the service (until the ticket expires).
- **Keytabs** stores long-term keys for one or more principals.
 
To undestand the Kerberos terminology better, you can read the <a href="http://www.zeroshell.org/kerberos/Kerberos-definitions/" target="_blank">Kerberos Authentication Protocol</a> site.

A Kerberos server, usually called **Key Distribution Center (KDC)** resides on one physical host, but logically has multiple components incorporated:

- **Database** - contains the user and service entries (user's principal, maximum validity, maximum renewal time, password expiration, etc.) 
- **Authentication Server(AS)** - replies to the authentication requests from the client, when the not yet authenticated user must insert a password. The AS sends a **Ticket Granting Ticket (TGT)** back which can be used furtheron by the user, without re-entering their password. 
- **Ticket Granting Server(TGS)** - distributes service tickets based on the TGT

To access a service using Kerberos a client must do the following:

1. Authenticate to the Kerberos Authentication Server and receive a Ticket Granting Ticket (TGT)
2. Request a service ticket from the Ticket Granting Server
3. Use the service ticket to authenticate to the server that is providing the service the client wants to use (in our case: HDFS, MapReduce, HBase, etc.)

The following picture shows the steps mentioned above.

![kerberos_authentication](static/images/kerberos.png) 

### Install Kerberos Key Distribution Center

The KDC server can be a completely separate machine or for example the machine where Cloudera Manager is running. You should bare in mind that if the KDC is not accessble, you will not be able to use your Hadoop cluster. To install the KDC server I followed the steps describe on the CentOS website: <a href="https://www.centos.org/docs/5/html/5.1/Deployment_Guide/s1-kerberos-server.html" target="_blank">Configure a Kerberos 5 server</a>.

Short summary of the necessary steps:

**NOTE:** These commands need to be performed on the machine which will act as the KDC. All these command need to be preformed as root or as a user with sudo rights.

1. Install the krb5-libs, krb5-server, and krb5-workstation packages. 

		$ yum install krb5-libs krb5-server krb5-workstation

1. Set the realm name and the domain-to-realm mapping in /etc/krb5.conf and /var/kerberos/krb5dc/kdc.conf

	**NOTE:** By convention, all realm names are uppercase and all DNS hostnames and domain names are lowercase. 

	Our KDC is running on host1.mydomain.nl and out realm is GDD.NL. Here is the content of the /etc/krb5.conf file:

		$ cat /etc/krb5.conf 
			[logging]
			 default = FILE:/var/log/krb5libs.log
			 kdc = FILE:/var/log/krb5kdc.log
			 admin_server = FILE:/var/log/kadmind.log

			[libdefaults]
			 default_realm = GDD.NL
			 dns_lookup_realm = false
			 dns_lookup_kdc = false
			 ticket_lifetime = 24h
			 renew_lifetime = 7d
			 forwardable = true

			[realms]
			 GDD.NL = {
			  kdc = host1.mydomain.nl
			  admin_server = host1.mydomain.nl
			 }

			[domain_realm]
			 .example.com = GDD.NL
			 example.com = GDD.NL

	The content of /var/kerberos/krb5kdc/kdc.conf

		$ cat /var/kerberos/krb5kdc/kdc.conf 
			[kdcdefaults]
			 kdc_ports = 88
			 kdc_tcp_ports = 88

			[realms]
			 GDD.NL = {
			  #master_key_type = aes256-cts
			  acl_file = /var/kerberos/krb5kdc/kadm5.acl
			  dict_file = /usr/share/dict/words
			  admin_keytab = /var/kerberos/krb5kdc/kadm5.keytab
			  supported_enctypes = aes256-cts:normal aes128-cts:normal des3-hmac-sha1:normal arcfour-hmac:normal des-hmac-sha1:normal des-cbc-md5:normal des-cbc-crc:normal
			  max_life = 24h 0m 0s
              max_renewable_life = 7d 0h 0m 0s
			 }

	**NOTE:** we added the max_life and max_renewable_life properties.

1. Create the database which stores the keys for the Kerberos realm. With -s we create the stash file in which we store the master password. Without this file the KDC will prompt the user for the master password every time that it starts.

		$ kdb5_util create -s
			Loading random data
			Initializing database '/var/kerberos/krb5kdc/principal' for realm 'GDD.NL',
			master key name 'K/M@GDD.NL'
			You will be prompted for the database Master Password.
			It is important that you NOT FORGET this password.
			Enter KDC database master key: 
			Re-enter KDC database master key to verify: 

1. Edit the /var/kerberos/krb5kdc/kadm5.acl file to specify which principals have administrative access.

		$ cat /var/kerberos/krb5kdc/kadm5.acl 
			*/admin@GDD.NL	*

1. Create your first principal

	**NOTE:** First you should create a principal which has administrator privileges (the pricipal has to match the expression that you specified in /var/kerberos/krb5kdc/kadm5.acl). The kadmin utility communicates with the kadmind server over the network, and uses Kerberos to handle authentication. The first principal must already exist before connecting to the server over the network. We can create this principal with kadmin.local.

		$ kadmin.local -q "addprinc tunde/admin"
			Authenticating as principal root/admin@GDD.NL with password.
			WARNING: no policy specified for tunde/admin@GDD.NL; defaulting to no policy
			Enter password for principal "tunde/admin@GDD.NL": 
			Re-enter password for principal "tunde/admin@GDD.NL": 
			Principal "tunde/admin@GDD.NL" created.

1. Start Kerberos and make sure that the services will start after reboot
		
		$ service krb5kdc start
		$ service kadmin start
		$ chkconfig krb5kdc on
		$ chkconfig kadmin on

1. Use kadmin or kadmin.local to add principals. But which one can we use? As root you can use kadmin.local, but you cannot use kadmin because we didn't add a principal root/admin@GDD.NL. So this is what would happen:

		# log in with the root/admin principal -- fails, because we did not add this principal
		[root]$ kadmin
			Authenticating as principal root/admin@GDD.NL with password.
			kadmin: Client not found in Kerberos database while initializing kadmin interface 


		# log in with the tunde/admin principal -- works
		[root]$ kadmin -p tunde/admin
			Authenticating as principal tunde/admin with password.
			Password for tunde/admin@GDD.NL: 
			kadmin:
			kadmin: exit

		# log in with kadmin.local as root -- works
		[root]$ kadmin.local
			Authenticating as principal root/admin@GDD.NL with password.
			kadmin.local: 
			kadmin.local: exit 

	So let's see how we manage principals:

		[root]$ kadmin -p tunde/admin
			Authenticating as principal tunde/admin with password.
			Password for tunde/admin@GDD.NL: 

			#list principals -- see which users can get a kerberos ticket
			kadmin: list_principals

			#add a new principal
			kadmin:  addprinc user1
				WARNING: no policy specified for user1@GDD.NL; defaulting to no policy
				Enter password for principal "user1@GDD.NL": 
				Re-enter password for principal "user1@GDD.NL": 
				Principal "user1@GDD.NL" created.

			#delete principal
			kadmin: delprinc user1
				Are you sure you want to delete the principal "user1@GDD.NL"? (yes/no): yes
				Principal "user1@GDD.NL" deleted.
				Make sure that you have removed this principal from all ACLs before reusing.

			#let's add the user1 principal back
			kadmin:  addprinc user1
				WARNING: no policy specified for user1@GDD.NL; defaulting to no policy
				Enter password for principal "user1@GDD.NL": 
				Re-enter password for principal "user1@GDD.NL": 
				Principal "user1@GDD.NL" created.

			kadmin: exit

	**NOTE:** You can also specify a query and then exit from the kadmin console. 

		[root]$ kadmin -p tunde/admin -q "list_principals"
		[root]$ kadmin -p tunde/admin -q "addprinc user2"
		[root]$ kadmin -p tunde/admin -q "delprinc user2"


	To see what else you can do with the kadmin commnand, look at the <a href="http://web.mit.edu/kerberos/krb5-devel/doc/admin/admin_commands/kadmin_local.html" target="_blank">MIT Kerberos Documentation - kadmin</a>.

1. Now we should test if our KDC is issuing tickets correctly. 
	
		[root]$ kinit user1
			Password for user1@GDD.NL: 

		# Let's see the ticket and also display the encryption type
		[root]$ klist  -e
			Ticket cache: FILE:/tmp/krb5cc_0
			Default principal: user1@GDD.NL

			Valid starting     Expires            Service principal
			02/03/14 02:32:42  02/04/14 02:32:42  krbtgt/GDD.NL@GDD.NL
				renew until 02/03/14 02:32:42, Etype (skey, tkt): aes256-cts-hmac-sha1-96, aes256-cts-hmac-sha1-96 
	This means that we got a ticket for user1 and it is valid for 1 day.
	In case I would have been logged in as user "user1", I could have used kinit without specifying "user1" afterwards.

	We can also destroy tickets:

		[root]$ kdestroy
		[root]$  klist
			klist: No credentials cache found (ticket cache FILE:/tmp/krb5cc_0)

	**NOTE:** The principal username and the principal username/admin are different. If you added a principal username/admin that doesn't mean that you can get a ticket for the principal username. Let's see how this works. I've added a tunde/admin principal, but I didn't create a tunde principal.

		[root]$ kinit tunde
			kinit: Client not found in Kerberos database while getting initial credentials
		[root]$ kinit tunde/admin
			Password for tunde/admin@GDD.NL: 
		[root]$ klist
			Ticket cache: FILE:/tmp/krb5cc_0
			Default principal: tunde/admin@GDD.NL

			Valid starting     Expires            Service principal
			02/03/14 01:51:27  02/04/14 01:51:27  krbtgt/GDD.NL@GDD.NL
				renew until 02/03/14 01:51:27

1. <a name="ticket_renewal"></a>Check that you can renew the Kerberos Tickets (This is important for Hue)
	
	Why is TGT renewal important? Because some long running jobs might actually take advantage of renewing the ticket so they can continue running. Hue has a Kerberos Ticket Renewal instance. If you do not configure ticket renewal correctly, you won't be able to use Hue in a Kerberized environment.
	So how can we check?

		$ kinit tunde/admin
		$ klist
			Ticket cache: FILE:/tmp/krb5cc_0
			Default principal: tunde/admin@GDD.NL

			Valid starting     Expires            Service principal
			02/05/14 14:08:06  02/06/14 14:08:06  krbtgt/GDD.NL@GDD.NL
				renew until 02/05/14 14:08:06

		$ kinit -R
			kinit: Ticket expired while renewing credentials
 
 	If you didn't get this error, you can skip the rest of the blog, because your Kerberos server is working properly.

 	If you get this error, means that something is wrong with the Kerberos configuration. If it makes you feel better, it is probably not your fault: ticket renewal is per default disallowed in the most linux distributions. So what is happening?

 	The renewable life is set to be the minimum of:
		
	- the requested renewable life
	- the client principal's max renewable life
	- the service principal's max renewable life
	- the max renewable life for the realm (or one day, if not set)

	The principals' max renewable life times are set in the KDB records with kadmin. By default new principals get a max renewable life of 0 if the max renewable life for the realm is not set in kdc.conf. The kdb5_util utility sets the max renewable life for the TGS the same way.

	When you get a error similar to the one above, chances are that your krbtgt/<realm>@<realm> has a max renewable life time of 0. Let's see:

		$ kadmin -p tunde/admin
			kadmin:  getprinc tunde/admin
				Principal: tunde/admin@GDD.NL
				Expiration date: [never]
				Last password change: Mon Feb 03 01:15:15 PST 2014
				Password expiration date: [none]
				Maximum ticket life: 1 day 00:00:00
				Maximum renewable life: 0 days 00:00:00
				Last modified: Mon Feb 03 01:15:15 PST 2014 (root/admin@GDD.NL)
				Last successful authentication: [never]
				Last failed authentication: [never]
				Failed password attempts: 0
				Number of keys: 6
				Key: vno 1, aes256-cts-hmac-sha1-96, no salt
				Key: vno 1, aes128-cts-hmac-sha1-96, no salt
				Key: vno 1, des3-cbc-sha1, no salt
				Key: vno 1, arcfour-hmac, no salt
				Key: vno 1, des-hmac-sha1, no salt
				Key: vno 1, des-cbc-md5, no salt
				MKey: vno 1
				Attributes:
				Policy: [none]

	As you can see the maximum renewable life is 0 days.

	Where are these renewable lifetimes set?

	- In the /var/kerberos/krb5kdc/kdc.conf you should find max_life and max_renewable_life. Unfortunately CentOS doesn't have this set by default.
	- In the /etc/krb5.conf you have ticket_lifetime and renew_lifetime, but unfortunately having only these configured isn't enough

	Unfortunately setting the max_life and max_renewable_life in /var/kerberos/krb5kdc/kdc.conf and restarting the kadmin and krb5kdc services isn't enough, because the value was already saved in the KDB. So the quick fix would be to set the renew lifetime for the existing user and krbtgt realm. If you do not have too many users, you could also recreate the KDB using "kdb5_util create -s". Before recreating the database, you need to delete the principal* file from /var/kerberos/krb5kdc.

	The quick fix is to change the maxlife for the (all) user(s) and krbtgt/REALM principal can be set with:

		$ kadmin:  modprinc -maxlife 1days -maxrenewlife 7days +allow_renewable krbtgt@REALM
		$ kadmin:  modprinc -maxlife 1days -maxrenewlife 7days +allow_renewable user@REALM

	We need to update the krbtgt principal for our realm, because  KDC cannot hand out tickets with a longer lifetime than the lifetime of the krbtgt principal.
	In out case this would be:

		$ kadmin: modprinc -maxlife 1days -maxrenewlife 7days +allow_renewable krbtgt/GDD.NL
		$ kadmin:  modprinc -maxlife 1days -maxrenewlife 7days +allow_renewable tunde/admin@GDD.NL
			Principal "tunde/admin@GDD.NL" modified.
		$ kadmin:  getprinc tunde/admin
			Principal: tunde/admin@GDD.NL
			Expiration date: [never]
			Last password change: Mon Feb 03 01:15:15 PST 2014				
			Password expiration date: [none]
			Maximum ticket life: 1 day 00:00:00
			Maximum renewable life: 7 days 00:00:00
			Last modified: Wed Feb 05 14:32:52 PST 2014 (tunde/admin@GDD.NL)
			Last successful authentication: [never]
			Last failed authentication: [never]
			Failed password attempts: 0
			Number of keys: 6
			Key: vno 1, aes256-cts-hmac-sha1-96, no salt
			Key: vno 1, aes128-cts-hmac-sha1-96, no salt
			Key: vno 1, des3-cbc-sha1, no salt
			Key: vno 1, arcfour-hmac, no salt
			Key: vno 1, des-hmac-sha1, no salt
			Key: vno 1, des-cbc-md5, no salt
			MKey: vno 1
			Attributes:
			Policy: [none]

	And the maximum renewable life changed to 7 days.

So we have a working KDC, which can issue tickets and we can create new principals.

See you next time when we will discuss how to configure cross-realm trust.

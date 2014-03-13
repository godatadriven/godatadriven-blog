Title: Setting up cross realm trust between Active Directory and Kerberos KDC 
Date: 2014-03-13 15:40
Slug: cross-realm-trust-kerberos
Author: Tünde Bálint
Excerpt: Explains what you need to configure to set up cross-realm trust between Kerberos KDC and Active Directory.
Template: article
Latex:

This is the second part of the blog series and it is just a 'helper' blog, which explains how to set up cross-realm trust between an Active Directory and a Kerberos KDC. The rest of the series contains:

- what is Kerberos and how to set up a Kerberos server:  <a href="kerberos_kdc_install.html" target="_blank">Kerberos basics and installing a KDC</a>
- how to set up cross-realm trust between an Active Directory and the KDC server -- this blog
- how to use Kerberos with Cloudera Manager and Hadoop -- work in progress...please check back later...

**Cross-realm trust** describes situations when clients (typically users) of one realm use Kerberos to authenticate to services (e.g. server processes) which belong to another realm. Let's say that clients in realm A want to use the services in realm B. In this case, the administrator needs to configure that realm B *trusts* the realm A by sharing a key between the two involved KDCs (of the two different realms). In the above example the key would have the krbtgt/B@A form and should be added to both KDCs with the same key. By default cross-realm trust is unidirectional, meaning that if you also want the users from realm B to access services in realm A, you need to add another key (krbtgt@A/B). More about cross-realm trust: <a href="http://www.zeroshell.org/kerberos/Kerberos-cross-authentication/" target="_blank"> Cross Authentication </a>.

Luckily there is a good Cloudera post about how we can configure a Local Kerberos KDC to trust an Active Directory (see <a href="http://www.cloudera.com/content/cloudera-content/cloudera-docs/CDH4/4.2.2/CDH4-Security-Guide/cdh4sg_topic_15_1.html" target="_blank">here</a>). This post summarizes the same steps.

### Configuration on the Active Directory

We had a Windows 2008 Active Directory server installed.

1. Use ksetup to set up and maintaining Kerberos protocol and the Key Distribution Center (KDC) to support Kerberos realms, which are not also Windows domains. Using the following ksetup command will configure your computer to recognize the GDD.NL realm:

		ksetup /addkdc YOUR-LOCAL-REALM.COMPANY.COM kdc-server-hostname.cluster.corp.company.com

	In our case this command looks like:

		ksetup /addkdc GDD.NL host1.mydomain.nl

1. Use netdom to manage trust between domains

		netdom trust YOUR-LOCAL-REALM.COMPANY.COM /Domain:AD-REALM.COMPANY.COM /add /realm /passwordt:<TrustPassword>

	**NOTE:** Yes, it is passwordt. This specifies a new trust password. This parameter is valid only if you specify the /add parameter, and only if one of the domains that you specify is a non-Windows, Kerberos realm. You set the trust password on the Windows domain only, which means that you do not need credentials for the non-Windows domain.

	In our case:

		netdom trust GDD.NL /Domain:WIN_GDD.NL /add /realm /passwordt:<TrustPassword>

1. Set the proper encryption type
	
		ksetup /SetEncTypeAttr YOUR-LOCAL-REALM.COMPANY.COM <enc_type>

	This command looks like:

		ksetup /SetEncTypeAttr GDD.NL AES256-CTS-HMAC-SHA1-96 AES128-CTS-HMAC-SHA1-96 RC4-HMAC-MD5 DES-CBC-MD5 DES-CBC-CRC

### Configuration on the Kerberos server

Add a cross-realm krbtgt principal to the Kerberos KDC. To add this you need to use kadmin or kadmin.local. Use the same password you used in the netdom command on the Active Directory Server.

	kadmin:  addprinc -e "<enc_type_list>" krbtgt/YOUR-LOCAL-REALM.COMPANY.COM@AD-REALM.COMPANY.COM

In our case this command looks like:

	kadmin: addprinc -e "aes256-cts:normal aes128-cts:normal des3-hmac-sha1:normal arcfour-hmac:normal des-hmac-sha1:normal des-cbc-md5:normal des-cbc-crc:normal" krbtgt/GDD.NL@WIN_GDD.NL

### Configuration on all nodes in the cluster

Verify the kerberos /etc/krb5.conf. This should contain both realms om all the cluster nodes. The default realm and the domain realm should remain set as the MIT Kerberos realm which is local to the cluster. (so GDD.NL)

		[realms]
		  WIN_GDD.NL = {
		    kdc = host1.mywindomain.nl:88
		    admin_server = host1.mywindomain:749
		  }
		  GDD.NL = {
		    kdc = host1.mydomain.nl:88
		    admin_server = host1.mydomain.nl:749
		    default_domain = mydomain.nl
		  }

To properly translate principal names from the Active Directory realm into local names within Hadoop, you must configure the hadoop.security.auth_to_local setting in the core-site.xml file on all of the cluster machines. I didn't need to do this part, if you are interested in the details I would suggest the <a href="http://www.cloudera.com/content/cloudera-content/cloudera-docs/CDH4/4.2.2/CDH4-Security-Guide/cdh4sg_topic_19.html#topic_19_unique_2" target="_blank">Configuring the Mapping from Kerberos Principals to Short Names </a> site for further details.

Test the cross-realm trust. Let's assure that winUser exists in the Active Directory. We should be able to obtain a valid certificate: 

	$ kinit -p winUser
	$ klist
	Ticket cache: FILE:/tmp/krb5cc_500
	Default principal: winUser@GDD.NL

	Valid starting     Expires            Service principal
	02/28/14 01:25:22  03/01/14 01:25:22  krbtgt/GDD.NL@WIN_GDD.NL
		renew until 03/07/14 01:25:22


See you next time when we will discuss how to configure Cloudera Manager and Hadoop to use Kerberos.

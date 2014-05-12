Title: Configuring Samba4 and Cloudera Manager
Date: 2014-05-9 15:00
Slug: samba-configuration
Author: Tünde Bálint; Bolke de Bruin
Excerpt: The standard way of using Cloudera in an enterprise environment is to either create a cross realm trust with kerberos domain or to buy the enterprise add-ons. The down side of this that user administration is a hassle as you need to maintain the list of users that is able to access the system on every node by hand or replication (or you need to spend money). Samba 4 can serve as an Active Directory Domain Controller, provide DNS services, handle Kerberos-based authentication, and administer group policy. In this article we use Samba4 to setup an active directory domain and a domain controller. Next, we will configure SSSD and PAM to provide the necessary glue between active directory and the unix name service switch so users from active directory are available in linux. Finally, we will explain how to use this setup with Cloudera Manager. 
Template: article
Latex:
In this blog we will describe how we can configure Samba4 as an Active Directory domain controller to replace the Kerberos Domain Controller. We will also discuss SSSD and PAM. Our goal is to obtain renewable certificates which can be then used by Cloudera Manager, the hadoop daemons and users.
You might wonder why we actually bothered to implement this solution. We chose to implement this solution so we can have centralized administration of users.


### Background

**<em>Samba</em> **

Samba4 consists of multiple daemons:

- nmbd -- old style name resolution from the NT4 era
- smbd -- manages file transfers 
- winbindd -- manages the connections to domain controllers - replaced by sssd in this scenario (seems also deprecated in favor of sssd)
- ad - manages authentication. The Samba Active Directory domain controller functionality is implemented as an integrated Kerberos DC, LDAP server, DNS server, and SMB/CIFS server. Samba 4 AD DC functionality relies heavily on Heimdal Kerberos implementation. Samba 4 includes the embedded Heimdal. When compiled with MIT Kerberos, Samba 4 currently does not provide Active Directory Domain Controller functionality at all, only client side libraries and tools to the extent that does not involve AD DC operations.

Our goal is to set up Samba as a domain controller. To see how this can be done, you can read the <a href="https://wiki.samba.org/index.php/Samba_AD_DC_HOWTO"> Samba AD DC Howto</a>. The required steps are also listed in this blog. 

**NOTE:** Samba4 is quite new and much of the documentation still targets Samba3. 

**<em>PAM (Pluggable Authentication Modules)</em>**

PAM is a flexible mechanism for authentication users. PAM provides a way to develop programs that are independent of authentication scheme. These programs need "authentication modules" to be attached to them at run-time in order to work. Which authentication module is to be attached is dependent upon the local system setup and is at the discretion of the local system administrator. Read more at : <a href="http://tldp.org/HOWTO/User-Authentication-HOWTO/x115.html">PAM (Pluggable Authentication Modules)</a>.

**<em>SSSD (System Security Services Daemon)</em>**

SSSD is a system daemon. Its primary function is to provide access to identity and authentication remote resource through a common framework that can provide caching and offline support to the system. It provides PAM and NSS modules.
Integration with a Domain Controller (like an Active Directory server or in our case with the Samba AD DC) requires on the Linux side, SSSD. All communication between the PAM and the various possible back-ends is brokered through this daemon. 

### Our setup

We used a CentOS 6.5 machine to install the Samba AD DC and SSSD. On this machine also the Cloudera Manager 4.8 is running . Cloudera Manager 4.8 is managing a CDH 4.5 cluster consisting of 2 nodes. For all machines we are using static IPs. 

**<em> Prerequisites </em> **

1. Disable SElinux. In /etc/selinux/config make sure that you have a line saying "SELINUX=disabled" or use <a href="http://wiki.samba.org/index.php/Samba_AD_DC_access_control_settings">this</a> as a guideline. If you need to change this, reboot.

1. Set a FQDN for your server

1. Install NTPD (>= 4.2.6 if you have Windows clients and would like use signed ntp support), as accurate time synchronization is neccessary

1. Disable IP tables. 

		service iptables stop
		chkconfig iptables off

** NOTE:** Samba uses the following ports: 88/tcp, 88/udp, 137/tcp, 137/udp, 138/tcp, 138/udp, 139/udp, 139/udp, 445/tcp, 445/udp. So if you do not want to disable IP tables, make sure that these ports are open. We got these ports from the Samba documentation. We did not test if all ports are used in out setup. We were in a protected environment, so it was no problem to disable IP tables.

### Install & Configure & Test Samba and the Kerberos client

** NOTE:** We are using the sernet distribution of Samba4 as it packaged Samba4 4.1 and Samba4 4.0 had some issues for us. You can of course build from source if required.

1. Get sernet.repo ( you will need to create a Sernet acount for this on the <a href="https://portal.enterprisesamba.com/"> SerNet User Manager</a> site)

		cd /etc/yum.repos.d/
		wget https://<username>:<password>@download.sernet.de/packages/samba/4.1/centos/6/sernet-samba-4.1.repo
	
1. Edit repo file with user and password provided by Sernet


		cat /etc/yum.repos.d/sernet-samba-4.1.repo 

		[sernet-samba-4.1]
		name=SerNet Samba 4.1 Packages (centos-6)
		type=rpm-md
		baseurl=https://USERNAME:ACCESSKEY@download.sernet.de/packages/samba/4.1/centos/6/
		gpgcheck=1
		gpgkey=https://USERNAME:ACCESSKEY@download.sernet.de/packages/samba/4.1/centos/6/repodata/repomd.xml.key
		enabled=1

1. Install repo key

		yum install http://ftp.sernet.de/pub/sernet-build-key-1.1-4.noarch.rpm

1. Install Sernet packages

	**NOTE:** If you have the krb5-server package installed, you will need to uninstall it, as it conflicts with the sernet-samba-ad package.

		yum install -y sernet-samba sernet-samba-ad  sernet-samba-client


1. Configure Samba to act as a Domain Controller

	The only parameter you need to change is the samba startup mode in /etc/default/sernet-samba

		vi /etc/default/sernet-samba

		# SAMBA_START_MODE defines how Samba should be started. Valid options are one of
		#   "none"    to not enable it at all,
		#   "classic" to use the classic smbd/nmbd/winbind daemons
		#   "ad"      to use the Active Directory server (which starts the smbd on its own)
		# (Be aware that you also need to enable the services/init scripts that
		# automatically start up the desired daemons.)
		SAMBA_START_MODE="ad"

		# SAMBA_RESTART_ON_UPDATE defines if the the services should be restarted when
		# the RPMs are updated. Setting this to "yes" effectively enables the
		# functionality of the try-restart parameter of the init scripts.
		SAMBA_RESTART_ON_UPDATE="no"

		# NMBD_EXTRA_OPTS may contain extra options that are passed as additional
		# arguments to the nmbd daemon
		NMBD_EXTRA_OPTS=""

		# WINBINDD_EXTRA_OPTS may contain extra options that are passed as additional
		# arguments to the winbindd daemon
		WINBINDD_EXTRA_OPTS=""

		# SMBD_EXTRA_OPTS may contain extra options that are passed as additional
		# arguments to the smbd daemon
		SMBD_EXTRA_OPTS=""

		# SAMBA_EXTRA_OPTS may contain extra options that are passed as additional
		# arguments to the samba daemon
		SAMBA_EXTRA_OPTS=""

		# SAMBA_IGNORE_NSUPDATE_G defines whether the samba daemon should be started
		# when 'nsupdate -g' is not available. Setting this to "yes" would mean that
		# samba will be started even without 'nsupdate -g'. This will lead to severe
		# problems without a proper workaround!
		SAMBA_IGNORE_NSUPDATE_G="no"                             

1. Now we need to create our smb.conf file in /etc/samba.

		vi /etc/samba/smb.conf

		# Global parameters
		[global]
			workgroup = GDD
			realm = GDD.NL
			server role = active directory domain controller
		    dns forwarder = 8.8.8.8
			idmap_ldb:use rfc2307 = yes
			kerberos method = system keytab
			log level = 1
			template shell = /bin/sh
			winbind separator = +
			allow dns updates = signed
			tls enabled = yes
        	tls keyfile = tls/key.pem
        	tls cafile = tls/ca.pem
        	tls certfile = tls/cert.pem
			
		[netlogon]
			path = /var/lib/samba/sysvol/gdd.nl/scripts
			read only = No

		[sysvol]
			path = /var/lib/samba/sysvol
			read only = No			

	We specify tls enabled property to allow Samba to use autogenerated self-signed certificate.  On its first startup, Samba creates a private key, a self signed certificate and a CA certificate:
			
		/usr/local/samba/private/tls/ca.pem
		/usr/local/samba/private/tls/cert.pem
		/usr/local/samba/private/tls/key.pem
	
	These certificates are valid for 700 days after creation (the lifetime, that is used when auto-creating the certificates, is hardcoded in „source4/lib/tls/tlscert.c“).
	As per default TLS is enabled („tls enabled = yes“), the above files are used, what corresponds to the following smb.conf parameters:
	
		tls enabled  = yes
		tls keyfile  = tls/key.pem
		tls certfile = tls/cert.pem
		tls cafile   = tls/ca.pem
	    
	We configure the internal DNS server to use the Google DNS to forward request to in case our Samba server cannot handle requests. You need to set the "dns forwarder" parameter to the DNS server to which the requests can be forwarded if they can not be handled by Samba itself. 
	
	The winbind separator option allows you to specify how NT domain names and user names are combined into unix user names when presented to users. By default, winbindd will use the traditional '\' separator so that the unix user names look like DOMAIN\username. We had problems with Cloudera Manager and the postgreSQL used by cloudera manager because of this, so we changed the separator to '+'.


1.	Provision a domain

	If this is the first domain controller in a new domain (as this blog assumes), this involves setting up the internal LDAP, Kerberos, and DNS servers and performing all of the basic configuration needed for the directory. 

	**Note:** When asked for a password, provide a strong password, otherwise the domain provisioning will fail.
	**Note:** rfc2307 argument adds POSIX attributes (UID/GID) to the AD Schema. This will be necessary if you intend to authenticate Linux, BSD, or OS X clients (including the local machine) in addition to Microsoft Windows. It is required if you do not want your unix systems littered with Windows user names like $SYSTEM$. It does require you to add the unix attributes for users that need to have access to your hadoop environment.

		samba-tool domain provision --use-rfc2307 --interactive --function-level=2008_R2

		#You will need to answer a few questions.

			Realm [LOCALDOMAIN]: GDD.NL
			 Domain [GDD]: GDD
			 Server Role (dc, member, standalone) [dc]: 
			 DNS backend (SAMBA_INTERNAL, BIND9_FLATFILE, BIND9_DLZ, NONE) [SAMBA_INTERNAL]: 
			 DNS forwarder IP address (write 'none' to disable forwarding) [172.16.115.2]: none
			Administrator password: 
			Retype password: 
			Looking up IPv4 addresses
			Looking up IPv6 addresses
			No IPv6 address will be assigned
			Setting up secrets.ldb
			Setting up the registry
			Setting up the privileges database
			Setting up idmap db
			Setting up SAM db
			Setting up sam.ldb partitions and settings
			Setting up sam.ldb rootDSE
			Pre-loading the Samba 4 and AD schema
			Adding DomainDN: DC=gdd,DC=nl
			Adding configuration container
			Setting up sam.ldb schema
			Setting up sam.ldb configuration data
			Setting up display specifiers
			Modifying display specifiers
			Adding users container
			Modifying users container
			Adding computers container
			Modifying computers container
			Setting up sam.ldb data
			Setting up well known security principals
			Setting up sam.ldb users and groups
			Setting up self join
			Adding DNS accounts
			Creating CN=MicrosoftDNS,CN=System,DC=gdd,DC=nl
			Creating DomainDnsZones and ForestDnsZones partitions
			Populating DomainDnsZones and ForestDnsZones partitions
			Setting up sam.ldb rootDSE marking as synchronized
			Fixing provision GUIDs
			A Kerberos configuration suitable for Samba 4 has been generated at /var/lib/samba/private/krb5.conf
			Setting up fake yp server settings
			Once the above files are installed, your Samba4 server will be ready to use
			Server Role:           active directory domain controller
			Hostname:              host1
			NetBIOS Domain:        GDD
			DNS Domain:            gdd.nl
			DOMAIN SID:            S-1-5-21-4088664197-506966525-840056760


1. Add a reverse zone -- we will need this when we add the new hosts. It is important for Hadoop that we can properly do forward and reverse lookup.

		samba-tool dns zonecreate <server> <zone> [options]

	In our case this would be:

		samba-tool dns zonecreate host1.gdd.nl 115.16.172.in-addr.arpa -Uadministrator%password


1. Install Kerberos client, which means we need to install the client packages and provide each client with a valid krb5.conf configuration file. 
 
 		yum install -y krb5-workstation


1. Configure Kerberos. Here we changed the following parameters: dns_lookup_realm, dns_lookup_kdc, default_realm, kdc and admin_server. 

	**NOTE:** To understand the Kerberos parameters in the libdefaults section better, check out the <a href="http://web.mit.edu/kerberos/krb5-1.5/krb5-1.5.1/doc/krb5-admin/libdefaults.html#libdefaults" target="_blank"> Kerberos documentation for libdefaults</a>. However, bear in mind that the internal KDC of Samba4 is based on the Heimdal implementation so there are some differences.

	We also added the appdefaults section, (see defaults at <a href="http://web.mit.edu/kerberos/krb5-1.5/krb5-1.5.1/doc/krb5-admin/appdefaults.html#appdefaults" target="_blank">Kerberos appdefaults</a>) because pam_krb5 module expects a pam subsection in the appdefaults section from where it reads its configuration information.

		vi /etc/krb5.conf

		[logging]
		 default = FILE:/var/log/krb5libs.log
		 kdc = FILE:/var/log/krb5kdc.log
		 admin_server = FILE:/var/log/kadmind.log

		[libdefaults]
		 default_realm = GDD.NL
		 dns_lookup_realm = true
		 dns_lookup_kdc = true
		 ticket_lifetime = 24h
		 renew_lifetime = 7d
		 forwardable = true

		[realms]
		 GDD.NL = {
		        kdc = host1.gdd.nl:88
		        admin_server = host1.gdd.nl:749
		 }

		[appdefaults]
		     pam = {
		          debug = false
		          ticket_lifetime = 36000
		          renew_lifetime = 36000
		          forwardable = true
		          krb4_convert = false
		     }

1. Test connectivity

		smbclient -L host1 -U% 
			Domain=[GDD] OS=[Unix] Server=[Samba 4.1.5-SerNet-RedHat-7.el6]

				Sharename       Type      Comment
				---------       ----      -------
				netlogon        Disk      
				sysvol          Disk      
				IPC$            IPC       IPC Service (Samba 4.1.5-SerNet-RedHat-7.el6)
			Domain=[GDD] OS=[Unix] Server=[Samba 4.1.5-SerNet-RedHat-7.el6]

				Server               Comment
				---------            -------

				Workgroup            Master
				---------            -------

1. Test authentication

		smbclient //host1/netlogon -UAdministrator -c 'ls'
		Enter Administrator's password: 
		Domain=[GDD] OS=[Unix] Server=[Samba 4.1.5-SerNet-RedHat-7.el6]
		  .                                   D        0  Fri Feb 28 08:44:37 2014
		  ..                                  D        0  Fri Feb 28 08:44:37 2014

				54963 blocks of size 262144. 9834 blocks available

1. Add a new user

		samba-tool user add tunde
			New Password: 
			Retype Password: 
			User 'tunde' created successfully
		samba-tool user list
			Administrator
			krbtgt
			Guest
			tunde
		# Optionally set RFC2307 (NIS Schema) attributes in samba-tool create. Mainly needed for UID mapping to be usable. 
		# Not all attributes are set-able, only harmless and non-overlapping ones (uid, uidNumber, gidNumber, loginShell)
		samba-tool user add test1 --uid-number=1000 --gid-number=100 --login-shell=/bin/bash --uid=test1
			New Password: 
			Retype Password: 
			User 'test1' created successfully
		#Password should not expire
		samba-tool user setexpiry test1 -k yes --noexpiry
			Expiry for user 'test1' disabled.
		#Delete a user
		samba-tool user delete test1
			Deleted user test1


1. Other way to list users

		pdbedit -L -v
			...
			---------------
			Unix username:        Administrator
			NT username:          
			Account Flags:        [U          ]
			User SID:             S-1-5-21-3460841026-2796003680-2018327927-500
			Primary Group SID:    S-1-5-21-3460841026-2796003680-2018327927-513
			Full Name:            
			Home Directory:       
			HomeDir Drive:        (null)
			Logon Script:         
			Profile Path:         
			Domain:               
			Account desc:         Built-in account for administering the computer/domain
			Workstations:         
			Munged dial:          
			Logon time:           0
			Logoff time:          0
			Kickoff time:         Wed, 13 Sep 30828 19:48:05 PDT
			Password last set:    Fri, 28 Feb 2014 08:44:41 PST
			Password can change:  Fri, 28 Feb 2014 08:44:41 PST
			Password must change: never
			Last bad password   : 0
			Bad password count  : 0
			Logon hours         : FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
			---------------
			Unix username:        tunde
			NT username:          
			Account Flags:        [U          ]
			User SID:             S-1-5-21-3460841026-2796003680-2018327927-1103
			Primary Group SID:    S-1-5-21-3460841026-2796003680-2018327927-513
			Full Name:            
			Home Directory:       
			HomeDir Drive:        (null)
			Logon Script:         
			Profile Path:         
			Domain:               
			Account desc:         
			Workstations:         
			Munged dial:          
			Logon time:           0
			Logoff time:          0
			Kickoff time:         Wed, 13 Sep 30828 19:48:05 PDT
			Password last set:    Fri, 28 Feb 2014 09:00:05 PST
			Password can change:  Fri, 28 Feb 2014 09:00:05 PST
			Password must change: never
			Last bad password   : 0
			Bad password count  : 0
			Logon hours         : FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

1. Test that you can obtain a certificate 

		kinit tunde
			Password for tunde@GDD.NL: 
			Warning: Your password will expire in 41 days on Fri Apr 11 10:00:05 2014
		klist
			Ticket cache: FILE:/tmp/krb5cc_0
			Default principal: tunde@GDD.NL

			Valid starting     Expires            Service principal
			02/28/14 09:00:21  02/28/14 19:00:21  krbtgt/GDD.NL@GDD.NL
				renew until 03/07/14 09:00:18


1. Test that your /etc/resolv.conf points to the correct server. The resolv.conf should point to the server where the Samba AD is running. Make sure that the /etc/resolv.conf is not overwritten after restart.


### Install & Configure & Test SSSD

1. Install SSSD (System Security Services Daemon), which is a system daemon. Its primary function is to provide access to identity and authentication remote resource through a common framework that can provide caching and offline support to the system. It provides PAM and NSS modules. Reference: <a href="https://fedorahosted.org/sssd/" target="_blank"> SSSD - System Security Services Daemon</a>

     	yum install -y sssd

1. Extract the keytab for a domain account (you can use the machines account for that, too) and make sure, it is readable only for root.

		samba-tool domain exportkeytab /etc/krb5.sssd.keytab --principal=HOST1$
		chown root:root /etc/krb5.sssd.keytab 
		chmod 600 /etc/krb5.sssd.keytab

1. Look at what the keytab contains:

		 klist -k /etc/krb5.sssd.keytab 
			Keytab name: FILE:/etc/krb5.sssd.keytab
			KVNO Principal
			---- --------------------------------------------------------------------------
			   1 HOST1$@GDD.NL
			   1 HOST1$@GDD.NL
			   1 HOST1$@GDD.NL
			   1 HOST1$@GDD.NL
			   1 HOST1$@GDD.NL


1. Configure SSSD

		vi /etc/sssd/sssd.conf

		[sssd]
		config_file_version = 2
		services = nss, pam
		domains = GDD.NL
		debug_level = 10

		[nss]
		nss_filter_groups = root
		nss_filter_users = root
		nss_entry_cache_timeout = 30
		nss_enum_cache_timeout = 30

		[domain/GDD.NL]
		id_provider = ad
		ad_server= host1.gdd.nl
		ad_domain= gdd.nl
		ldap_schema = ad
		ldap_id_mapping = False
		krb5_keytab=/etc/krb5.sssd.keytab
		enumerate=true
		override_homedir=/home/%u

1.	Change the permissions on the /etc/sssd/sssd.conf

		chmod 600 /etc/sssd/sssd.conf

1.	Use authconfig to configure NSS and PAM.

	authconfig provides a simple method of configuring /etc/sysconfig/network to handle NIS, as well as /etc/passwd and /etc/shadow, the files used for shadow password support. Basic LDAP, Kerberos 5, and SMB (authentication) client configuration is also provided.

		authconfig --enablesssd --enablesssdauth --enablemkhomedir --update
		
	After running this command we got an error:
	
		authconfig --enablesssd --enablesssdauth --enablemkhomedir --update
		error reading information on service winbind: No such file or directory

	But when we checked the nsswitch.conf and in pam.d/system-auth everything was set up properly. We are not using winbind anyway.

1.  Alternatively to the previous step configure NSS and PAM manually (or use the steps described here to check that NSS and PAM were configured correctly)

	- SSSD provides an NSS module, sssd_nss, so that you can configure your system to use SSSD to retrieve user information. Edit the /etc/nsswitch.conf file for your system to use the sss name database. 
	
			cat /etc/nsswitch.conf
				#
				# /etc/nsswitch.conf
				#
				# An example Name Service Switch config file. This file should be
				# sorted with the most-used services at the beginning.
				#
				# The entry '[NOTFOUND=return]' means that the search for an
				# entry should stop if the search in the previous entry turned
				# up nothing. Note that if the search failed due to some other reason
				# (like no NIS server responding) then the search continues with the
				# next entry.
				#
				# Valid entries include:
				#
				#       nisplus                 Use NIS+ (NIS version 3)
				#       nis                     Use NIS (NIS version 2), also called YP
				#       dns                     Use DNS (Domain Name Service)
				#       files                   Use the local files
				#       db                      Use the local database (.db) files
				#       compat                  Use NIS on compat mode
				#       hesiod                  Use Hesiod for user lookups
				#       [NOTFOUND=return]       Stop searching if not found so far
				#
	
				# To use db, put the "db" in front of "files" for entries you want to be
				# looked up first in the databases
				#
				# Example:
				#passwd:    db files nisplus nis
				#shadow:    db files nisplus nis
				#group:     db files nisplus nis
	
				passwd:     files sss
				shadow:     files sss
				group:      files sss
	
				#hosts:     db files nisplus nis dns
				hosts:      files dns
	
				# Example - obey only what nisplus tells us...
				#services:   nisplus [NOTFOUND=return] files
				#networks:   nisplus [NOTFOUND=return] files
				#protocols:  nisplus [NOTFOUND=return] files
				#rpc:        nisplus [NOTFOUND=return] files
				#ethers:     nisplus [NOTFOUND=return] files
				#netmasks:   nisplus [NOTFOUND=return] files
	
				bootparams: nisplus [NOTFOUND=return] files
	
				ethers:     files
				netmasks:   files
				networks:   files
				protocols:  files
				rpc:        files
				services:   files sss
	
				netgroup:   files sss
	
				publickey:  nisplus
	
				automount:  files
				aliases:    files nisplus

	- Configure PAM
	
		** NOTE: A mistake in the PAM configuration file can lock you out of the system completely. Always back up your configuration files before performing any changes, and keep a session open so that you can revert any changes you make should the need arise.**

		To enable your system to use SSSD for PAM, you need to edit the default PAM configuration file. Back up the PAM configuration file.

			cd /etc/pam.d/
			cp system-auth system-auth.bck
	
		Edit this file to reflect the following example:
	
			vi /etc/pam.d/system.auth
	
				#%PAM-1.0
				# This file is auto-generated.
				# User changes will be destroyed the next time authconfig is run.
				auth        required      pam_env.so
				auth        sufficient    pam_unix.so nullok try_first_pass
				auth        requisite     pam_succeed_if.so uid >= 500 quiet
				auth        sufficient    pam_sss.so use_first_pass
				auth        required      pam_deny.so
	
				account     required      pam_unix.so
				account     sufficient    pam_localuser.so
				account     sufficient    pam_succeed_if.so uid < 500 quiet
				account     [default=bad success=ok user_unknown=ignore] pam_sss.so
				account     required      pam_permit.so
	
				password    requisite     pam_cracklib.so try_first_pass retry=3 type=
				password    sufficient    pam_unix.so sha512 shadow nullok try_first_pass use_authtok
				password    sufficient    pam_sss.so use_authtok
				password    required      pam_deny.so
	
				session     optional      pam_keyinit.so revoke
				session     required      pam_limits.so
				session     optional      pam_mkhomedir.so
				session     [success=1 default=ignore] pam_succeed_if.so service in crond quiet use_uid
				session     required      pam_unix.so
				session     optional      pam_sss.so
	
1.	To start the SSSD daemon, just start the sssd service:

		service sssd start
		chkconfig sssd on

	For debugging, it may be more comfortable to run the daemon in foreground:
	
		/usr/sbin/sssd -i

1. Test that we can see the users added to the Samba AD:
	
	 	getent passwd 
			...
			test1:*:1000:100:test1:/home/test1:/bin/bash
			...
			
	If you check the output carefully you will see that the user Administrator and 'tunde' (in our case) does not appear in this list. This is because we did not specify the UID, GID property when we used samba-tool to create the tunde user.
	
	**NOTE:** It might take some time to actually see the test1 user in the output of the 'getent passwd' command. This is because it needs a bit of time to synchronize. If you do not want to wait you can just use:
		
		getent passwd test1 


### Joining other machines to the domain 

When we set up a Hadoop cluster, all the machines which run Hadoop services should be joined to the AD which we created in the previous step. In our case these are the extra 2 machines which are managed by Cloudera Manager and which act as Namenode, Datanode, Jobtracker and Tasktracker. The steps which we need to do on these machines are fairly similar to what we did on the machine which runs Cloudera Manager, Samba and SSSD...but you still need to watch out, there are a few changes...

1. Get sernet.repo ( you will need to create a Sernet acount for this on the <a href="https://portal.enterprisesamba.com/"> SerNet User Manager</a> site)

		cd /etc/yum.repos.d/
		wget https://<username>:<password>@download.sernet.de/packages/samba/4.1/centos/6/sernet-samba-4.1.repo

1. Edit repo file with user and password provided by Sernet
	
	
		cat /etc/yum.repos.d/sernet-samba-4.1.repo 
	
		[sernet-samba-4.1]
		name=SerNet Samba 4.1 Packages (centos-6)
		type=rpm-md
		baseurl=https://USERNAME:ACCESSKEY@download.sernet.de/packages/samba/4.1/centos/6/
		gpgcheck=1
		gpgkey=https://USERNAME:ACCESSKEY@download.sernet.de/packages/samba/4.1/centos/6/repodata/repomd.xml.key
		enabled=1

1. Install repo key

		yum install http://ftp.sernet.de/pub/sernet-build-key-1.1-4.noarch.rpm
	

1. Install Sernet packages

	**NOTE:** If you have the krb5-server package installed, you will need to uninstall it, as it conflicts with the sernet-samba-ad package.

		yum install -y sernet-samba sernet-samba-ad  sernet-samba-client
	
1. Set up Samba. Create the smb.conf file in /etc/samba

		vi /etc/samba/smb.conf
	
		[global]
		   workgroup = GDD
		   realm = GDD.NL
		   security = ADS
		   idmap config * : range = 16777216-33554431
		   template shell = /bin/false
		   winbind use default domain = true
		   winbind offline logon = false
		   winbind separator = +
		
		   encrypt passwords = yes
		   kerberos method = system keytab
		
		   idmap config *:backend = tdb
		   idmap config {{ domain }}:backend = rid
		   idmap config {{ domain }}:range = 5000-40000
		   idmap config {{ domain }}:base_rid = 0
		
		   winbind nss info = rfc2307
		   winbind trusted domains only = no
		   winbind enum users  = yes
		   winbind enum groups = yes
		
		   log level = 1	
		  
	Set the permissions:
	
		chmod 644 /etc/samba/smb.conf
	   	
1. Install Kerberos client, which means we need to install the client packages and provide each client with a valid krb5.conf configuration file. 

		yum install -y krb5-workstation


1. Configure Kerberos.

		vi /etc/krb5.conf
	
		[logging]
		 default = FILE:/var/log/krb5libs.log
		 kdc = FILE:/var/log/krb5kdc.log
		 admin_server = FILE:/var/log/kadmind.log
	
		[libdefaults]
		 default_realm = GDD.NL
		 dns_lookup_realm = true
		 dns_lookup_kdc = true
		 ticket_lifetime = 24h
		 renew_lifetime = 7d
		 forwardable = true
	
		[realms]
		 GDD.NL = {
		        kdc = host1.gdd.nl:88
		        admin_server = host1.gdd.nl:749
		 }
	
		[appdefaults]
		     pam = {
		          debug = false
		          ticket_lifetime = 36000
		          renew_lifetime = 36000
		          forwardable = true
		          krb4_convert = false
		     }

	Set the permissions:

		chmod 644 /etc/krb5.conf

1. Install SSSD 

    	yum install -y sssd

1. Configure SSSD

		vi /etc/sssd/sssd.conf
	
		[sssd]
		config_file_version = 2
		services = nss, pam
		domains = default
		debug_level = 10
	
		[nss]
		nss_filter_groups = root
		nss_filter_users = root
		nss_entry_cache_timeout = 30
		nss_enum_cache_timeout = 30
	
		[domain/GDD.NL]
		id_provider = ad
		ad_server= host1.gdd.nl
		ad_domain= gdd.nl
		ldap_schema = ad
		ldap_id_mapping = False
		enumerate=true
		override_homedir=/home/%u
	
	Change the permissions on the /etc/sssd/sssd.conf
	
		chmod 600 /etc/sssd/sssd.conf
	
1. Check domain join

		net ads testjoin -P

	This will probably fail, but it is a command which you should be aware of. 

1.  Join the domain:

		net ads join -Uadministrator%password

	Note: Here you need to change the password and if needed, you can also change 'administrator' to the username you are using.

	**NOTE:** The following should not be required, but we couldn't get samba to add our hosts automatically. This is probably a misconfiguration on our side.
	
1.	Set forward DNS

		samba-tool dns add <domain_dc> <dns_domain> <hostname> A <ip> -U administrator%password
	
	So if our domain dc is running on host1.gdd.nl, our dnd_domain is GDD.NL and we try to add a new host named host2.gdd.nl with IP 172.16.115.5 then this command would look like:
	
		samba-tool dns add host1.gdd.nl gdd.nl host2 A 172.16.115.5 -U administator%password
	
	Of course you still need to write the correct password in the previous line.


1. 	Set reverse DNS

		samba-tool dns add <domain_dc> <reverse_zone> <host_part> PTR <fully qualified host name> -U administrator%password
	
	So if our domain dc is running on host1.gdd.nl, our dnd_domain is GDD.NL and we try to add a new host named host2.gdd.nl with IP 172.16.115.5 then this command would look like:
	
		samba-tool dns add host1.gdd.nl 115.16.172.in-addr.arpa 5 PTR host2.gdd.nl -U administator%password
	
	Of course you still need to write the correct password in the previous line.


1.  Check that reverse and forward lookup work correctly.

1. 	Check that your /etc/resolv.conf points to the correct server. The resolv.conf should point to the server where the Samba AD is running. Make sure that the /etc/resolv.conf is not overwritten after restart.

1.	Update system user configurations

		authconfig --enablesssd --enablemkhomedir --enablesssdauth --update

1.	Start sssd service

		service sssd start
		chkconfig sssd on


### Setting up Hadoop security with Cloudera Manager

The steps we need to follow to set up Hadoop Security with Cloudera Manager are similar to the steps described in the <a href="kerberos-cloudera-setup.html" target="_blank">Setting up Kerberos authentication for Hadoop with Cloudera Manager</a> blog. We already installed the krb5-workstation package on all machines, so that doesn't need to happen.

To summarize the steps:

1.	Allow the CDH install user to sudo samba-tool. This is required for operations on the principal names.

1.	Install a CDH version with Cloudera Manager without configuring security. Make sure that the cluster works.

1.	Install the Java Cryptography Extension (JCE) 

1.	Create a Kerberos principal and keytab file for Cloudera Manager Server and copy them to the correct directory

1. 	Because the default script distributed with Cloudera generates the certificates using a MIT Kerberos KDC, we had to write a script which can generate these certificates by talking to our Samba AD KDC which is Heimdal based. This script is the following:


		#!/usr/bin/env bash
		
		# GPL v2
		set -e
		set -x
		
		# Explicitly add RHEL5/6 and SLES11 locations to path
		export PATH=/usr/kerberos/bin:/usr/kerberos/sbin:/usr/lib/mit/sbin:/usr/sbin:$PATH
		
		CMF_REALM=${CMF_PRINCIPAL##*\@}
		CMF_USER=${CMF_PRINCIPAL%\@*}
		
		KEYTAB_OUT=$1
		PRINCUSER=${2%\/*}
		PRINC=${2%\@*}
		HOSTNAME=${PRINC##*\/}
		USER=${PRINCUSER}-${HOSTNAME}
		DOMAINNAME=`hostname | awk -F. '{$1="";OFS="." ; print $0}' | sed 's/^.//'`
		CUSER=`whoami`
		
		# grab domain controller from DNS
		DC=`host -t SRV _ldap._tcp.dc._msdcs.${DOMAINNAME} | awk '{ print $8 }' | sed 's/.$//'`
		
		if [ -z "${DC}" ]; then
			echo "Error no domain controller found. Check if your hostname is in FQDN format and and your DNS works"
			exit 1
		fi
		
		# map the domainname to an array 
		IFS=. read -a SUFFICES <<< "${DOMAINNAME}"
		
		# SUFFIX becomes something like dc=example,dc=com
		SUFFIX=`echo $(printf "dc=%s," "${SUFFICES[@]}") | sed 's/,$//'`
		
		# TODOL correct way is to have CMF_USER be able to add/modify users
		kinit -k -t /etc/cloudera-scm-server/cmf.keytab administrator
		
		set +e
		ldapsearch -b "${SUFFIX}" "(sAMAccountName=${USER})" | grep numEntries > /dev/null
		RETVAL=$?
		set -e
		
		if [ ${RETVAL} -eq 1 ]; then
			sudo samba-tool user create ${USER} -k yes --random-password
			sudo samba-tool user setexpiry ${USER} -k yes --noexpiry
		fi
		
		# fix the upn for some reason the samba team refuses to patch this in ktpass.sh or in samba-tool
		echo "dn: cn=${USER},cn=Users,${SUFFIX}
		changetype: modify
		replace: userPrincipalName
		userPrincipalName: ${PRINC}@${CMF_REALM}" | ldapmodify 
		
		# check if the spn exists for this user
		set +e
		ldapsearch -b "${SUFFIX}" "(servicePrincipalname=${PRINC})" | grep numEntries > /dev/null
		RETVAL=$?
		set -e
		
		if [ ${RETVAL} -eq 1 ]; then
			# GRRRRRR why doesnt samba-tool accept -H with spns?
			sudo samba-tool spn add ${PRINC} ${USER} -k yes
		fi
		
		sudo samba-tool domain exportkeytab ${KEYTAB_OUT} --principal=${PRINC} -k yes
		sudo chown ${CUSER} ${KEYTAB_OUT}
		
		chmod 600 ${KEYTAB_OUT}
	
	Save this script to /etc/cloudera-scm-server/gen_credentials.sh and change permissions:
	
		cd /etc/cloudera-scm-server
		chown cloudera-scm:cloudera-scm gen_credentials.sh
		chmod 755 gen_credentials.sh
		
1.	In the Cloudera Manager Admin Console (http://Cloudera_Manager_server_IP:7180) go to Administration -> Security -> Custom Kerberos Keytab Retrieval Script and set the value to /etc/cloudera-scm-server/gen_credentials.sh

1.	Follow all the steps described in the <a href="kerberos-cloudera-setup.html" target="_blank">Setting up Kerberos authentication for Hadoop with Cloudera Manager</a> blog, in Configure Cloudera Manager and CDH to use Kerberos section, step 5. This part describes the steps which you need to do from the Cloudera Manager Admin Console (http://Cloudera_Manager_server_IP:7180) to enable security in Hadoop.


After you followed all these steps you should have a secured Hadoop cluster using a Samba AD.


### Troubleshooting

**<em>Samba AD DC</em> **

1.  SELinux enabled - Samba error

		smbclient -L host1 -U% 
			session setup failed: NT_STATUS_ACCESS_DENIED

	The problem was that we forgot to reboot after disabling selinux.

1.  Providing weak password when provisioning the domain:

		samba-tool domain provision --use-rfc2307 --interactive --function-level=2008_R2
		...
		ERROR(ldb): uncaught exception - 0000052D: Constraint violation - check_password_restrictions: the password is too short. It should be equal or longer than 7 characters!
		  File "/usr/lib64/python2.6/site-packages/samba/netcmd/__init__.py", line 175, in _run
		    return self.run(*args, **kwargs)
		  File "/usr/lib64/python2.6/site-packages/samba/netcmd/domain.py", line 398, in run
		    use_rfc2307=use_rfc2307, skip_sysvolacl=False)
		  File "/usr/lib64/python2.6/site-packages/samba/provision/__init__.py", line 2155, in provision
		    skip_sysvolacl=skip_sysvolacl)
		  File "/usr/lib64/python2.6/site-packages/samba/provision/__init__.py", line 1757, in provision_fill
		    next_rid=next_rid, dc_rid=dc_rid)
		  File "/usr/lib64/python2.6/site-packages/samba/provision/__init__.py", line 1436, in fill_samdb
		    "KRBTGTPASS_B64": b64encode(krbtgtpass.encode('utf-16-le'))
		  File "/usr/lib64/python2.6/site-packages/samba/provision/common.py", line 50, in setup_add_ldif
		    ldb.add_ldif(data, controls)
		  File "/usr/lib64/python2.6/site-packages/samba/__init__.py", line 224, in add_ldif
		    self.add(msg, controls)

	We try to run again, so we can provide a strong password

		samba-tool domain provision --use-rfc2307 --interactive --function-level=2008_R2
		...
		Unable to load modules for /var/lib/samba/private/sam.ldb: Record exists at ../source4/dsdb/samdb/ldb_modules/partition_metadata.c:134
		ERROR(ldb): uncaught exception - Record exists at ../source4/dsdb/samdb/ldb_modules/partition_metadata.c:134
		  File "/usr/lib64/python2.6/site-packages/samba/netcmd/__init__.py", line 175, in _run
		    return self.run(*args, **kwargs)
		  File "/usr/lib64/python2.6/site-packages/samba/netcmd/domain.py", line 398, in run
		    use_rfc2307=use_rfc2307, skip_sysvolacl=False)
		  File "/usr/lib64/python2.6/site-packages/samba/provision/__init__.py", line 2124, in provision
		    schema=schema, fill=samdb_fill, am_rodc=am_rodc)
		  File "/usr/lib64/python2.6/site-packages/samba/provision/__init__.py", line 1202, in setup_samdb
		    samdb.connect(path)
		  File "/usr/lib64/python2.6/site-packages/samba/samdb.py", line 71, in connect
		    options=options)

	Solution -- Note: Make sure you do not have other domains in the sam.ldb

		rm  /var/lib/samba/private/sam.ldb

1. Authentication test fails

		smbclient //host1/netlogon -UAdministrator -c 'ls'
		Enter Administrator's password: 
		Domain=[GDD] OS=[Unix] Server=[Samba 4.1.5-SerNet-RedHat-7.el6]
		tree connect failed: NT_STATUS_BAD_NETWORK_NAME


	The problem is that the netlogon path from /etc/samba/smb.conf doesn't exists or does not have the correct permissions. We are talking about the following parameter from /etc/samba/smb.conf:

		[netlogon]
		path = /var/lib/samba/sysvol/gdd.nl/scripts

	Solution:

		mkdir /var/lib/samba/sysvol/gdd.nl/scripts
		chmod 770 /var/lib/samba/sysvol/gdd.nl/scripts


**<em>SSSD</em>**

1.  No domains configured error when trying to start SSSD

		/usr/sbin/sssd -i
		(Fri Feb 28 08:01:02:501988 2014) [sssd] [confdb_get_domain_internal] (0x0010): Unknown domain [GDD.NL]
		(Fri Feb 28 08:01:02:502023 2014) [sssd] [confdb_get_domains] (0x0010): Error (2 [No such file or directory]) retrieving domain [GDD.NL], skipping!
		(Fri Feb 28 08:01:02:502035 2014) [sssd] [confdb_get_domains] (0x0010): No properly configured domains, fatal error!
		(Fri Feb 28 08:01:02:502042 2014) [sssd] [get_monitor_config] (0x0010): No domains configured.
		(Fri Feb 28 08:01:02:502088 2014) [sssd] [main] (0x0020): Error loading configuration database: [2]: No such file or directory

	Solution is to actually configure a domain.
	
1.  Fatal error initializing data providers when trying to start SSSD

		sssd -i
		...
		(Mon Mar  3 05:59:23 2014) [sssd[be[GDD.NL]]] [load_backend_module] (0x0010): Error (2) in module (ad) initialization (sssm_ad_id_init)!
		(Mon Mar  3 05:59:23 2014) [sssd[be[GDD.NL]]] [be_process_init] (0x0010): fatal error initializing data providers
		(Mon Mar  3 05:59:23 2014) [sssd[be[GDD.NL]]] [main] (0x0010): Could not initialize backend [2]
		(Mon Mar  3 05:59:23 2014) [sssd] [sbus_remove_watch] (0x2000): 0x1d4be30/0x1d44340
		(Mon Mar  3 05:59:23 2014) [sssd] [sbus_remove_watch] (0x2000): 0x1d4be30/0x1d4c850
		(Mon Mar  3 05:59:23 2014) [sssd] [sbus_dispatch] (0x4000): dbus conn: 1D4E190
		(Mon Mar  3 05:59:23 2014) [sssd] [sbus_dispatch] (0x0080): Connection is not open for dispatching.

	Damn, forgot to generate the credential file and the line I did not have a line in /etc/sssd/sssd.conf saying: krb5_keytab=/etc/krb5.sssd.keytab

	Solution: Generate keytab file with 

		samba-tool domain exportkeytab /etc/krb5.sssd.keytab --principal=HOST1$

	Add the "krb5_keytab=/etc/krb5.sssd.keytab" line to /etc/sssd/sssd.conf

	Note: HOST1 is used for the host account in our case.


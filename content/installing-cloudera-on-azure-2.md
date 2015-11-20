Title: Installing Cloudera on Azure (part 2 of 2)
Date: 2015-11-20 15:00
Slug: installing-cloudera-on-azure-2
Author: Tunde Alkemade, Alexander Bij, Walter van der Scheer
Excerpt: This is part 2 of 2 about the installation of a Cloudera cluster on Microsoft Azure. In this article we motivate our choices on using the template or developing the implementation from scratch, and the actual modifications we made to the Cloudera template.
Latex:

<span class="lead">
Recently, GoDataDriven pioneered with the Cloudera template to install a Cloudera cluster on Microsoft Azure. In this series of 2 articles we share our insights and experiences with installing Cloudera and modifying the template that Cloudera provides for the installation on MS Azure.
</span>

## Modifying the Cloudera template 
Although the deployment templates offers quite a number of features, in our use case there were some specific requirements, so we had to decide whether to use the template and modify it, or start from scratch by installing some Linux machines on Azure and configure the rest using a provisioning tool like Ansible. First of all we had a close look at the requirements for the use case and the out-of-the-box features of the template. 

## Requirements for the use case

The general requirements for our use case were: 
<ul>
<li>Install Cloudera Enterprise Hadoop on Azure</li> 
<li>Make sure single sign-on is possible </li>
<li>To reduce costs, start by using only 5 worker nodes, with three 1 TB data disks each</li> 
</ul>

And the following technical requirements were added: 
<ul>
<li>Deploy 3 master nodes, so if the cluster expands the load can be handled</li>
<li>Make sure that HDFS and YARN are configured with high availability enabled</li> 
<li>Connect the Cloudera cluster to the Active Directory to be able to authenticate users who are allowed to use the cluster</li>
<li>Install and configure Sentry to be able to assure access control. Set up one gateway machine from which the users would be able to work. On this gateway we would also have RStudio and IPython installed so these can be used for analysis</li>
</ul>

## Out-of-the-box features of the template 

First of all we took a look at the features of the template: 
<ol>
<li>Creates a Resource Group for all the components</li> 
<li>Create VNet and subnets</li> 
<li>Create availability sets. Place masters and workers in different availability sets</li>  
<li>Create security groups</li> 
<li>Create Masternode and Workernode instances using the Cloudera VM Image (CentOS image built and maintained by Cloudera). The template automatically uses Azure DS14 machines, which are the only machine types recommended and supported by Cloudera for Hadoop installations.</li> 
<li>For each host a [Premium Storage account](https://azure.microsoft.com/en-us/documentation/articles/storage-premium-storage-preview-portal/) is created</li>
<li>Add disks to the machines, format and mount the disks (10 data disks of 1 TB per node)</li>
<li>Set up forward/reverse lookup between hosts using /etc/hosts file </li>
<li>Tune Linux OS and network configurations like disable SELinux, disable IPtables, TCP tuning parameters, disable huge pages</li> 
<li>Set up time synchronization to an external server (NTPD)</li>
<li>Setup Cloudera Manager and the database used by the Cloudera Manager</li>
<li>Setup Hadoop services using the Cloudera Python API</li> 
</ol>

The template also has a disadvantage: it is meant to start up a cluster, but you cannot create extra data nodes and add them to the cluster. The template does not provision a gateway machine for you. 

## Best-practices for a manual implementation 
We also identified a couple of best practices which we would need to keep in mind if we wouldn’t use the template: 
When deploying a Linux image on Azure there is a temporary drive added. When using the DS14 machines the attached disk on /mnt/resource is SSD and actually pretty big (something like 60 GB). This temporary storage must not be used to store data that you are not willing to lose. The temporary storage is present on the physical machine that is hosting your VM. Your VM can move to a different host at any point in time due to various reasons (hardware failure etc.). When this happens your VM will be recreated on the new host using the OS disk from your storage account. Any data saved on the previous temporary drive will not be migrated and you will be assigned a temporary drive on the new host. (Understanding the temporary drive on Windows Azure Virtual Machines - http://blogs.msdn.com/b/mast/archive/2013/12/07/understanding-the-temporary-drive-on-windows-azure-virtual-machines.aspx) 
The OS root partition (where also the /var/log directory resides) is fairly small (10GB). This is perfect for an OS disk, but Cloudera also puts the parcels (an alternate form of distribution for Cloudera Hadoop) on /opt/cloudera and the logs into /var/logs. These take up quite a lot of space so a 10 GB disk is not enough. That’s why you should move the parcels and the log file to a different disk. (Reminder: normally the template takes care of this for you.) 
If you install Cloudera without moving these files to a different disk, you will see warning messages in Cloudera Manager that there not enough free disk space available. 
In a distributed system, thus also for a Hadoop cluster (especially if Kerberos is used), time synchronization between hosts is essential. Microsoft Azure provides time synchronization, but the VMs read the (emulated) hardware clock from the underlying Hyper-V platform only upon boot. From that point on the clock is maintained by the service using a timer interrupt. This is not a perfect time source, of course, and therefore you have to use NTP software to keep it accurate.  
Modifications to the template 
After analyzing the gaps, we decided to use the template but modify some parts, because in this way we can get the machines that we want and afterwards add them to the cluster. When additional nodes are required, we would be able to do this using the same template. 
The original template is located in GitHub at https://github.com/Azure/azure-quickstart-templates/tree/master/cloudera-on-centos. We made the following modifications: 
Creation of the virtual network with a separate template. This allows us to change the number ofsubnets and make a site2site VPN connection. The Cloudera template was modified to use an existing VNet and subnet 
Seting-up the DNS component of the Active Directory for the machines to do forward and reverse lookup 
Add ingthe HTTPS ports to the security groups, because when using TLS for Cloudera Manager different ports are being used. 
Disabling IPv6 
Using the time server provided by the client 
Decreasing the number of data disks per node 
Installing Hadoop components ourselves to increase control over what goes where. Also, the template does not support the integration of Hadoop with the Active Directory, so we did this manually.  
Adding a new node type to the template to deploy a gateway node 
Changing the template 
In orde to change the template, first we had to understand how the template works.  
Fout bij het laden van [Afbeelding] 
When you deploy using the marketplace you interact with the azuredeploy.parameters.json through the UI as this is the file where the parameters are specified. This file is read by the main template file azuredeploy.json which defines the dependencies between the elements of the template file. 
First of all the template creates the virtual network, security groups and availability sets. This is done in shared-resouces.json.  
After deployment of these resources we can start creating the virtual machines, calling master-node.json and data-node.json in parallel. These scripts set up the specific security groups for masters and data nodes, create the storage accounts (one per node), set up the network interfaces and define the public IPs. Also the machines are created, and then the initialize-node.sh script is called. In this script: 
hosts file is set up 
selinux is disabled 
iptables is disables 
hugepages are disabled 
NTPD is configured and started 
The Linux Integration Service driver is installed. This is a set of drivers that enable synthetic device support in supported Linux virtual machines under Hyper-V. 
Scratch directories are created 
Based on the node type the disks scripts are called (prepare-datanode-disks.sh or prepare-masternode-disks.sh) 
So what do the disks scripts do? These scripts prepares the machines with specific OS based tuning and calling prepare-datanode-disks.sh or prepare-masternode-disks.sh. They format and mount the different disks. For the data node the 10 data disks are mounted and  another disk is created for the parcels. 
A disk is created for the parcels of the Master Node, for the external PostgreSQL DB, the Zookeeper process, and the Quorum Journal manager process.  
After these scripts complete, we can start installing Cloudera on the machines. The setup-cloudera.json is called, initializing the installation by calling bootstrap-cloudera.sh. This script gathers the private IPs which should be used by the installation and then call initialize-cloudera-server.sh. This script only runs on the first master node, which will be the Cloudera Manager server. We need to install specific packages here, including Python to install the Hadoop daemons. Initialize-cloudera-server.sh then calls the database installation script (initialize-postgresql.sh), which installs a PostgreSQL database for the Cloudera related services (like activity monitor, service management, etc.) and also a separate database for Hive metastore. This separate database is used to store the schemas of the tables from Hive and Impala; the data itself resides in HDFS. 
After the database is installed, Cloudera Manager is started and as a last step the cmxDeployOnIbiza.sh script is called on the first masternode to install all the Hadoop daemons on different hosts. It's using Python to instruct Cloudera Manager though the Rest API to deploy the various components. 
Now you should have a running cluster. If you run the template in ‘Production’ mode you would get a Cloudera CDH 5.4.x installation, where the different Hadoop daemons would be placed on nodes in the following way: 
Fout bij het laden van [Afbeelding] 
The template also supports installing Sentry, HBase, Flume, Sqoop and KMS, but these are not enabled by default and they can’t be enabled by just setting a variable, so you would need to change the script to install these components too. 
Using an existing VNet/subnet 
We created the VNet separately, so we had to take out the part from the template which creates the VNet. This is in the shared-resouces.json file and it is the block which creates the  
type": "Microsoft.Network/virtualNetworks", 
 
Afbeelding  
Then we added a new variable called vNetResourceGroup in the azuredeploy.parameters.json 
Afbeelding 
and we made sure that this can be read by the template file. To achieve this we defined it in the azuredeploy.json and we also made sure that now the VnetID references this parameter: 
Afbeelding 
Next in the master-node.json and data-node.json we need to make sure that the subnet reference is actually made using the previously defined VnetID.  
Afbeelding 
If you look carefully you will notice that we actually do not have to send an extra parameter between the azuredeploy.json  and the master-node.json/data-node.json even though we did add a new parameter. This is because we added VNetID to the parameter group called networkSpec and this group is transferred to the needed template files. 
Use DNS to resolve host names 
To use the DNS server for forward and reverse lookup we had to set up /etc/resolv.conf on the Linux machines. For this we needed to IP addresses and hostnames of the DNS servers. We also needed to set the hostname properly, so we had to know the domain suffix. As a first step we made sure that all these parameters are defined in azuredeploy.parameters.json and understood by the azuredeploy.json template file: 
Afbeelding 
Afbeelding 
Next, we transferred the new parameters using the vmSpec complex variable in azuredeploy.json 
Afbeelding 
Now these parameters can be accessed by the master-node.json and data-node.json template files. So in these files we need to make sure that the parameters are transferred to the initialize-node.sh script file. We just defined extra command line arguments for the script. If you compare this script with the initial script you will see that we also deleted quite a few command-line arguments which were used for the Cloudera installation, which we are not doing with the template file. 
Afbeelding 
How does the initialize-node.sh script know if it is installing a data node or a master node? Well, if you look closely you see that the second argument transferred to this script is actually the node type. 
In the initialize-node.sh script we then read the command line arguments: 
Afbeelding 
So we can set up /etc/resolv.conf. To make sure that upon restart this won’t be overridden, we also created a dhclient-enter-hooks file. 
Afbeelding 
In the code snippet above you can also see how NTPD can be set to a new host and how you can disable IPv6. 
Deploying the (customized) template 
First before you start deploying you should check if you can start the requested machines using your Azure subscription account. The account by default has a core limit of 20. It is important to emphasize that quotas for resources in Azure Resource Groups are per-region accessible by your subscription. If you need to request a quota increase, you need to decide how many cores you want to use in which regions and then make a specific request for Azure Resource Group core quotas for the amounts and regions that you want. 
To install a Cloudera PoC environment with the template you would need at least 4 * 16 cores, if you only want 3 worker nodes. Each machine deployed by the Cloudera template is a DS14 machine which has 16 cores. 
If you do not want to change anything in the template you can easily deploy this using the Azure Marketplace. In this case you can just provide the parameters requested by the UI and you would end up with a running cluster. 
Fout bij het laden van [Afbeelding] 
If you change something in the template, like we did, you need to make sure that the changes are in a public GitHub repository, otherwise the deployment process won’t be able to access it. You can use parameters defined in the azuredeploy.parameters.json. This file contains sensitive information, so it should not be in the public GitHub repo. 
Alternatively, if you’re not comfortable in creating a public GitHub repository you could place the script files in Azure storage and provide storage account and key information. 
To be able to use your own template in GitHub, you need to modify the scriptsUri variable in azuredeploy.json 
Afbeelding 
Because we are not using the marketplace to deploy, we need to create a separate resource group where we place the created assets. This way it will be easier to modify and delete the resources inside this group. With the Azure CLI you can create a resource group the following way: 
azure group create -n "myResourceGroup" -l "West Europe" 
And then you can start deploying your cluster: 
azure group deployment create  -g myResourceGroup  -n "MyClouderaDeployment"  -f azuredeploy.json  -e azuredeploy-parameters.json 
Make sure that after you deploy you change the password of the user you just created to access the hosts and also the Cloudera Manager user password. Currently, passwords can be plainly seen in your deployment configuration on Azure. Also the parameters transferred to the shell scripts can be seen on the hosts in the /var/log/azure/..../extension.log. So here you would also see the password for Cloudera Manager. If you want to change this you should consider integrating Azure Key Vault into the scripts. (What is Azure Key Vault? https://azure.microsoft.com/en-us/documentation/articles/key-vault-whatis/) This way you would be able to use SSH-keys to access your machines. 
We decided to run the template without using Key Vault, just making sure that the given user isn’t allowed to log in with a password. Because we did not install Cloudera Manager with the template, we did not have to worry about that password.  
Summary 
The Cloudera Template is a great basis to provision a Hadoop cluster on Azure. If you do not have too many exotic requests you can use the template as is. You have the freedom and responsibility to maintain the machines and the cluster. The Cloudera distribution comes with all the tools you need to unlock value from your data in a secure way and with the Cloudera Manager you can manage the cluster. 
Even if you have are special requirements, the template is a great starting point and its not hard to modify it to your needs. 
About GoDataDriven 
GoDataDriven is a leading data science boutique from The Netherlands. Since 2009 GoDataDriven has been helping organizations becoming a data driven enterprise by offering custom services and standardized propositions, based on Open Source technology. The team consists of a unique combination of experienced Data Scientists, excellent Data Engineers, all with state-of-the-art know-how of technology. 
GoDataDriven is partner of Cloudera, Hortonworks, Microsoft, Confluent, Elastic, and Databricks.  
Clients of GoDataDriven include Wehkamp, Bol.com, KLM, ING, Rabobank, Bakkersland and NPO. 
Resources 
Azure Resource Manager overview - https://azure.microsoft.com/en-us/documentation/articles/resource-group-overview/ 
About images for virtual machines - https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-images/  
Azure Compute, Network, and Storage Providers under the Azure Resource Manager - https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-azurerm-versus-azuresm/ 
Connecting classic VNets to new VNets - https://azure.microsoft.com/en-us/documentation/articles/virtual-networks-arm-asm-s2s/ 
Understanding the temporary drive on Windows Azure Virtual Machines - http://blogs.msdn.com/b/mast/archive/2013/12/07/understanding-the-temporary-drive-on-windows-azure-virtual-machines.aspx  
Enterprise Data Hub: A New Way to Work with Data https://www.cloudera.com/content/dam/cloudera/Resources/PDF/solution-briefs/Cloudera-EDH-ExecutiveBrief.pdf  
Cloudera Glossary http://www.cloudera.com/content/www/en-us/documentation/enterprise/latest/topics/glossaries.html 

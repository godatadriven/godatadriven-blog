Title: Installing Cloudera on Azure (part 1 of 2)
Date: 2015-11-20 15:00
Slug: installing-cloudera-on-azure-1
Author: Tunde Alkemade, Alexander Bij, Walter van der Scheer
Excerpt: Recently, GoDataDriven pioneered with the Cloudera template to install a Cloudera cluster on Microsoft Azure. In this article we provide an introduction to a use-case, Cloudera, Microsoft Azure, several deployment modes and the architectural design. 
Template: article
Latex:

<span class="lead">
Recently, GoDataDriven pioneered with the Cloudera template to install a Cloudera cluster on Microsoft Azure. In this series of 2 articles we share our insights and experiences with installing Cloudera and modifying the template that Cloudera provides for the installation on MS Azure.
</span>

## Introduction
Processing large amounts of unstructured data requires serious computing power and also maintenance effort. As load on computing power typically fluctuates due to time and seasonal influences and/or processes running on certain times, a cloud solution like Microsoft Azure is a good option to be able to scale up easily and pay only for what is actually used. In this article we provide an introduction to our use-case, give some background on Cloudera as well as on Microsoft Azure, discuss the several deployment modes and the explain architectural design of the Cloudera cluster.

Earlier, on November 3rd 2015, GoDataDriven already presented a webinar about [running Cloudera on MS Azure](https://info.microsoft.com/WE-Azure-WBNR-FY16-11Nov-03-Running-Cloudera-on-Azure.html), which has been recorded and is available for viewing after [registration](https://info.microsoft.com/WE-Azure-WBNR-FY16-11Nov-03-Running-Cloudera-on-Azure.html). 

## The use-case: Data Science infrastructure for large European airport 

In order to explore and analyze data, one of the largest European airports approached GoDataDriven to set-up a pre-production environment with adequate security measures, robust enough for production load. Cloudera was selected as Hadoop distribution to be installed on MS Azure.

The first use-case to motivate the installation of Cloudera was to be able to leverage the computing mechanisms offered to do predictive maintenance of the airpots'assets. By collecting data from all the assets in the Cloudera cluster, the airport was able to develop predictive models for the maintenance based on power usage, visitor flow and sensor data. 

Being a long-standing Cloudera partner, GoDataDriven is one of the most experienced consultancy boutiques when it comes to setting up Cloudera clusters on all kinds of hosting platforms, but setting it up using the Azure cloud was a new challenge.

## Hadoop & Cloudera: a short introduction 
Apache Hadoop is a framework that allows distributed processing of large data sets across clusters of computers. It is designed to scale up by simply adding servers, thus immediately adding local computing power and storage. Rather than relying on the hardware to deliver high-availability, the library itself is designed to detect and handle failures on the application layer.  

[Cloudera](www.cloudera.com) is an active contributor to the Apache Hadoop project and provides an enterprise-ready distribution which bundles multiple open-source projects. The Cloudera enterprise data hub is a unified platform that can collect and store unlimited data cost-effectively and reliably, and enable diverse users to quickly gain value from that data through a collection of frameworks that span data processing, interactive analytics, and real-time serving applications. The Enterprise Data Hub makes it possible to deliver integrated analytic solutions for less cost and effort than ever before. 

Afbeelding 

The enterprise data hub comprises proprietary elements as well as many open source components like HDFS, YARN, MapReduce, Zookeeper, HBase, Spark, Hive, Impala, Pig, Sqoop, Cloudera Search and Navigator. For a description of all these components please [visit the Cloudera Glossary](http://www.cloudera.com/content/www/en-us/documentation/enterprise/latest/topics/glossaries.html).  

With all these components integrated and managed by one interface an organization can load and store all types of data, transform the data in a usable format, create workflows to easily explore the data and then run data-driven experiments and analysis over unlimited data.  

## Microsoft Azure: a short introduction 

[Microsoft Azure](https://azure.microsoft.com/nl-nl/) is a cloud service for both infrastructure-as-a-service (IaaS) and platform-as-a-service (PaaS), with data centers spanning the globe. The offering consists of several services, including virtual machines, virtual networks, and storage services, as well as higher-level services such as web applications and databases.  
 
## Relevant Azure services for Cloudera Enterprise deployments 
For Cloudera Enterprise deployments on Azure, the following service offerings are relevant:
<ul>
<li>**Azure Virtual Network (VNet)**, a logical network overlay that can include services and VMs and can be connected to your on-premise network through a VPN.Azure Virtual Machines: Images are used in Azure to provide a new virtual machine with an operating system. From one VM image you can provision multiple VMs. These virtual machines will run on the Hypervisor.</li>
<li>**Azure Storage**: Cloudera recommends Premium Storage, which stores data on the latest technology Solid State Drives (SSDs) instead of Hard Disk Drives. Cloudera recommends one storage account per node to be able to leverage higher IOPS.</li> 
<li>**Availability Sets**: Availability sets provide redundancy to your application, ensuring that during either a planned or unplanned maintenance event, at least one virtual machine will be available and meet the 99.95% Azure SLA.</li>
<li>**Network Security Groups**: Network Security Groups provide segmentation within a Virtual Network (VNet) as well as full control over traffic that ingresses or egresses a virtual machine in a VNet. It also helps achieve scenarios such as DMZs (demilitarized zones) to allow users to tightly secure backend services such as databases and application servers.</li>
</ul>

## Deployment modes 

At the moment Azure has two deployment modes available: 
<ol>
<li>ASM (Azure Service Management)</li>
<li>ARM (Azure Resource Manager)</li>
</ol>

The ASM API is the “old” or “classic” API , and correlates to the [web portal](http://manage.windowsazure.com). Azure Service Management is an XML-driven REST API, which adds some overhead to API calls, compared to JSON.  

The Azure Resource Manager (ARM) API is a JSON-driven REST API to interact with Azure cloud resources. Microsoft recommends deploying in ARM mode.  
 
One of the benefits of using the ARM API is that you can declare cloud resources as part of what’s called an “ARM JSON template.” An ARM JSON template is a specially-crafted JSON file that contains cloud resource definitions. Once the resources have been declared in the JSON template, the template file is deployed into a container called a Resource Group. An ARM Resource Group is a logical set of correlated cloud resources that roughly share a life span. Using the ARM mode you are able to deploy resources in parallel, which was a limitation in ASM. 
 
The new [Azure Ibiza Preview Portal](http://portal.azure.com) is used to provision Azure cloud resources with ARM. If you provision cloud resources using the “old” Azure Portal, they are provisioned through the ASM API. You are not limited to the portal to deploy your templates. You can use the PowerShell or the Azure command-line interface to manage all Azure resources and deploy complete templates. The Azure CLI is based on NodeJs and thereby available on all environments. Both ARM and ASM are modes which can be configured in the tool, which you can check "azure config" and change "azure config mode arm". 
 
When deciding which deployment model to use, you have to watch out, because resources deployed in the ASM mode cannot be seen by the resources deployed in the ARM mode by default. If you want to achieve this, you would need to [create a VPN tunnel between the two VNets](https://azure.microsoft.com/en-us/documentation/articles/virtual-networks-arm-asm-s2s/). 

Cloudera provides an ARM template which installs a Hadoop cluster, including OS and network tuning and Hadoop configuration tuning, decreasing deployment time and expertise needed. There is also an Azure VM image built and maintained by Cloudera which is used during deployment.  

## Architectural design 

Users and administrator use the VPN tunnel to be able to access the Azure environment. 

The GatewaySubnet is needed to be able to set up the Site2Site VPN between the client’s network and the Azure network where the Hadoop cluster resides. 

For user management we decided to set up two Active Directory servers, which are also Domain Name Server. These are placed in their own subnet.  

Because of the high traffic between all nodes in the cluster, the Hadoop machines are in their own subnet. You might wonder why, but let us explain shortly how HDFS works: When you write a file into HDFS, this file is split into blocks (block size is usually 128 MB) and these blocks are placed on the worker nodes (called Data nodes). Each block has a replication factor of 3. Only the master node (Namenode) knows which block belongs to which file. The Namenode does not store blocks, but it does maintain the active replication factor. If a client wants to read a file from HDFS, it will first contact the Namenode, get the location of the blocks and then read the blocks form the Datanodes. 
The Datanodes send heartbeats to the Namenodes and the when the active Namenode notices that a block hasn’t got the requested replication factor, it instructs another Datanode to copy that given block.  

So now you can see that there is a lot of traffic between the Namenode - Datanode and also between the Datanode – Datanode.  And here we only mentioned the communication between one component, HDFS. 

The architectural design is presented in the picture XXX.

Afbeelding 

We also have a ClientSubnet for the machines which can access the cluster. Users can connect to this machine, do their analysis, but are not able to SSH to the machines in the Hadoop subnet. 

By configuring single sign-on using the Active Directory and configuring SSO for the Hadoop services, users can use a single password everywhere.

## Modifying the Cloudera template

Now you have an overview of the relevant Azure services for Cloudera Enterprise deployments, deployment modes and the architectural design. In the next post we will motivate our choices on using the template or developing the implementation from scratch, and the actual modifications we made to the Cloudera template. 

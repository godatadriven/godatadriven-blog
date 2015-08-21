Title: Provision Linux machine on Azure
Date: 2015-08-21 18:00
Slug: azure-provision
Author: Alexander Bij
Excerpt: In this tutorial I'll explain some Azure and show you how to provision a CentOS node on Azure.
Template: article
Latex:

### Azure

Azure is the cloud environment from Microsoft. Creating resources in the cloud can be done using the [classic portal](https://manage.windowsazure.com/), the [new portal](https://portal.azure.com), the [PowerShell](https://github.com/Azure/azure-powershell), the [Azure-CLI](https://github.com/Azure/azure-xplat-cli) and some others.

The classic portal and the PowerShell have all the options available, which may be absent is the current version of the new portal or the Azure-CLI. For example moving a VM to another resourcegroup is not possible in the Azure-CLI at the moment.

### What does it cost?

- No upfront costs
- No termination fees
- Pay only what you use

For this excerise we use the A2 instances with are almost 9 cent an hour for 2 cores and 3.5 Gb mem and 60 Gb internal storage. Its charged by minutes. The bigger the machine, the more you pay. You don't pay for machines being stopped (Deallocated). 

More details about the VM costs are explained on [Azure VM Prizing](http://azure.microsoft.com/en-us/pricing/details/virtual-machines/#Linux).

When you want to attach more storage/disks you need to create an storage account. The [Azure Storage Prizing](http://azure.microsoft.com/en-us/pricing/details/storage/) depends on redundency, used size and type you choose.

### Install the Azule-CLI & connect

You can use homebrew (brew) on the mac to install NodeJS and azure-cli.

    :::shell
    brew install node // Mac only
    npm install -g azure-cli // -g means globally not in current directory

When creating an account on Azure you will get a trial subscription. For 30 days you'll have 150 euro's to spend on running instances. After you have created an account and a subscription you can get started using the 'azure' command to login:

    :::shell
    # Launch a browser to Azure portal, follow steps...
    azure account download
    azure account import <ThePublishSettingsFile>

These credentials from the publishSettingsFile will be usable for about a week, than it expires. If you want to clear you subscription(s) on your machine:

    :::shell
    azure account clear -q


### a Word on Modes

Currently Azure has two modes with do not work (well) together.

- ASM: Azure Service Manager (classic / XML)
- ARM: Azure Resource Manager (templates / JSON)

Good overview of the advantages of the [Azure Resource Manager](https://azure.microsoft.com/en-us/documentation/articles/virtual-machines-azurerm-versus-azuresm/) over the Azure Service Manager.

We have noticed that the ASM-mode locks during deployments. When creating a couple of VM's and attaching a couple of disks you have to wait for each command to complete. This will work a lot better in the ARM-mode were you can prepare templates and provision resources much faster.

In this post I'll pick the classic ASM-mode. When playing around with 2 nodes this is fine. When you want to provision more nodes with extra storage and configuration you should go for ARM-mode.

### Prepare your keys

You should create a new ssh key pair

    :::shell
    cd ~/.ssh
    mkdir azure
    ssh-keygen -f ~/.ssh/azure/azure-trail

> Never share your private key (azure-trail), use the public key (azure-trail.pub) for other machines to thrust you!

### ASM mode (classic)

When creating the first node in Azure a 'cloud service' is created. This is a <resource_group_name>.cloudapp.net on the public internet. So the name 'linuxnodes' might be in use.

    :::shell
    # Enable ASM (which is default)
    azure config mode asm

    # How to find latest image for CentOS available?
    azure vm image list | grep -i centos

    # Provision a linux node:
    azure vm create --vm-name linuxnode1 \
      --userName admin \
      --ssh 22 \
      --ssh-cert ~/.ssh/azure/azure-trail.pub \
      --no-ssh-password \
      --vm-size "Basic_A2" \
      --location "West Europe" \
      linuxnodes "5112500ae3b842c8b9c604889f8753c3__OpenLogic-CentOS-66-20150706"

What happened? Check the [new Azure portal](https://portal.azure.com) and explore!

 - A new storage account (linuxnode1-<stuff>.vhd) is created. 
 - A Resource Group (linuxnodes) is created.
 - A VM is created and started with CentOS 6.
 - An internal IP-address is assigned (Dynamic).
 - A public IP-address is assigned 
 - A domainname is created for these nodes. (linuxnodes.cloudapp.net)
 - An endpoint is created to connect from internet on port 22. We specified the public SSH-port, else Azure will pick a random port.


### Add another node

When adding another linux machine 'linuxnode2' using the same Resource Group and DNS name. The public address will be the same, so we need to change the public SSH-port number. The internal ssh port is still 22.

Use the **connect** command to attach to existing dns-name and resourcegroup 'linuxnodes'. The **location** command is not needed because it will use the same resource group.

    azure vm create --vm-name linuxnode2 \
      --userName admin \
      --ssh 23 \
      --ssh-cert ~/.ssh/azure/azure-trail.pub \
      --no-ssh-password \
      --vm-size "Basic_A2" \
      --connect \
      linuxnodes "5112500ae3b842c8b9c604889f8753c3__OpenLogic-CentOS-66-20150706"

### Connect
You can use a Mac / linux machine or use PuTTy on Windows to access your nodes.

    :::shell
    # ssh -i <privatekey> -p <port> <user@dns/ip>
    ssh -i ~/.ssh/azure/azure-trail -p 22 admin@linuxnodes.cloudapp.net
    # or port 23 for linuxnode2.

    # Become the superuser:
    sudo -i
    # And have fun...

### Clean Up, save money

If you stop the machines (deallocated) you are not charged anymore. You can do that through the Azure portal or by command

    :::shell
    azure vm shutdown linuxnode1
    azure vm shutdown linuxnode2

> note: the storage account will still cost little money.

From the azure portal you can remove the whole resource group [new Azure portal](https://portal.azure.com) in one go.

### Conclusion

I have showed you how to install and use the Azure-CLI shell and how to provision linux nodes in ASM-mode. This is the basis for a server under your own control. By default nothing is accessable from the scary internet except for the SSH port. By adding endpoints you can forward an port to the VM to access a server.


Greetings, Alexander Bij

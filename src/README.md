# Overview

This charm provides the Open Virtual Network (OVN) local controller, Open
vSwitch Database and Switch.

On successful deployment the unit will be enlisted as a `Chassis` in the OVN
network.

Open vSwitch bridges for integration, external Layer2 and Layer3 connectivity
is managed by the charm.

# Usage

OVN makes use of Public Key Infrastructure (PKI) to authenticate and authorize
control plane communication.  The charm requires a Certificate Authority to be
present in the model as represented by the `certificates` relation.

The [OpenStack Base bundle][openstack-base-bundle] gives an example of how you
can deploy OpenStack and OVN with [Vault][charm-vault] to automate certificate
lifecycle management.

## OpenStack support

When related to the [nova-compute][charm-nova-compute] charm the OVN Chassis
charm will enable services that provide [Nova Metadata][nova-metadata] to
instances.

## Network Spaces support

This charm supports the use of Juju Network Spaces.

By binding the `ovsdb` endpoint you can influence which interface will be used
for communication with the OVN Southbound DB as well as overlay traffic.

    juju deploy ovn-chassis --bind "ovsdb=internal-space"

By binding the `data` extra-binding you can influence which interface will be
used for overlay traffic.

    juju deploy ovn-chassis --bind "data=overlay-space"

## Port Configuration

Chassis port configuration is composed of a mapping between physical network
names to bridge names (`ovn-bridge-mappings`) and individual interface to
bridge names (`bridge-interface-mappings`).  There must be a match in both
configuration options before the charm will configure bridge and interfaces on
a unit.

The physical network name can be referenced when the administrator programs the
OVN logical flows, either by talking directly to the Northbound database, or by
interfaceing with a Cloud Management System (CMS).

Networks for use with external Layer3 connectivity should have mappings on
chassis located in the vicinity of the datacenter border gateways.  Having two
or more chassis with mappings for a Layer3 network will have OVN automatically
configure highly available routers with liveness detection provided by the
Bidirectional Forwarding Detection (BFD) protocol.

Chassis without direct external mapping to a external Layer3 network will
forward traffic through a tunnel to one of the chassis acting as a gateway for
that network.

> **Note**: It is not necessary nor recommended to add mapping for external
  Layer3 networks to all chassis.  Doing so will create a scaling problem at
  the physical network layer that needs to be resolved with globally shared
  Layer2 (does not scale) or tunneling at the top-of-rack switch layer (adds
  complexity) and is generally not a recommended configuration.

Networks for use with external Layer2 connectivity should have mappings present
on all chassis with potential to host the consuming payload.

## SR-IOV for networking support

Single root I/O virtualization (SR-IOV) enables splitting a single physical
network port into multiple virtual network ports known as virtual functions
(VFs).  The division is done at the PCI level which allows attaching the VF
directly to a virtual machine instance, bypassing the networking stack of the
hypervisor hosting the instance.

It is possible to configure chassis to prepare network interface cards (NICs)
for use with SR-IOV and make them available to OpenStack.

### Prerequisites

To use the feature you need to use a NIC with support for SR-IOV.

Machines need to be pre-configured with apropriate kernel command-line
parameters.  The charm does not handle this facet of configuration and it is
expected that the user configure this either manually or through the bare metal
provisioning layer (for example [MAAS][maas]).  Example:

    intel_iommu=on iommu=pt probe_vf=0

### Charm configuration

Enable SR-IOV, map physical network name 'physnet2' to the physical port named
`enp3s0f0` and create 4 virtual functions on it.

    juju config ovn-chassis enable-sriov=true
    juju config ovn-chassis sriov-device-mappings=physnet2:enp3s0f0
    juju config ovn-chassis sriov-numvfs=enp3s0f0:4

After enabling the virtual functions you should make note of the ``vendor_id``
and ``product_id`` of the virtual functions.

    juju run --application ovn-chassis 'lspci -nn | grep "Virtual Function"'
    03:10.0 Ethernet controller [0200]: Intel Corporation 82599 Ethernet Controller Virtual Function [8086:10ed] (rev 01)
    03:10.2 Ethernet controller [0200]: Intel Corporation 82599 Ethernet Controller Virtual Function [8086:10ed] (rev 01)
    03:10.4 Ethernet controller [0200]: Intel Corporation 82599 Ethernet Controller Virtual Function [8086:10ed] (rev 01)
    03:10.6 Ethernet controller [0200]: Intel Corporation 82599 Ethernet Controller Virtual Function [8086:10ed] (rev 01)

In the above example ``vendor_id`` is '8086' and ``product_id`` is '10ed'.

Add mapping between physical network name, physical port and Open vSwitch
bridge.

    juju config ovn-chassis ovn-bridge-mappings=physnet2:br-ex
    juju config ovn-chassis bridge-interface-mappings br-ex:a0:36:9f:dd:37:a8

> **Note**: The above configuration allows OVN to configure a 'external' port
  on one of the chassis for providing DHCP and metadata to instances connected
  directly to the network through SR-IOV.

For OpenStack to make use of the VFs the ``neutron-sriov-agent`` needs to talk
to RabbitMQ.

    juju add-relation ovn-chassis:amqp rabbitmq-server:amqp

OpenStack Nova also needs to know which PCI devices it is allowed to pass
through to instances.

    juju config nova-compute pci-passthrough-whitelist='{"vendor_id":"8086", "product_id":"10ed", "physical_network":"physnet2"}'

### Boot an instance

    openstack port create --network my-network --vnic-type direct my-port
    openstack server create --flavor my-flavor --key-name my-key \
        --nic port-id=<UUID OF THE PORT CREATED ABOVE> my-instance

## DPDK fast packet processing support

It is possible to configure chassis to use experimental DPDK userspace network
acceleration.

> **Note**: Currently instances are required to be attached to a external
  network (also known as provider network) for connectivity.  OVN supports
  distributed DHCP for provider networks.  For OpenStack workloads use of
  [Nova config drive][nova-config-drive] is required to provide metadata to
  instances when using DPDK.

### Prerequisites

To use the feature you need to use a supported CPU architecture
and network interface card (NIC) hardware.  Please consult the DPDK
[supported hardware page][dpdk-hardware].

Machines need to be pre-configured with apropriate kernel command-line
parameters.  The charm does not handle this facet of configuration and it is
expected that the user configure this either manually or through the bare metal
provisioning layer (for example [MAAS][maas]).  Example:

    default_hugepagesz=1G hugepagesz=1G hugepages=64 intel_iommu=on iommu=pt

For the communication between the userspace networking stack and the NIC driver
in a virtual machine instance to work the instances need to be configured to
use hugepages.  For OpenStack this can be accomplished by
[Customizing instance huge pages allocations][instance-huge-pages].
Example:

    $ openstack flavor set m1.large --property hw:mem_page_size=large

By default, the charm will configure Open vSwitch/DPDK to consume one processor
core + 1G of RAM from each NUMA node on the unit being deployed; this can be
tuned using the ``dpdk-socket-memory`` and ``dpdk-socket-cores`` configuration
options.  The userspace kernel driver can be configured using the
``dpdk-driver`` configuration option.  See config.yaml for more details.

> **Note**: Changing dpdk-socket-\* configuration options will trigger a
  restart of Open vSwitch, and subsequently interrupt instance connectivity.

## DPDK bonding

Once Network interface cards are bound to DPDK they will be invisible to the
standard Linux kernel network stack and subsequently it is not possible to use
standard system tools to configure bonding.

For DPDK interfaces the charm supports configuring bonding in Open vSwitch.
This is accomplished through the ``dpdk-bond-mappings`` and
``dpdk-bond-config`` configuration options.  Example:

    ovn-chassis:
      options:
        enable-dpdk: True
        bridge-interface-mappings: br-ex:dpdk-bond0
        dpdk-bond-mappings: "dpdk-bond0:00:53:00:00:00:42 dpdk-bond0:00:53:00:00:00:51"
        dpdk-bond-config: ":balance-slb:off:fast"

In this example, the network interface cards associated with the two MAC
addresses provided will be used to build a bond identified by a port named
'dpdk-bond0' which will be attached to the 'br-ex' bridge.


# Bugs

Please report bugs on [Launchpad][lp-ovn-chassis].

For general questions please refer to the OpenStack [Charm Guide][cg].

<!-- LINKS -->
[cg]: https://docs.openstack.org/charm-guide/latest/
[charm-nova-compute]: https://jaas.ai/nova-compute
[charm-vault]: https://jaas.ai/vault/
[dpdk-hardware]: http://core.dpdk.org/supported/
[lp-ovn-chassis]: https://bugs.launchpad.net/charm-ovn-chassis/+filebug
[maas]: https://maas.io/
[nova-config-drive]: https://docs.openstack.org/nova/latest/user/metadata.html#config-drives
[nova-metadata]: https://docs.openstack.org/nova/latest/user/metadata.html
[instance-huge-pages]: https://docs.openstack.org/nova/latest/admin/huge-pages.html#customizing-instance-huge-pages-allocations
[openstack-base-bundle]: https://github.com/openstack-charmers/openstack-bundles/blob/master/development/openstack-base-bionic-ussuri-ovn/bundle.yaml

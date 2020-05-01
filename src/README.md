# Overview

This charm provides the Open Virtual Network (OVN) local controller, Open
vSwitch Database and Switch.

On successful deployment the unit will be enlisted as a `Chassis` in the OVN
network.

Open vSwitch bridges for integration, external Layer2 and Layer3 connectivity
is managed by the charm.

> **Note**: The OVN charms are considered preview charms.

# Usage

OVN makes use of Public Key Infrastructure (PKI) to authenticate and authorize
control plane communication.  The charm requires a Certificate Authority to be
present in the model as represented by the `certificates` relation.

There is a [OVN overlay bundle](https://github.com/openstack-charmers/openstack-bundles/blob/master/development/overlays/openstack-base-ovn.yaml)
for use in conjunction with the [OpenStack Base bundle](https://github.com/openstack-charmers/openstack-bundles/blob/master/development/openstack-base-bionic-train/bundle.yaml)
which give an example of how you can automate certificate lifecycle management
with the help from [Vault](https://jaas.ai/vault/).

## OpenStack support

When related to the [nova-compute](https://jaas.ai/nova-compute) charm the OVN
Chassis charm will enable services that provide
[Nova Metadata](https://docs.openstack.org/nova/latest/user/metadata.html) to
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

## DPDK fast packet processing support

It is possible to configure chassis to use experimental DPDK userspace network
acceleration.

> **Note**: Currently instances are required to be attached to a external
  network (also known as provider network) for connectivity.  OVN supports
  distributed DHCP for provider networks.  For OpenStack workloads use of
  [Nova config drive](https://docs.openstack.org/nova/latest/user/metadata.html#config-drives)
  is required to provide metadata to instances.

### Prerequisites

To use the feature you need to use a supported CPU architecture
and network interface card (NIC) hardware.  Please consult the DPDK
[supported hardware page](http://core.dpdk.org/supported/).

Machines need to be pre-configured with apropriate kernel command-line
parameters.  The charm does not handle this facet of configuration and it is
expected that the user configure this either manually or through the bare metal
provisioning layer (for example [MAAS](https://maas.io/).  Example:

    default_hugepagesz=1G hugepagesz=1G hugepages=64 intel_iommu=on iommu=pt

For the communication between the userspace networking stack and the NIC driver
in a virtual machine instance to work the instances need to be configured to
use hugepages.  For OpenStack this can be accomplished by
[Customizing instance huge pages allocations](https://docs.openstack.org/nova/latest/admin/huge-pages.html#customizing-instance-huge-pages-allocations).
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

Please report bugs on [Launchpad](https://bugs.launchpad.net/charm-ovn-chassis/+filebug).

For general questions please refer to the OpenStack [Charm Guide](https://docs.openstack.org/charm-guide/latest/).

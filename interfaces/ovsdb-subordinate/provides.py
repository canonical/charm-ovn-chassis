# Copyright 2020 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import charms.reactive as reactive

# the reactive framework unfortunately does not grok `import as` in conjunction
# with decorators on class instance methods, so we have to revert to `from ...`
# imports
from charms.reactive import (
    Endpoint,
    when,
    when_not,
)

from .ovsdb_subordinate_common import hash_hexdigest


class OVSDBSubordinateProvides(Endpoint):
    """This interface is used on a principle charm to connect to subordinate
    """

    def _add_interface_request(self, bridge, ifname, ifdata):
        """Retrieve interface requests from relation and add/update requests

        :param bridge: Name of bridge
        :type bridge: str
        :param ifname: Name of interface
        :type ifname: str
        :param ifdata: Data to be attached to interface in Open vSwitch
        :type ifdata: Dict[str,Union[str,Dict[str,str]]]
        """
        for relation in self.relations:
            relation_ifs = relation.to_publish.get('create-interfaces', {})
            relation_ifs.update({bridge: {ifname: ifdata}})
            relation.to_publish['create-interfaces'] = relation_ifs

    def _interface_requests(self):
        """Retrieve interface requests from relation

        :returns: Current interface requests
        :rtype: Optional[Dict[str,Union[str,Dict[str,str]]]]
        """
        for relation in self.relations:
            return relation.to_publish_raw.get('create-interfaces')

    def create_interface(self, bridge, ifname, ethaddr, ifid):
        """Request system interface created and attach it to CMS

        Calls to this function are additive so a principle charm can request to
        have multiple interfaces created and maintained.

        The flag {endpoint_name}.{interface_name}.created will be set when
        ready.

        :param bridge: Bridge the new interface should be created on
        :type bridge: str
        :param ifname: Interface name we want the new netdev to get
        :type ifname: str
        :param ethaddr: Ethernet address we want to attach to the netdev
        :type ethaddr: str
        :param ifid: Unique identifier for port from CMS
        :type ifid: str
        """
        interface = {
            'type': 'internal',
            'external-ids': {
                'iface-id': ifid,
                'iface-status': 'active',
                'attached-mac': ethaddr,
            },
        }
        self._add_interface_request(bridge, ifname, interface)
        reactive.clear_flag(
            self.expand_name('{endpoint_name}.interfaces.created'))

    @when('endpoint.{endpoint_name}.joined')
    def joined(self):
        reactive.set_flag(self.expand_name('{endpoint_name}.connected'))
        reactive.set_flag(self.expand_name('{endpoint_name}.available'))

    @when_not('endpoint.{endpoint_name}.joined')
    def broken(self):
        reactive.clear_flag(self.expand_name('{endpoint_name}.available'))
        reactive.clear_flag(self.expand_name('{endpoint_name}.connected'))

    @when('endpoint.{endpoint_name}.changed.interfaces-created')
    def new_requests(self):
        ifreq = self._interface_requests()

        if ifreq is not None and self.all_joined_units.received[
                'interfaces-created'] == hash_hexdigest(ifreq):
            reactive.set_flag(
                self.expand_name('{endpoint_name}.interfaces.created'))
            reactive.clear_flag(
                self.expand_name(
                    'endpoint.{endpoint_name}.changed.interfaces-created'))

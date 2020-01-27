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

import subprocess

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


class OVSDBSubordinateRequires(Endpoint):
    """This interface is used on the subordinate side of the relation"""

    def _get_ovs_value(self, tbl, col, rec=None):
        """Get value of column in record in table

        :param tbl: Name of table
        :type tbl: str
        :param col: Name of column
        :type col: str
        :param rec: Record ID
        :type rec: Optional[str]
        :raises: subprocess.CalledProcessError
        """
        cp = subprocess.run(('ovs-vsctl', 'get', tbl, rec or '.', col),
                            stdout=subprocess.PIPE,
                            check=True, universal_newlines=True)
        return cp.stdout.rstrip().replace('"', '').replace("'", '')

    def publish_chassis_name(self):
        """Publish chassis name"""
        ovs_hostname = self._get_ovs_value('Open_vSwitch',
                                           'external_ids:hostname')
        for relation in self.relations:
            relation.to_publish['chassis-name'] = ovs_hostname

    def publish_ovn_configured(self):
        """Publish whether OVN is configured in the local OVSDB"""
        ovn_configured = False
        try:
            self._get_ovs_value('Open_vSwitch', 'external_ids:ovn-remote')
            ovn_configured = True
        except subprocess.CalledProcessError:
            # No OVN
            pass

        for relation in self.relations:
            relation.to_publish['ovn-configured'] = ovn_configured

    @property
    def interface_requests(self):
        """Retrieve current interface requests

        :returns: Current interface requests
        :rtype: Dict[str,Union[str,Dict[str,str]]]
        """
        return self.all_joined_units.received.get('create-interfaces', {})

    def interface_requests_handled(self):
        """Notify peer that interface requests has been dealt with

        Sets a hash of request data back on relation to signal to the other end
        it has been dealt with so it can proceed.

        Note that we do not use the reactive request response pattern library
        as we do not have use for per-unit granularity and we do not have
        actual useful data to return.
        """
        # The raw data is a json dump using sorted keys
        ifreq_hexdigest = hash_hexdigest(
            self.all_joined_units.received_raw['create-interfaces'])
        for relation in self.relations:
            relation.to_publish['interfaces-created'] = ifreq_hexdigest
        reactive.clear_flag(
            self.expand_name('{endpoint_name}.interfaces.new_requests'))

    @when('endpoint.{endpoint_name}.joined')
    def joined(self):
        self.publish_chassis_name()
        self.publish_ovn_configured()
        reactive.set_flag(self.expand_name('{endpoint_name}.connected'))
        reactive.set_flag(self.expand_name('{endpoint_name}.available'))

    @when_not('endpoint.{endpoint_name}.joined')
    def broken(self):
        reactive.clear_flag(self.expand_name('{endpoint_name}.available'))
        reactive.clear_flag(self.expand_name('{endpoint_name}.connected'))

    @when('endpoint.{endpoint_name}.changed.create-interfaces')
    def new_requests(self):
        reactive.set_flag(
            self.expand_name('{endpoint_name}.interfaces.new_requests'))
        reactive.clear_flag(
            self.expand_name(
                'endpoint.{endpoint_name}.changed.create-interfaces'))

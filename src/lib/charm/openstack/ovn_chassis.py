# Copyright 2019 Canonical Ltd
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

import charms_openstack.charm as charm
from charmhelpers.core import hookenv as che
import charms.ovn_charm
from lib.charm.openstack.basic_ipt_helper import BasicIPTHelper


charm.use_defaults('charm.default-select-release')


class OVNChassisCharm(charms.ovn_charm.DeferredEventMixin,
                      charms.ovn_charm.BaseOVNChassisCharm):
    # OpenvSwitch and OVN is distributed as part of the Ubuntu Cloud Archive
    # Pockets get their name from OpenStack releases.
    #
    # This defines the earliest version this charm can support, actually
    # installed version is selected by the principle charm.
    release = 'ussuri'
    name = 'ovn-chassis'

    # Setting an empty source_config_key activates special handling of release
    # selection suitable for subordinate charms
    source_config_key = ''

    # iptables helper
    ipt = BasicIPTHelper(che.log)

    def _get_chain_name(self):
        # This name cannot exceed 24 characters (2)
        return "juju-och-nfnotrack"

    def _get_temp_chain_name(self):
        temp_chain_suffix = "-temp"
        return self._get_chain_name() + temp_chain_suffix

    def _init_ipt_notrack_chain(self, chain_name, criterias):
        """ 
        Initialize a iptables NOTRACK rule chain with given criterias.
        """
        # Create new chain
        self.ipt.chain_create(chain_name)

        # Populate the chain with rules
        for criteria in criterias:
            self.ipt.chain_append_notrack_rule(chain_name, criteria)

        # Attach chain to PREROUTING & OUTPUT chains
        self.ipt.chain_attach_to(chain_name, "PREROUTING")
        self.ipt.chain_attach_to(chain_name, "OUTPUT")

    def _deinit_ipt_notrack_chain(self, chain_name):
        """
        Deinitialize a NOTRACK chain, if exist.
        """
        if self.ipt.chain_exist(chain_name):
            # Check if jump to chain_name exist in PREROUTING
            if self.ipt.check_rule_exist("-j {}".format(chain_name), "PREROUTING"):
                self.ipt.chain_detach_from(chain_name, "PREROUTING")
            # Check if jump to chain_name exist in OUTPUT
            if self.ipt.check_rule_exist("-j {}".format(chain_name), "OUTPUT"):
                self.ipt.chain_detach_from(chain_name, "OUTPUT")
            # A chain cannot de deleted while there are still rules on it
            # so, flush all the rules
            self.ipt.chain_flush(chain_name)
            # ... and delete the chain.
            self.ipt.chain_delete(chain_name)

    def remove_notrack_rules(self):
        """
        Remove iptables NOTRACK rules from the system.
        """
        che.status_set('maintenance', "Disabling iptables NOTRACK rules")

        self._deinit_ipt_notrack_chain(self._get_chain_name())
        self._deinit_ipt_notrack_chain(self._get_temp_chain_name())

    def configure_notrack_rules(self):
        """
        Configure iptables NOTRACK rules.

        :raises: 
            IptablesOpsError when an iptables operation fails
            IptablesInvalidRuleCriteria when an iptables rule criteria is invalid
        """

        if self.config['enable-notrack-rules']:
            che.status_set('maintenance', "Enabling iptables NOTRACK rules")

            # Delete the temp chain, if exist.
            self._deinit_ipt_notrack_chain(self._get_temp_chain_name())

            criterias = list(
                x for x in filter(None, self.config['notrack-rule-criteria'].split(";")))

            # Validate the sanity of the criterias first
            for criteria in criterias:
                # The chain name does not matter here, rule syntax errors
                # will be reported first.
                self.ipt.check_criteria_ok(
                    criteria, self._get_temp_chain_name())

            # NOTE(mustafakemalgilor): The code is populating a temp chain and attaching it to
            # PREROUTING & OUTPUT before decommisioning the old one. This is done for having a
            # graceful shift between different rule sets. This should allow us to have no `no-rule`
            # gaps during the rule chain update.

            self._init_ipt_notrack_chain(
                self._get_temp_chain_name(), criterias)

            # Decommission and delete previous chain, if exist
            self._deinit_ipt_notrack_chain(self._get_chain_name())

            # Rename `temp chain`` to `chain``
            self.ipt.chain_rename(
                self._get_temp_chain_name(), self._get_chain_name())
        else:
            self.remove_notrack_rules()

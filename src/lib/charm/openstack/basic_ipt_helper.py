# Copyright 2022 Canonical Ltd
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


class IptablesOpsError(Exception):
    """Thrown when an iptables operation is failed."""
    pass


class IptablesInvalidRuleCriteriaError(Exception):
    """Thrown when given criteria for iptables rule is invalid."""
    pass


class BasicIPTHelper:
    """Simple class to invoke common iptables operations."""

    def __init__(self, log=lambda x: x, ipt_cmd_name="iptables") -> None:
        self.log = log
        self.ipt_cmd_name = ipt_cmd_name

    def exec(self, cmd):
        """
        Execute a shell command, and return the exit code.

        :param str[] cmd: Command and parameters

        :returns: tuple that contains retcode, command output and command.
        :rtype: tuple(str, str, str)
        """
        proc = subprocess.Popen(
            cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _ = proc.communicate()
        return (proc.returncode, out, ' '.join(cmd))

    def chain_attach_to(self, chain_name, to_chain_name, table_name='raw'):
        """
        Attach `chain_name` to `to_chain_name` in table `table_name`.

        :param str chain_name: Name of the chain to attach
        :param str from_chain_name: Name of the chain to attach to
        :param str table_name: Name of the table to operate on, default `raw`

        :raises: 
            IptablesOpsError if attach fails.
        """
        self.log("ipt: attaching chain `{}` to `{}` in table `{}`".format(
            chain_name, to_chain_name, table_name))
        ec, out, cmdstr = self.exec(
            [self.ipt_cmd_name, "-t", table_name, "-A", to_chain_name, "-j", chain_name])

        if not (ec == 0):
            raise IptablesOpsError(
                "Could not attach iptables chain `{}` to chain `{}` in table `{}`, command: `{}`, error code: `{}`, command output: {}".format(chain_name, to_chain_name, table_name, cmdstr, ec, out))

    def chain_detach_from(self, chain_name, from_chain_name, table_name='raw'):
        """
        Detach `chain_name` from `to_chain_name` in table `table_name`.

        :param str chain_name: Name of the chain to detach
        :param str from_chain_name: Name of the chain to detach from
        :param str table_name: Name of the table to operate on, default `raw`

        :raises: 
            IptablesOpsError if detach fails.
        """
        self.log("ipt: detaching chain `{}` from `{}` in table `{}`".format(
            chain_name, from_chain_name, table_name))
        ec, out, cmdstr = self.exec(
            [self.ipt_cmd_name, "-t", table_name, "-D", from_chain_name, "-j", chain_name])

        if not (ec == 0):
            raise IptablesOpsError(
                "Could not detach iptables chain `{}` from chain `{}` in table `{}`, command: `{}`, error code: `{}`, command output: {}".format(chain_name, from_chain_name, table_name, cmdstr, ec, out))

    def chain_create(self, chain_name, table_name='raw'):
        """
        Create a new chain named `chain_name` in table `table_name`.

        :param str chain_name: Name for the new chain
        :param str table_name: Table to create chain in, default `raw`

        :raises: 
            IptablesOpsError if create fails.
        """
        self.log("ipt: creating chain `{}` in table `{}`".format(
            chain_name, table_name))
        ec, out, cmdstr = self.exec(
            [self.ipt_cmd_name, '-t', table_name, '-N', chain_name])

        if not (ec == 0):
            raise IptablesOpsError(
                "Could not create iptables chain `{}` in table `{}`, command: `{}`, error code: `{}`, command output: {}".format(chain_name, table_name, cmdstr, ec, out))

    def chain_exist(self, chain_name, table_name='raw'):
        """
        Check if a chain named `chain_name` exist in table `table_name`.

        :param str chain_name: Chain name
        :param str table_name: Table to look for chain, default `raw`

        """
        # iptables -t raw -n --list MYCHAINa
        self.log("ipt: checking if chain `{}` exist in table `{}`".format(
            chain_name, table_name))
        ec, out, cmdstr = self.exec(
            [self.ipt_cmd_name, '-t', table_name, '-L', chain_name])

        # iptables will return 0 if chain exist
        return ec == 0

    def chain_flush(self, chain_name, table_name='raw'):
        """
        Flush all rules in chain named `chain_name` in table `table_name`.

        :param str chain_name: Chain to flush
        :param str table_name: Table that contains the chain

        :raises: 
            IptablesOpsError if flush fails.
        """
        self.log("ipt: flushing chain `{}` in table `{}`".format(
            chain_name,  table_name))
        ec, out, cmdstr = self.exec(
            [self.ipt_cmd_name, '-t', table_name, '-F', chain_name])

        if not (ec == 0):
            raise IptablesOpsError(
                "Could not flush iptables chain `{}` in table `{}`, command: `{}`, error code: `{}`, command output: {}".format(chain_name, table_name, cmdstr, ec, out))

    def chain_delete(self, chain_name, table_name='raw'):
        """Delete chain named `chain_name` from table `table_name`.

        :param str chain_name: Chain to delete
        :param str table_name: Table that contains the chain

        :raises: 
            IptablesOpsError if delete fails.
        """
        self.log("ipt: deleting chain `{}` in table `{}`".format(
            chain_name, table_name))
        ec, out, cmdstr = self.exec(
            [self.ipt_cmd_name, '-t', table_name, '-X', chain_name])

        if not (ec == 0):
            raise IptablesOpsError(
                "Could not delete iptables chain `{}` in table `{}`, command: `{}`, error code: `{}`, command output: {}".format(chain_name, table_name, cmdstr, ec, out))

    def chain_append_notrack_rule(self, chain_name, criteria_str, table_name='raw', comment="This rule is managed by Juju. Do not modify."):
        """Append a new NOTRACK rule with criteria `criteria_str` to chain named `chain_name` in table `table_name`.

        :param str chain_name: Chain to append the rule
        :param str criteria_str: Criteria of the rule
        :param str table_name: Table that contains the chain

        :raises: 
            IptablesOpsError if rule append fails.
        """
        self.log("ipt: appending rule with criteria  `{}` to chain `{}` in table `{}`".format(
            criteria_str, chain_name, table_name))
        self.log(criteria_str.split(" ")[-1])
        ec, out, cmdstr = self.exec(
            [self.ipt_cmd_name, '-t', table_name, '-A', chain_name, *criteria_str.split(" "), "-j", "NOTRACK", "-m", "comment", "--comment", comment])

        if not (ec == 0):
            raise IptablesOpsError(
                "Could not append iptables rule with criteria `{}` to chain `{}` in table `{}`, command: `{}`,error code: `{}`, command output: {}".format(criteria_str, chain_name, table_name, cmdstr, ec, out))

    def chain_rename(self, chain_name, new_chain_name, table_name='raw'):
        """Rename chain named `chain_name` to `new_chain_name` in table `table_name`.

        :param str chain_name: Name of the chain to rename
        :param str new_chain_name: Desired chain name
        :param str table_name: Table that contains the chain

        :raises: 
            IptablesOpsError if rename fails.
        """
        self.log("ipt: renaming chain `{}` to `{}` in table `{}`".format(
            chain_name, new_chain_name, table_name))
        ec, out, cmdstr = self.exec([self.ipt_cmd_name, "-t",
                                     table_name, "-E", chain_name, new_chain_name])

        if not (ec == 0):
            raise IptablesOpsError(
                "Could not rename iptables chain `{}` to new name `{}` in table `{}`, command: `{}`, error code: `{}`, command output: {}".format(chain_name, new_chain_name, table_name, cmdstr, ec, out))

    def check_rule_exist(self, criteria_str, chain_name, table_name='raw'):
        """Check if a rule with `criteria_str` would be a valid rule in chain named `chain_name` in table `table_name`.

        :param str criteria_str: Rule criteria to check
        :param str chain_name: Name of the chain (to be used for checking)
        :param str table_name: Table that contains the chain

        :returns: true if at least one rule with criteria `criteria_str` exist in `chain_name`, `table_name`
                  false otherwise
        :rtype: bool
        """
        self.log("ipt: checking rule with criteria `{}` exist in chain `{}` and table `{}`".format(
            criteria_str, chain_name, table_name))
        ec, _, _ = self.exec(
            [self.ipt_cmd_name, '-t', table_name, '-C', chain_name, *criteria_str.split(" ")])

        return ec == 0

    def check_criteria_ok(self, criteria_str, chain_name, table_name='raw'):
        """Check if a rule with `criteria_str` would be a valid rule in chain named `chain_name` in table `table_name`.

        :param str criteria_str: Rule criteria to check
        :param str chain_name: Name of the chain (to be used for checking)
        :param str table_name: Table that contains the chain

        :raises: 
            IptablesInvalidRuleCriteriaError if given criteria is a valid criteria
        """
        self.log("ipt: checking criteria `{}`".format(criteria_str))
        ec, out, cmdstr = self.exec(
            [self.ipt_cmd_name, '-t', table_name, '-C', chain_name, *criteria_str.split(" ")])

        if (ec == 2):
            raise IptablesInvalidRuleCriteriaError(
                "Given iptables criteria `{}` for chain `{}` and table `{}` is not valid, command: `{}`, error code: `{}`, command output: {}".format(criteria_str, chain_name, table_name, cmdstr, ec, out))

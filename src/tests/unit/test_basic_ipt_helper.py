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

import unittest
from unittest import mock

from charm.openstack.basic_ipt_helper import BasicIPTHelper
from charm.openstack.basic_ipt_helper import IptablesOpsError
from charm.openstack.basic_ipt_helper import IptablesInvalidRuleCriteriaError


class BasicIPTHelperTestCase(unittest.TestCase):
    """Unit tests class for BasicIPTHelper."""
    pass

    def setUp(self) -> None:
        self.ipt = BasicIPTHelper(print, "not-iptables")
        return super().setUp()

    @mock.patch("charm.openstack.basic_ipt_helper.subprocess.Popen")
    def test_exec(self, mock_popen):
        """Test `exec()` invokes Popen() as intended."""
        handle = mock_popen()
        handle.communicate.return_value = ("stdout", "stderr")
        handle.returncode = 0
        ec, out, cmdstr = self.ipt.exec(["test-cmd", "-P", "param"])
        mock_popen.assert_called_with(
            ["test-cmd", "-P", "param"], shell=False, stdout=-1, stderr=-2)
        self.assertEqual(ec, 0)
        self.assertEqual(out, "stdout")
        self.assertEqual(cmdstr, "test-cmd -P param")

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (0, "out", "cmd"))
    def test_chain_attach_to(self, mock_exec):
        """Test `chain_attach_to` invokes `exec` with correct iptables command."""
        self.ipt.chain_attach_to("chain", "to_chain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-A", "to_chain", "-j", "chain"])
        mock_exec.return_value = lambda c: (1, "out", "cmd")

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (1, "out", "cmd"))
    def test_chain_attach_to_false_path(self, mock_exec):
        """Test `chain_attach_to` invokes `exec` with correct iptables command (false path)."""
        self.assertRaises(IptablesOpsError,  self.ipt.chain_attach_to,
                          "chain", "to_chain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-A", "to_chain", "-j", "chain"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (0, "out", "cmd"))
    def test_chain_detach_from(self, mock_exec):
        """Test `chain_detach_from` invokes `exec` with correct iptables command."""
        self.ipt.chain_detach_from("chain", "from_chain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-D", "from_chain", "-j", "chain"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (1, "out", "cmd"))
    def test_chain_detach_from_false_path(self, mock_exec):
        """Test `chain_detach_from` invokes `exec` with correct iptables command (false path)."""
        self.assertRaises(IptablesOpsError, self.ipt.chain_detach_from,
                          "chain", "from_chain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-D", "from_chain", "-j", "chain"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (0, "out", "cmd"))
    def test_chain_create(self, mock_exec):
        """Test `chain_create` invokes `exec` with correct iptables command."""
        self.ipt.chain_create("chain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-N", "chain"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (1, "out", "cmd"))
    def test_chain_create_false_path(self, mock_exec):
        """Test `chain_create` invokes `exec` with correct iptables command (false path)."""
        self.assertRaises(IptablesOpsError,
                          self.ipt.chain_create, "chain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-N", "chain"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (0, "out", "cmd"))
    def test_chain_flush(self, mock_exec):
        """Test if `chain_flush` invokes `exec` with correct iptables command."""
        self.ipt.chain_flush("chain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-F", "chain"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (1, "out", "cmd"))
    def test_chain_flush_false_path(self, mock_exec):
        """Test if `chain_flush` invokes `exec` with correct command (false path)."""
        self.assertRaises(IptablesOpsError,
                          self.ipt.chain_flush, "chain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-F", "chain"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (0, "out", "cmd"))
    def test_chain_delete(self, mock_exec):
        """Test if `chain_delete` invokes `exec` with correct iptables command."""
        self.ipt.chain_delete("chain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-X", "chain"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (1, "out", "cmd"))
    def test_chain_delete_false_path(self, mock_exec):
        """Test if `chain_delete` invokes `exec` with correct iptables command (false path)."""
        self.assertRaises(IptablesOpsError,
                          self.ipt.chain_delete, "chain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-X", "chain"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (0, "out", "cmd"))
    def test_chain_append_notrack_rule(self, mock_exec):
        """Test if `chain_append_notrack_rule` invokes `exec` with correct iptables command."""
        self.ipt.chain_append_notrack_rule(
            "chain", "-p udp --dport 6081", "tablename", "test_comment")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-A", "chain", *"-p udp --dport 6081".split(" "), "-j", "NOTRACK", "-m", "comment", "--comment", "test_comment"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (1, "out", "cmd"))
    def test_chain_append_rule_false_path(self, mock_exec):
        """Test if `chain_append_notrack_rule` invokes `exec` with correct iptables command (false path)."""
        self.assertRaises(IptablesOpsError, self.ipt.chain_append_notrack_rule,
                          "chain", "-p udp --dport 6081", "tablename", "test_comment")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-A", "chain", *"-p udp --dport 6081".split(" "), "-j", "NOTRACK", "-m", "comment", "--comment", "test_comment"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (0, "out", "cmd"))
    def test_chain_rename(self, mock_exec):
        """Test if `chain_rename` invokes `exec` with correct iptables command."""
        self.ipt.chain_rename("chain", "newchain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-E", "chain", "newchain"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (1, "out", "cmd"))
    def test_chain_rename_false_path(self, mock_exec):
        """Test if `chain_rename` invokes `exec` with correct iptables command (false path)."""
        self.assertRaises(IptablesOpsError, self.ipt.chain_rename,
                          "chain", "newchain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-E", "chain", "newchain"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (0, "out", "cmd"))
    def test_check_criteria_ok(self, mock_exec):
        """Test if `check_criteria_ok` invokes `exec` with correct iptables command."""
        self.ipt.check_criteria_ok("-p udp --dport 6081", "chain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-C", "chain", *"-p udp --dport 6081".split(" ")])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (2, "out", "cmd"))
    def test_check_criteria_ok_false_path(self, mock_exec):
        """Test if `check_criteria_ok` invokes `exec` with correct iptables command (false path)."""
        self.assertRaises(IptablesInvalidRuleCriteriaError,
                          self.ipt.check_criteria_ok, "-p udp --dport 6081", "chain", "tablename")
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-C", "chain", *"-p udp --dport 6081".split(" ")])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (0, "out", "cmd"))
    def test_chain_exist(self, mock_exec):
        """Test if `test_chain_exist` invokes `exec` with correct iptables command."""
        self.assertEqual(True, self.ipt.chain_exist("chain", "tablename"))
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-L", "chain"])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (1, "out", "cmd"))
    def test_chain_exist_false_path(self, mock_exec):
        """Test if `test_chain_exist` invokes `exec` with correct iptables command (false path)."""
        self.assertEqual(False, self.ipt.chain_exist("chain", "tablename"))
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-L", "chain"])


    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (0, "out", "cmd"))
    def test_check_rule_exist(self, mock_exec):
        """Test if `test_rule_exist` invokes `exec` with correct iptables command."""
        self.assertEqual(True, self.ipt.check_rule_exist("-p udp --dport 6081", "chain", "tablename"))
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-C", "chain", *"-p udp --dport 6081".split(" ")])

    @mock.patch("charm.openstack.basic_ipt_helper.BasicIPTHelper.exec", side_effect=lambda c: (1, "out", "cmd"))
    def test_check_rule_exist_false_path(self, mock_exec):
        """Test if `test_rule_exist` invokes `exec` with correct iptables command."""
        self.assertEqual(False, self.ipt.check_rule_exist("-p udp --dport 6081", "chain", "tablename"))
        mock_exec.assert_called_once_with(
            ["not-iptables", "-t", "tablename", "-C", "chain", *"-p udp --dport 6081".split(" ")])

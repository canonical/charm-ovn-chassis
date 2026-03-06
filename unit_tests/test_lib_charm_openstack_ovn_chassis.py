# Copyright 2026 Canonical Ltd
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

import os
import sys
import tempfile
import unittest

import mock


charms = sys.modules['charms']
charms.ovn_charm = mock.MagicMock()


class _DeferredEventMixin(object):
    pass


class _BaseOVNChassisCharm(object):

    @property
    def packages(self):
        return []

    def render_nrpe(self):
        return None


charms.ovn_charm.DeferredEventMixin = _DeferredEventMixin
charms.ovn_charm.BaseOVNChassisCharm = _BaseOVNChassisCharm
sys.modules['charms.ovn_charm'] = charms.ovn_charm

import lib.charm.openstack.ovn_chassis as ovn_chassis


class TestOVNChassisCharmMethods(unittest.TestCase):

    def setUp(self):
        self.target = ovn_chassis.OVNChassisCharm.__new__(
            ovn_chassis.OVNChassisCharm)

    def test_configure_ovn_controller_log_permissions_restart_on_change(self):
        with mock.patch.object(
            self.target, '_ensure_ovn_common_logrotate_create'
        ) as ensure_logrotate, mock.patch.object(
            self.target,
            '_ensure_ovn_controller_dropin',
            return_value=True,
        ) as ensure_dropin, mock.patch.object(
            ovn_chassis.subprocess, 'call'
        ) as subprocess_call, mock.patch.object(
            ovn_chassis, 'service_restart'
        ) as service_restart:
            self.target.configure_ovn_controller_log_permissions()

        ensure_logrotate.assert_called_once_with()
        ensure_dropin.assert_called_once_with()
        subprocess_call.assert_called_once_with(
            ['systemctl', 'daemon-reload'])
        service_restart.assert_called_once_with('ovn-controller')

    def test_configure_ovn_controller_log_permissions_no_restart_no_change(self):  # noqa: E501
        with mock.patch.object(
            self.target, '_ensure_ovn_common_logrotate_create'
        ) as ensure_logrotate, mock.patch.object(
            self.target,
            '_ensure_ovn_controller_dropin',
            return_value=False,
        ) as ensure_dropin, mock.patch.object(
            ovn_chassis.subprocess, 'call'
        ) as subprocess_call, mock.patch.object(
            ovn_chassis, 'service_restart'
        ) as service_restart:
            self.target.configure_ovn_controller_log_permissions()

        ensure_logrotate.assert_called_once_with()
        ensure_dropin.assert_called_once_with()
        subprocess_call.assert_not_called()
        service_restart.assert_not_called()

    def test_ensure_ovn_common_logrotate_create_adds_line(self):
        with tempfile.TemporaryDirectory() as td:
            logrotate_path = os.path.join(td, 'ovn-common')
            with open(logrotate_path, 'w') as fd:
                fd.write(
                    '/var/log/ovn/ovn-controller.log {\n'
                    '    daily\n'
                    '    postrotate\n'
                    '        /bin/true\n'
                    '    endscript\n'
                    '}\n')

            with mock.patch.object(
                ovn_chassis, 'OVN_COMMON_LOGROTATE', logrotate_path
            ), mock.patch.object(ovn_chassis, 'write_file') as write_file:
                changed = self.target._ensure_ovn_common_logrotate_create()

            self.assertTrue(changed)
            write_file.assert_called_once()
            args, kwargs = write_file.call_args
            self.assertEqual(args[0], logrotate_path)
            self.assertIn('create 0640 root adm\n    postrotate', args[1])
            self.assertEqual(kwargs.get('perms'), 0o644)

    def test_ensure_ovn_common_logrotate_create_no_change_if_present(self):
        with tempfile.TemporaryDirectory() as td:
            logrotate_path = os.path.join(td, 'ovn-common')
            with open(logrotate_path, 'w') as fd:
                fd.write(
                    '/var/log/ovn/ovn-controller.log {\n'
                    '    create 0640 root adm\n'
                    '    postrotate\n'
                    '        /bin/true\n'
                    '    endscript\n'
                    '}\n')

            with mock.patch.object(
                ovn_chassis, 'OVN_COMMON_LOGROTATE', logrotate_path
            ), mock.patch.object(ovn_chassis, 'write_file') as write_file:
                changed = self.target._ensure_ovn_common_logrotate_create()

            self.assertFalse(changed)
            write_file.assert_not_called()

    def test_ensure_ovn_controller_dropin_writes_when_missing(self):
        with tempfile.TemporaryDirectory() as td:
            dropin_dir = os.path.join(td, 'ovn-controller.service.d')
            dropin_file = os.path.join(dropin_dir, 'log-perms.conf')
            with mock.patch.object(
                ovn_chassis,
                'OVN_CONTROLLER_SYSTEMD_DROPIN_DIR',
                dropin_dir,
            ), mock.patch.object(
                ovn_chassis,
                'OVN_CONTROLLER_SYSTEMD_DROPIN_FILE',
                dropin_file,
            ), mock.patch.object(ovn_chassis, 'write_file') as write_file:
                changed = self.target._ensure_ovn_controller_dropin()

            self.assertTrue(changed)
            write_file.assert_called_once_with(
                dropin_file,
                ovn_chassis.OVN_CONTROLLER_SYSTEMD_DROPIN_CONTENT,
                perms=0o644,
            )

    def test_ovn_controller_dropin_uses_adm_group_and_permissions(self):
        self.assertIn(
            'ExecStartPost=/usr/bin/chown root:adm '
            '/var/log/ovn/ovn-controller.log\n',
            ovn_chassis.OVN_CONTROLLER_SYSTEMD_DROPIN_CONTENT,
        )
        self.assertIn(
            'ExecStartPost=/usr/bin/chmod 0640 '
            '/var/log/ovn/ovn-controller.log\n',
            ovn_chassis.OVN_CONTROLLER_SYSTEMD_DROPIN_CONTENT,
        )

    def test_ensure_ovn_controller_dropin_no_change_if_same(self):
        with tempfile.TemporaryDirectory() as td:
            dropin_dir = os.path.join(td, 'ovn-controller.service.d')
            dropin_file = os.path.join(dropin_dir, 'log-perms.conf')
            os.makedirs(dropin_dir, exist_ok=True)
            with open(dropin_file, 'w') as fd:
                fd.write(ovn_chassis.OVN_CONTROLLER_SYSTEMD_DROPIN_CONTENT)

            with mock.patch.object(
                ovn_chassis,
                'OVN_CONTROLLER_SYSTEMD_DROPIN_DIR',
                dropin_dir,
            ), mock.patch.object(
                ovn_chassis,
                'OVN_CONTROLLER_SYSTEMD_DROPIN_FILE',
                dropin_file,
            ), mock.patch.object(ovn_chassis, 'write_file') as write_file:
                changed = self.target._ensure_ovn_controller_dropin()

            self.assertFalse(changed)
            write_file.assert_not_called()

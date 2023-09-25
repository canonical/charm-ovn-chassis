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

import mock
import os
import tempfile

import reactive.ovn_chassis_handlers as handlers

import charms_openstack.test_utils as test_utils
import charm.openstack.ovn_chassis as ovn_chassis


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def setUp(self):
        super().setUp()

    def test_hooks(self):
        hook_set = {
            'when_not': {
                'enable_ovn_chassis_handlers': ('MOCKED_FLAG',),
                'configure_deferred_restarts': ('is-update-status-hook',),
            },
        }
        # test that the hooks were registered via the
        # reactive.ovn_handlers
        self.registered_hooks_test_helper(handlers, hook_set, {})


class TestOvnHandlers(test_utils.PatchHelper):

    def test_enable_ovn_chassis_handlers(self):
        self.patch_object(handlers.reactive, 'set_flag')
        handlers.enable_ovn_chassis_handlers()
        self.set_flag.assert_called_once_with('MOCKED_FLAG')

    def test_render_nrpe(self):
        with tempfile.TemporaryDirectory() as dtmp:
            os.environ['CHARM_DIR'] = dtmp
            self.patch_object(ovn_chassis.nrpe, 'NRPE')
            self.patch_object(ovn_chassis.nrpe, 'add_init_service_checks')
            self.target.render_nrpe()
            # Note that this list is valid for Ussuri
            self.add_init_service_checks.assert_has_calls([
                mock.call().add_init_service_checks(
                    mock.ANY,
                    ['ovn-northd', 'ovn-ovsdb-server-nb',
                     'ovn-ovsdb-server-sb'],
                    mock.ANY
                ),
            ])
            self.NRPE.assert_has_calls([
                mock.call().write(),
            ])

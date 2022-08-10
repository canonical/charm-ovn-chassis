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
import charms.reactive as reactive
import charms_openstack.charm as charm

from . import ovn_chassis_charm_handlers


# Clear configured flag if notrack rule related configuration changes
reactive.register_trigger(when='config.changed.enable-notrack-rules',
                          clear_flag='iptables.notrack.configured')
reactive.register_trigger(when='config.changed.notrack-rule-criteria',
                          clear_flag='iptables.notrack.configured')


@reactive.when_not(ovn_chassis_charm_handlers.OVN_CHASSIS_ENABLE_HANDLERS_FLAG)
def enable_ovn_chassis_handlers():
    reactive.set_flag(
        ovn_chassis_charm_handlers.OVN_CHASSIS_ENABLE_HANDLERS_FLAG)


@reactive.when_not('is-update-status-hook')
def configure_deferred_restarts():
    with charm.provide_charm_instance() as instance:
        instance.configure_deferred_restarts()


@reactive.when_not('iptables.notrack.configured')
def configure_notrack_rules():
    with charm.provide_charm_instance() as instance:
        instance.configure_notrack_rules()
        reactive.set_flag("iptables.notrack.configured")


@reactive.hook('stop')
def on_stop():
    """Default handler for stop.
    """
    with charm.provide_charm_instance() as instance:
        instance.remove_notrack_rules()

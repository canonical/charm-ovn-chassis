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

import os
import subprocess

from charmhelpers.core.host import rsync, service_restart, write_file
from charmhelpers.contrib.charmsupport import nrpe
import charmhelpers.fetch as ch_fetch

import charms_openstack.charm as charm

import charms.ovn_charm

NAGIOS_PLUGINS = '/usr/local/lib/nagios/plugins'
SCRIPTS_DIR = '/usr/local/bin'
CERTCHECK_CRONFILE = '/etc/cron.d/ovn-chassis-cert-checks'
CRONJOB_CMD = "{schedule} root {command} 2>&1 | logger -p local0.notice\n"
OVN_COMMON_LOGROTATE = '/etc/logrotate.d/ovn-common'
OVN_CONTROLLER_SYSTEMD_DROPIN_DIR = \
    '/etc/systemd/system/ovn-controller.service.d'
OVN_CONTROLLER_SYSTEMD_DROPIN_FILE = \
    '{}/log-perms.conf'.format(OVN_CONTROLLER_SYSTEMD_DROPIN_DIR)
OVN_CONTROLLER_SYSTEMD_DROPIN_CONTENT = """[Service]
ExecStartPre=/usr/bin/mkdir -p /var/log/ovn
ExecStartPre=/usr/bin/touch /var/log/ovn/ovn-controller.log
ExecStartPost=/usr/bin/chown root:adm /var/log/ovn/ovn-controller.log
ExecStartPost=/usr/bin/chmod 0640 /var/log/ovn/ovn-controller.log
"""


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

    # packages needed by nrpe checks
    nrpe_packages = ['python3-cryptography']

    # Setting an empty source_config_key activates special handling of release
    # selection suitable for subordinate charms
    source_config_key = ''

    @property
    def packages(self):
        return super().packages + self.nrpe_packages

    def render_nrpe(self):
        hostname = nrpe.get_nagios_hostname()
        self.add_nrpe_certs_check(nrpe.NRPE(hostname=hostname))
        super().render_nrpe()

    def add_nrpe_certs_check(self, charm_nrpe):
        script = 'nrpe_check_ovn_certs.py'
        src = os.path.join(os.getenv('CHARM_DIR'), 'files', 'nagios', script)
        dst = os.path.join(NAGIOS_PLUGINS, script)
        rsync(src, dst)
        charm_nrpe.add_check(
            shortname='check_ovn_certs',
            description='Check that ovn certs are valid.',
            check_cmd=script
        )
        # Need to install this as a system package since it is needed by the
        # cron script that runs outside of the charm.
        ch_fetch.apt_install(['python3-cryptography'])
        script = 'check_ovn_certs.py'
        src = os.path.join(os.getenv('CHARM_DIR'), 'files', 'scripts', script)
        dst = os.path.join(SCRIPTS_DIR, script)
        rsync(src, dst)
        cronjob = CRONJOB_CMD.format(
            schedule='*/15 * * * *',
            command=dst)
        write_file(CERTCHECK_CRONFILE, cronjob)

    def configure_ovn_controller_log_permissions(self):
        """Ensure ovn-controller log file permissions remain rsyslog readable.

        This applies two safeguards:
        1) add ``create 0640 root adm`` before ``postrotate`` in
           ``/etc/logrotate.d/ovn-common`` (if missing)
        2) install a systemd drop-in for ``ovn-controller`` to enforce
           log permissions on service start.
        """
        self._ensure_ovn_common_logrotate_create()
        if self._ensure_ovn_controller_dropin():
            subprocess.call(['systemctl', 'daemon-reload'])
            service_restart('ovn-controller')

    def _ensure_ovn_common_logrotate_create(self):
        """Add ``create 0640 root adm`` before ``postrotate`` if missing."""
        if not os.path.exists(OVN_COMMON_LOGROTATE):
            return False

        with open(OVN_COMMON_LOGROTATE) as fd:
            content = fd.read()

        if 'create 0640 root adm' in content:
            return False

        lines = content.splitlines(True)
        for idx, line in enumerate(lines):
            if line.strip().startswith('postrotate'):
                indent = line[:len(line) - len(line.lstrip())]
                lines.insert(
                    idx,
                    '{}create 0640 root adm\n'.format(indent),
                )
                new_content = ''.join(lines)
                write_file(OVN_COMMON_LOGROTATE, new_content, perms=0o644)
                return True

        return False

    def _ensure_ovn_controller_dropin(self):
        """Create / update ovn-controller systemd drop-in."""
        os.makedirs(OVN_CONTROLLER_SYSTEMD_DROPIN_DIR, exist_ok=True)

        if os.path.exists(OVN_CONTROLLER_SYSTEMD_DROPIN_FILE):
            with open(OVN_CONTROLLER_SYSTEMD_DROPIN_FILE) as fd:
                current = fd.read()
            if current == OVN_CONTROLLER_SYSTEMD_DROPIN_CONTENT:
                return False

        write_file(
            OVN_CONTROLLER_SYSTEMD_DROPIN_FILE,
            OVN_CONTROLLER_SYSTEMD_DROPIN_CONTENT,
            perms=0o644,
        )
        return True

import logging

import zaza.openstack.utilities.openstack as openstack


def remove_security_group_rules_with_remote_group():
    keystone_session = openstack.get_overcloud_keystone_session()
    keystone_client = openstack.get_keystone_session_client(keystone_session)
    neutron_client = openstack.get_neutron_session_client(
        keystone_session)

    token_data = keystone_client.tokens.get_token_data(
        keystone_session.get_token())
    project_id = token_data['token']['project']['id']
    for sg in neutron_client.list_security_groups(
            project_id=project_id).get('security_groups', []):
        if sg['name'] != 'default':
            continue
        for rule in neutron_client.list_security_group_rules(
                remote_group_id=sg['id']).get('security_group_rules', []):
            logging.info('Removing security group with remote group: "{}"'
                         .format(rule['id']))
            neutron_client.delete_security_group_rule(rule['id'])

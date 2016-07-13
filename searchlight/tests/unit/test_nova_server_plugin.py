# Copyright 2015 Hewlett-Packard Corporation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import datetime
import mock
import novaclient.exceptions
import novaclient.v2.servers as novaclient_servers

from searchlight.elasticsearch.plugins.nova import\
    servers as servers_plugin
from searchlight.elasticsearch import ROLE_USER_FIELD
import searchlight.tests.unit.utils as unit_test_utils
import searchlight.tests.utils as test_utils


USER1 = u'27f4d76b-be62-4e4e-aa33bb11cc55'

TENANT1 = u'4d64ac83-87af-4d2a-b884-cc42c3e8f2c0'
TENANT2 = u'c6993374-7c4b-4f18-b317-85e3acdfd259'

# Instances
ID1 = u'6c41b4d1-f0fa-42d6-9d8d-e3b99695aa69'
ID2 = u'08ca6c43-eea8-48d0-bbb2-30c50109d5d8'
ID3 = u'a380287d-1f61-4887-959c-8c5ab8f75f8f'


flavor1 = {
    u'id': '1',
    u'links': [{
        u'href': u'http://localhost:8774/dontcare',
        u'rel': u'bookmark'
    }]
}
flavor2 = {
    u'id': '2',
    u'links': [{
        u'href': u'http://localhost:8774/stilldontcare',
        u'rel': u'bookmark'
    }]
}

imagea = {
    u'id': u'a',
    u'links': [{
        u'href': u'http://localhost:8774/dontcare',
        u'rel': u'bookmark'
    }]
}
imageb = {
    u'id': u'b',
    u'links': [{
        u'href': u'http://localhost:8774/dontcare',
        u'rel': u'bookmark'
    }]
}

net_ip4_6 = {
    u'net4_6': [
        {
            u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:1e:37:32',
            u'version': 4,
            u'addr': u'0.0.0.0',
            u'OS-EXT-IPS:type': u'fixed'
        },
        {
            u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:1e:37:32',
            u'version': 6,
            u'addr': u'::1',
            u'OS-EXT-IPS:type': u'fixed'
        }
    ],
    u'net4': [
        {
            u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:1e:37:32',
            u'version': 4,
            u'addr': u'127.0.0.1',
            u'OS-EXT-IPS:type': u'fixed'
        }
    ]
}

fake_version_list = [test_utils.FakeVersion('2.1'),
                     test_utils.FakeVersion('2.1')]

net_ipv4 = {u'net4': [dict(net_ip4_6[u'net4'][0])]}

_now = datetime.datetime.utcnow()
_five_minutes_ago = _now - datetime.timedelta(minutes=5)
created_now = _five_minutes_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
updated_now = _now.strftime('%Y-%m-%dT%H:%M:%SZ')

nova_server_getter = 'novaclient.v2.client.servers.ServerManager.get'
nova_version_getter = 'novaclient.v2.client.versions.VersionManager.list'


def _instance_fixture(instance_id, name, tenant_id, **kwargs):
    # A full nova v2 server.get output
    attrs = {
        u'OS-DCF:diskConfig': u'MANUAL',
        u'OS-EXT-AZ:availability_zone': u'nova',
        u'OS-EXT-SRV-ATTR:host': u'devstack',
        u'OS-EXT-SRV-ATTR:hypervisor_hostname': u'devstack',
        u'OS-EXT-SRV-ATTR:instance_name': u'instance-00000001',
        u'OS-EXT-STS:power_state': 1,
        u'OS-EXT-STS:task_state': None,
        u'OS-EXT-STS:vm_state': u'active',
        u'OS-SRV-USG:launched_at': created_now,
        u'OS-SRV-USG:terminated_at': None,
        u'accessIPv4': u'',
        u'accessIPv6': u'',
        u'addresses': {
            u'public': [{
                u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:1e:37:32',
                u'OS-EXT-IPS:type': u'fixed',
                u'addr': u'172.25.0.3',
                u'version': 4
            }, {
                u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:1e:37:32',
                u'OS-EXT-IPS:type': u'fixed',
                u'addr': u'2001:db8::3',
                u'version': 6
            }]
        },
        u'config_drive': u'True',
        u'created': created_now,
        u'flavor': {
            u'id': u'1',
            u'links': [{
                u'href': u'http://localhost:8774/dontcare',
                u'rel': u'bookmark'
            }]
        },
        u'hostId': u'd86d2c042a1f233227f70c5e9d2c5829de98d222d0922f469054ac17',
        u'id': instance_id,
        u'image': {
            u'id': u'46b77e67-ce40-44ca-823d-e6f83489f21e',
            u'links': [{
                u'href': u'http://localhost:8774/dontcare',
                u'rel': u'bookmark'
            }]
        },
        u'key_name': u'key',
        u'links': [
            {
                u'href': u'http://localhost:8774/dontcare',
                u'rel': u'self'
            },
            {
                u'href': u'http://localhost:8774/dontcare',
                u'rel': u'bookmark'
            }
        ],
        u'metadata': {},
        u'name': name,
        u'os-extended-volumes:volumes_attached': [],
        u'progress': 0,
        u'security_groups': [{u'name': u'default'}],
        u'status': u'ACTIVE',
        u'tenant_id': tenant_id,
        u'updated': updated_now,
        u'user_id': USER1}

    attrs.update(kwargs)
    server = mock.Mock(spec=novaclient_servers.Server, **attrs)
    server.to_dict.return_value = attrs
    return server


class TestServerLoaderPlugin(test_utils.BaseTestCase):
    def setUp(self):
        super(TestServerLoaderPlugin, self).setUp()
        self.plugin = servers_plugin.ServerIndex()
        self._create_fixtures()

    def _create_fixtures(self):
        self.instance1 = _instance_fixture(
            ID1, u'instance1', tenant_id=TENANT1,
            flavor=flavor1, image=imagea, addresses=net_ipv4,
            **{u'OS-EXT-AZ:availability_zone': u'az1',
               u'OS-EXT-SRV-ATTR:host': u'host1',
               u'hostId': u'host1'})
        self.instance2 = _instance_fixture(
            ID2, 'instance2', tenant_id=TENANT2,
            flavor=flavor2, image=imageb, addresses=net_ip4_6)
        self.instances = [self.instance1, self.instance2]

    def test_index_name(self):
        self.assertEqual('searchlight', self.plugin.resource_group_name)

    def test_document_type(self):
        self.assertEqual('OS::Nova::Server', self.plugin.get_document_type())

    @mock.patch(nova_version_getter, return_value=fake_version_list)
    def test_serialize(self, mock_version):
        expected = {
            u'OS-DCF:diskConfig': u'MANUAL',
            u'OS-EXT-AZ:availability_zone': u'az1',
            u'OS-EXT-SRV-ATTR:host': u'host1',
            u'OS-EXT-SRV-ATTR:hypervisor_hostname': u'devstack',
            u'OS-EXT-SRV-ATTR:instance_name': u'instance-00000001',
            u'OS-EXT-STS:power_state': 1,
            u'OS-EXT-STS:task_state': None,
            u'OS-EXT-STS:vm_state': u'active',
            u'OS-SRV-USG:launched_at': created_now,
            u'OS-SRV-USG:terminated_at': None,
            u'accessIPv4': u'',
            u'accessIPv6': u'',
            u'addresses': {
                u'public': [{
                    u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:1e:37:32',
                    u'OS-EXT-IPS:type': u'fixed',
                    u'addr': u'172.25.0.3',
                    u'version': 4
                }, {
                    u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:1e:37:32',
                    u'OS-EXT-IPS:type': u'fixed',
                    u'addr': u'2001:db8::3',
                    u'version': 6
                }]
            },
            u'config_drive': u'True',
            u'flavor': {u'id': u'1'},
            u'hostId': u'host1',
            u'id': u'6c41b4d1-f0fa-42d6-9d8d-e3b99695aa69',
            u'image': {u'id': u'a'},
            u'key_name': u'key',
            u'metadata': {},
            u'name': u'instance1',
            u'os-extended-volumes:volumes_attached': [],
            u'owner': u'4d64ac83-87af-4d2a-b884-cc42c3e8f2c0',
            u'security_groups': [u'default'],
            u'status': u'ACTIVE',
            u'tenant_id': u'4d64ac83-87af-4d2a-b884-cc42c3e8f2c0',
            u'project_id': u'4d64ac83-87af-4d2a-b884-cc42c3e8f2c0',
            u'updated': updated_now,
            u'user_id': u'27f4d76b-be62-4e4e-aa33bb11cc55',
            u'networks': [{
                u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:1e:37:32',
                u'version': 4,
                u'ipv4_addr': u'127.0.0.1',
                u'OS-EXT-IPS:type': u'fixed',
                u'name': u'net4',
            }],
            u'addresses': net_ipv4,
            u'created': created_now,
            u'created_at': created_now,
            u'updated': updated_now,
            u'updated_at': updated_now,
        }
        with mock.patch(nova_server_getter, return_value=self.instance1):
            serialized = self.plugin.serialize(self.instance1.id)

        self.assertEqual(expected, serialized)

    @mock.patch(nova_version_getter, return_value=fake_version_list)
    def test_serialize_no_image(self, mock_version):
        instance = _instance_fixture(
            ID3, u'instance3', tenant_id=TENANT1,
            flavor=flavor1, image='', addresses=net_ipv4,
            **{u'OS-EXT-AZ:availability_zone': u'az1',
               u'OS-EXT-SRV-ATTR:host': u'host1',
               u'hostId': u'host1'})
        expected = {
            u'OS-DCF:diskConfig': u'MANUAL',
            u'OS-EXT-AZ:availability_zone': u'az1',
            u'OS-EXT-SRV-ATTR:host': u'host1',
            u'OS-EXT-SRV-ATTR:hypervisor_hostname': u'devstack',
            u'OS-EXT-SRV-ATTR:instance_name': u'instance-00000001',
            u'OS-EXT-STS:power_state': 1,
            u'OS-EXT-STS:task_state': None,
            u'OS-EXT-STS:vm_state': u'active',
            u'OS-SRV-USG:launched_at': created_now,
            u'OS-SRV-USG:terminated_at': None,
            u'accessIPv4': u'',
            u'accessIPv6': u'',
            u'addresses': {
                u'public': [{
                    u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:1e:37:32',
                    u'OS-EXT-IPS:type': u'fixed',
                    u'addr': u'172.25.0.3',
                    u'version': 4
                }, {
                    u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:1e:37:32',
                    u'OS-EXT-IPS:type': u'fixed',
                    u'addr': u'2001:db8::3',
                    u'version': 6
                }]
            },
            u'config_drive': u'True',
            u'flavor': {u'id': u'1'},
            u'hostId': u'host1',
            u'id': u'a380287d-1f61-4887-959c-8c5ab8f75f8f',
            u'key_name': u'key',
            u'metadata': {},
            u'name': u'instance3',
            u'os-extended-volumes:volumes_attached': [],
            u'owner': u'4d64ac83-87af-4d2a-b884-cc42c3e8f2c0',
            u'project_id': u'4d64ac83-87af-4d2a-b884-cc42c3e8f2c0',
            u'security_groups': [u'default'],
            u'status': u'ACTIVE',
            u'tenant_id': u'4d64ac83-87af-4d2a-b884-cc42c3e8f2c0',
            u'updated': updated_now,
            u'user_id': u'27f4d76b-be62-4e4e-aa33bb11cc55',
            u'networks': [{
                u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:1e:37:32',
                u'version': 4,
                u'ipv4_addr': u'127.0.0.1',
                u'OS-EXT-IPS:type': u'fixed',
                u'name': u'net4',
            }],
            u'addresses': net_ipv4,
            u'created': created_now,
            u'created_at': created_now,
            u'updated': updated_now,
            u'updated_at': updated_now,
        }
        with mock.patch(nova_server_getter, return_value=instance):
            serialized = self.plugin.serialize(instance.id)

        self.assertEqual(expected, serialized)

    def test_facets_non_admin(self):
        mock_engine = mock.Mock()
        self.plugin.engine = mock_engine
        # Don't care about the actual aggregation result; the base functions
        # are tested separately.
        mock_engine.search.return_value = {'aggregations': {}}

        fake_request = unit_test_utils.get_fake_request(
            USER1, TENANT1, '/v1/search/facets', is_admin=False
        )

        facets = self.plugin.get_facets(fake_request.context)
        facet_names = [f['name'] for f in facets]

        network_facets = ('name', 'version', 'ipv6_addr', 'ipv4_addr',
                          'OS-EXT-IPS-MAC:mac_addr', 'OS-EXT-IPS:type')
        expected_facet_names = [
            'OS-EXT-AZ:availability_zone', 'created_at', 'description',
            'flavor.id', 'id', 'image.id', 'locked', 'name',
            'owner', 'security_groups', 'status', 'tags', 'updated_at',
            'user_id']
        expected_facet_names.extend(['networks.' + f for f in network_facets])

        self.assertEqual(set(expected_facet_names), set(facet_names))

        # Test fields with options
        complex_facet_option_fields = (
            'image.id', 'flavor.id', 'networks.name',
            'networks.OS-EXT-IPS:type', 'networks.version')
        aggs = dict(unit_test_utils.complex_facet_field_agg(name)
                    for name in complex_facet_option_fields)

        simple_facet_option_fields = (
            'status', 'OS-EXT-AZ:availability_zone', 'security_groups',
            'locked'
        )
        aggs.update(dict(unit_test_utils.simple_facet_field_agg(name)
                         for name in simple_facet_option_fields))

        expected_agg_query = {
            'aggs': aggs,
            'query': {
                'filtered': {
                    'filter': {
                        'and': [
                            {'term': {ROLE_USER_FIELD: 'user'}},
                            {'term': {'tenant_id': TENANT1}}
                        ]
                    }
                }
            }
        }
        mock_engine.search.assert_called_with(
            index=self.plugin.alias_name_search,
            doc_type=self.plugin.get_document_type(),
            body=expected_agg_query,
            ignore_unavailable=True,
            size=0
        )

    def test_facets_admin(self):
        mock_engine = mock.Mock()
        self.plugin.engine = mock_engine
        mock_engine.search.return_value = {'aggregations': {}}

        fake_request = unit_test_utils.get_fake_request(
            USER1, TENANT1, '/v1/search/facets', is_admin=True
        )

        facets = self.plugin.get_facets(fake_request.context)
        facet_names = [f['name'] for f in facets]

        network_facets = ('name', 'version', 'ipv6_addr', 'ipv4_addr',
                          'OS-EXT-IPS-MAC:mac_addr', 'OS-EXT-IPS:type')
        expected_facet_names = [
            'OS-EXT-AZ:availability_zone', 'created_at', 'description',
            'flavor.id', 'host_status', 'id', 'image.id', 'locked',
            'name', 'owner', 'project_id', 'security_groups', 'status',
            'tags', 'tenant_id', 'updated_at', 'user_id']
        expected_facet_names.extend(['networks.' + f for f in network_facets])

        self.assertEqual(set(expected_facet_names), set(facet_names))

        complex_facet_option_fields = (
            'image.id', 'flavor.id', 'networks.name',
            'networks.OS-EXT-IPS:type', 'networks.version')
        aggs = dict(unit_test_utils.complex_facet_field_agg(name)
                    for name in complex_facet_option_fields)

        simple_facet_option_fields = (
            'status', 'OS-EXT-AZ:availability_zone', 'security_groups',
            'host_status', 'locked'
        )
        aggs.update(dict(unit_test_utils.simple_facet_field_agg(name)
                         for name in simple_facet_option_fields))

        expected_agg_query = {
            'aggs': aggs,
            'query': {
                'filtered': {
                    'filter': {
                        'and': [
                            {'term': {ROLE_USER_FIELD: 'admin'}},
                            {'term': {'tenant_id': TENANT1}}
                        ]
                    }
                }
            }
        }
        mock_engine.search.assert_called_with(
            index=self.plugin.alias_name_search,
            doc_type=self.plugin.get_document_type(),
            body=expected_agg_query,
            ignore_unavailable=True,
            size=0
        )

    def test_facets_all_projects(self):
        # For non admins, all_projects should have no effect
        mock_engine = mock.Mock()
        self.plugin.engine = mock_engine

        # Don't really care about the return values
        mock_engine.search.return_value = {
            'aggregations': {}
        }

        fake_request = unit_test_utils.get_fake_request(
            USER1, TENANT1, '/v1/search/facets', is_admin=False
        )

        self.plugin.get_facets(fake_request.context, all_projects=True)

        expected_agg_query_filter = {
            'filtered': {
                'filter': {
                    'and': [
                        {'term': {ROLE_USER_FIELD: 'user'}},
                        {'term': {'tenant_id': TENANT1}}
                    ]
                }
            }
        }

        # Call args are a tuple (name, posargs, kwargs)
        search_call = mock_engine.search.mock_calls[0]
        search_call_body = search_call[2]['body']
        self.assertEqual(set(['aggs', 'query']), set(search_call_body.keys()))

        # The aggregation query's tested elsewhere, just check the query filter
        self.assertEqual(expected_agg_query_filter, search_call_body['query'])

        # Admins can request all_projects
        fake_request = unit_test_utils.get_fake_request(
            USER1, TENANT1, '/v1/search/facets', is_admin=True
        )

        self.plugin.get_facets(fake_request.context, all_projects=True)

        # Test the SECOND call to the mock
        search_call = mock_engine.search.mock_calls[1]
        search_call_body = search_call[2]['body']

        # We don't expect any filter query here, just the aggregations.
        self.assertEqual(set(['aggs', 'query']), set(search_call_body.keys()))

    def test_facets_no_mapping(self):
        mock_engine = mock.Mock()
        self.plugin.engine = mock_engine

        fake_request = unit_test_utils.get_fake_request(
            USER1, TENANT1, '/v1/search/facets', is_admin=True
        )

        mock_engine.search.return_value = {
            'aggregations': {
                'status': {'buckets': []},
                'image.id': {'doc_count': 0}
            }
        }

        facets = self.plugin.get_facets(fake_request.context)

        status_facet = list(filter(lambda f: f['name'] == 'status',
                                   facets))[0]
        image_facet = list(filter(lambda f: f['name'] == 'image.id',
                                  facets))[0]
        expected_status = {'name': 'status', 'options': [], 'type': 'string'}
        expected_image = {'name': 'image.id', 'options': [], 'type': 'string',
                          'resource_type': 'OS::Glance::Image'}

        self.assertEqual(expected_status, status_facet)
        self.assertEqual(expected_image, image_facet)

    @mock.patch(nova_version_getter, return_value=fake_version_list)
    def test_created_at_updated_at(self, mock_version):
        self.assertTrue('created_at' not in self.instance1.to_dict())
        self.assertTrue('updated_at' not in self.instance1.to_dict())

        with mock.patch(nova_server_getter, return_value=self.instance1):
            serialized = self.plugin.serialize(self.instance1.id)

        self.assertEqual(serialized['created_at'], created_now)
        self.assertEqual(serialized['updated_at'], updated_now)

    @mock.patch(nova_version_getter, return_value=fake_version_list)
    def test_update_404_deletes(self, mock_version):
        """Test that if a server is missing on a notification event, it
        gets deleted from the index
        """
        mock_engine = mock.Mock()
        self.plugin.engine = mock_engine

        notification_handler = self.plugin.get_notification_handler()
        doc_deleter = self.plugin._index_helper
        nova_exc = novaclient.exceptions.NotFound('missing')
        with mock.patch(nova_server_getter,
                        side_effect=nova_exc) as mock_get:
            with mock.patch.object(doc_deleter,
                                   'delete_document') as mock_deleter:
                fake_timestamp = '2015-09-01 08:57:35.282586'
                notification_handler.index_from_api(
                    {u'instance_id': u'missing',
                     u'updated_at': u'2016-02-01T00:00:00Z'},
                    fake_timestamp)
                mock_get.assert_called_once_with(u'missing')
                mock_deleter.assert_called_once_with(
                    # Version should really be integer; see bug #1  550494
                    {'_id': u'missing', '_version': '454284800097855282'})

    def test_vol_events_supported(self):
        not_handler = self.plugin.get_notification_handler()
        vol_payload = {
            "instance_id": "a",
            "volume_id": "b"
        }

        with mock.patch.object(not_handler, 'index_from_api') as mock_update:
            events = not_handler.get_event_handlers()
            self.assertTrue('compute.instance.volume.attach' in events)
            self.assertTrue('compute.instance.volume.detach' in events)

            attach = events['compute.instance.volume.attach']
            attach(vol_payload, 1234)

            mock_update.assert_called_with(vol_payload, 1234)
            mock_update.reset()

            detach = events['compute.instance.volume.detach']
            detach(vol_payload, 1234)

            mock_update.assert_called_with(vol_payload, 1234)

    @mock.patch(nova_version_getter, return_value=fake_version_list)
    def test_filter_result(self, mock_version):
        """We reformat outgoing results so that security group looks like the
        response we get from the nova API.
        """
        with mock.patch(nova_server_getter, return_value=self.instance1):
            es_result = self.plugin.serialize(self.instance1.id)
        self.plugin.filter_result({'_source': es_result}, None)
        self.assertEqual([{'name': 'default'}], es_result['security_groups'])

    @mock.patch(nova_version_getter, return_value=fake_version_list)
    def test_boot_state_change_notifications(self, mock_version):
        """This is an attempt to stop hammering the nova API!
        Many state change events are received in a short space of time during
        nova instance boots. We'll ignore some of them.
        """
        mock_engine = mock.Mock()
        self.plugin.engine = mock_engine

        successful_boot_events = [
            ("compute.instance.update",
             dict(state_description="scheduling", old_state="building",
                  state="building", old_task_state="scheduling",
                  new_task_state="scheduling"),
             "2016-05-12 20:44:40.352048"),
            ("compute.instance.update",
             dict(state_description="scheduling", old_state="building",
                  state="building", old_task_state="scheduling",
                  new_task_state=None),
             "2016-05-12 20:44:40.867902"),
            ("compute.instance.create.start",
             dict(state_description="", state="building"),
             "2016-05-12 20:44:40.885366"),
            ("compute.instance.update",
             dict(state_description="", old_state="building",
                  state="building", old_task_state=None,
                  new_task_state=None),
             "2016-05-12 20:44:40.981856"),
            ("compute.instance.update",
             dict(state_description="networking", old_state="building",
                  state="building", old_task_state="networking",
                  new_task_state="networking"),
             "2016-05-12 20:44:41.082192"),
            ("compute.instance.update",
             dict(state_description="block_device_mapping",
                  old_state="building", state="building",
                  old_task_state="networking",
                  new_task_state="block_device_mapping"),
             "2016-05-12 20:44:41.298666"),
            ("compute.instance.update",
             dict(state_description="spawning", old_state="building",
                  state="building", old_task_state="block_device_mapping",
                  new_task_state="spawning"),
             "2016-05-12 20:44:41.355864"),
            ("port.create.start",
             dict(device_owner="compute:None",
                  device_id="913a1d19-f96f-4bb2-b459-84dd25ebb923"),
             "2016-05-12 20:44:41.673135"),
            ("port.create.end",
             dict(device_owner="compute:None",
                  device_id="913a1d19-f96f-4bb2-b459-84dd25ebb923"),
             "2016-05-12 20:44:42.700366"),
            ("image.send", {}, "2016-05-12 20:44:42.700366"),
            ("image.send", {}, "2016-05-12 20:44:45.444854"),
            ("compute.instance.update",
             dict(state_description="", old_state="building",
                  state="active", old_task_state="spawning",
                  new_task_state=None),
             "2016-05-12 20:44:52.915259"),
            ("compute.instance.create.end",
             dict(state_description="", state="active"),
             "2016-05-12 20:44:52.976685"),
        ]

        for event in successful_boot_events:
            event[1]["instance_id"] = u"a380287d-1f61-4887-959c-8c5ab8f75f8f"

        # Feed the events to the notification handler
        handler = self.plugin.get_notification_handler()
        event_handlers = handler.get_event_handlers()

        def handle_message(message, expected_event_type):
            self.assertEqual(expected_event_type, message[0],
                             "Expected event type doesn't match test "
                             "message type.")
            # type, payload, timestamp
            type_handler = event_handlers.get(message[0], None)
            if type_handler:
                type_handler(message[1], message[2])

        with mock.patch.object(self.plugin.index_helper,
                               'save_documents') as mock_save, \
            mock.patch.object(self.plugin.index_helper,
                              'update_document') as mock_update, \
            mock.patch(nova_server_getter,
                       return_value=self.instance1) as nova_getter:

                def assert_call_counts(get, save, update):
                    # Helper to reduce copy pasta
                    self.assertEqual(get, nova_getter.call_count)
                    self.assertEqual(save, mock_save.call_count)
                    self.assertEqual(update, mock_update.call_count)

                # Expect a nova API hit from the first update
                handle_message(successful_boot_events[0],
                               "compute.instance.update")
                assert_call_counts(get=1, save=1, update=0)

                # Expect nothing for the next update (should be ignored)
                handle_message(successful_boot_events[1],
                               "compute.instance.update")
                assert_call_counts(get=1, save=1, update=0)

                # Causes a nova GET
                handle_message(successful_boot_events[2],
                               "compute.instance.create.start")
                assert_call_counts(get=2, save=2, update=0)

                # Update after create.start is ignored
                handle_message(successful_boot_events[3],
                               "compute.instance.update")
                assert_call_counts(get=2, save=2, update=0)

                # Then networking, disk mapping etc
                mock_engine.get.return_value = {
                    '_version': 3,
                    '_source': {
                        'OS-EXT-STS:vm_state': 'building',
                        'OS-EXT-STS:task_state': None
                    }
                }
                handle_message(successful_boot_events[4],
                               "compute.instance.update")
                assert_call_counts(get=2, save=2, update=1)

                mock_engine.get.return_value = {
                    '_version': 4,
                    '_source': {
                        'OS-EXT-STS:vm_state': 'building',
                        'OS-EXT-STS:task_state': 'networking'
                    }
                }
                handle_message(successful_boot_events[5],
                               "compute.instance.update")
                assert_call_counts(get=2, save=2, update=2)

                mock_engine.get.return_value = {
                    '_version': 5,
                    '_source': {
                        'OS-EXT-STS:vm_state': 'building',
                        'OS-EXT-STS:task_state': 'block_device_mapping'
                    }
                }
                handle_message(successful_boot_events[6],
                               "compute.instance.update")
                assert_call_counts(get=2, save=2, update=3)

                # port.create events are ignored
                handle_message(successful_boot_events[7],
                               "port.create.start")
                handle_message(successful_boot_events[8],
                               "port.create.end")
                assert_call_counts(get=2, save=2, update=3)

                # image.send ignored
                handle_message(successful_boot_events[9], "image.send")
                handle_message(successful_boot_events[10], "image.send")
                assert_call_counts(get=2, save=2, update=3)

                # final update is also ignored because create.end follows
                handle_message(successful_boot_events[11],
                               "compute.instance.update")
                assert_call_counts(get=2, save=2, update=3)

                # create.end causes full save
                handle_message(successful_boot_events[12],
                               "compute.instance.create.end")
                assert_call_counts(get=3, save=3, update=3)

    def test_racing_state_change_notifications(self):
        """Test that a 'state update' change doesn't get applied if it looks
        like the instance state has already been updated by a later change.
        """
        mock_engine = mock.Mock()
        self.plugin.engine = mock_engine

        handler = self.plugin.get_notification_handler()
        event_handlers = handler.get_event_handlers()

        with mock.patch.object(self.plugin.index_helper,
                               'update_document') as mock_update:
            # Simulate the 'spawning' event getting processed first
            mock_engine.get.return_value = {
                '_version': 4,
                '_source': {
                    'OS-EXT-STS:vm_state': 'building',
                    'OS-EXT-STS:task_state': 'spawning'
                }
            }
            event_handlers['compute.instance.update'](
                dict(state_description="block_device_mapping",
                     old_state="building", state="building",
                     old_task_state="networking",
                     new_task_state="block_device_mapping",
                     instance_id=u"a380287d-1f61-4887-959c-8c5ab8f75f8f"),
                "2016-05-12 20:44:41.298666")

            self.assertEqual(0, mock_update.call_count)

    @mock.patch(nova_version_getter, return_value=fake_version_list)
    def test_delete_state_change_notifications(self, mock_version):
        mock_engine = mock.Mock()
        self.plugin.engine = mock_engine

        delete_events = [
            ('compute.instance.update',
             dict(state_description='deleting', state='active',
                  old_task_state='deleting', new_task_state='deleting'),
             '2016-05-23 18:44:02.889647'),
            ('compute.instance.delete.start',
             dict(state_description='deleting', state='active'),
             '2016-05-23 18:44:02.943141'),
            ('compute.instance.shutdown.start',
             dict(state_description='deleting', state='active'),
             '2016-05-23 18:44:02.950168'),
            ('compute.instance.update',
             dict(state_description='deleting', state='active',
                  old_state='active', new_task_state='deleting',
                  old_task_state='deleting'),
             '2016-05-23 18:44:04.155735'),
            ('port.delete.start', {}, '2016-05-23 18:44:04.435210'),
            ('port.delete.end', {}, '2016-05-23 18:44:04.627044'),
            ('compute.instance.shutdown.end',
             dict(state_description='deleting', state='active'),
             '2016-05-23 18:44:04.696012'),
            ('compute.instance.update',
             dict(state_description='', state='deleted', new_task_state=None,
                  old_task_state='deleting'),
             '2016-05-23 18:44:04.779076'),
            ('compute.instance.delete.end',
             dict(state_description='', state='deleted',
                  updated_at='2016-05-23 18:44:04'),
             '2016-05-23 18:44:04.916681')
        ]

        for event in delete_events:
            event[1]["instance_id"] = u"a380287d-1f61-4887-959c-8c5ab8f75f8f"

        handler = self.plugin.get_notification_handler()
        event_handlers = handler.get_event_handlers()

        def handle_message(message, expected_event_type, expect_handled=True):
            self.assertEqual(expected_event_type, message[0],
                             "Expected event type doesn't match test "
                             "message type.")
            # type, payload, timestamp
            type_handler = event_handlers.get(message[0], None)
            if type_handler:
                type_handler(message[1], message[2])
            else:
                if expect_handled:
                    self.fail("Expected event '%s' to be handled" %
                              expected_event_type)

        with mock.patch.object(self.plugin.index_helper,
                               'save_documents') as mock_save, \
            mock.patch.object(self.plugin.index_helper,
                              'delete_document') as mock_delete, \
            mock.patch.object(self.plugin.index_helper,
                              'get_document') as mock_es_getter, \
            mock.patch(nova_server_getter,
                       return_value=self.instance1) as nova_getter:

                def assert_call_counts(get=0, save=0, es_gets=0):
                    # Helper to reduce copy pasta
                    self.assertEqual(get, nova_getter.call_count)
                    self.assertEqual(save, mock_save.call_count)
                    self.assertEqual(es_gets, mock_es_getter.call_count)

                handle_message(delete_events[0],
                               "compute.instance.update")
                assert_call_counts(es_gets=1)

                handle_message(delete_events[1],
                               "compute.instance.delete.start",
                               expect_handled=False)

                handle_message(delete_events[2],
                               "compute.instance.shutdown.start",
                               expect_handled=False)
                assert_call_counts(es_gets=1)

                handle_message(delete_events[3],
                               "compute.instance.update")
                assert_call_counts(es_gets=2)

                # Ignore port events
                handle_message(delete_events[4],
                               "port.delete.start",
                               expect_handled=False)
                handle_message(delete_events[5],
                               "port.delete.end",
                               expect_handled=False)

                handle_message(delete_events[6],
                               "compute.instance.shutdown.end")
                assert_call_counts(get=1, save=1, es_gets=2)

                # Ignore this one too
                handle_message(delete_events[7],
                               "compute.instance.update")
                assert_call_counts(get=1, save=1, es_gets=2)

                handle_message(delete_events[8],
                               "compute.instance.delete.end")
                assert_call_counts(get=1, save=1, es_gets=2)
                self.assertEqual(1, mock_delete.call_count)

    @mock.patch(nova_version_getter, return_value=fake_version_list)
    def test_pause_state_change_notifications(self, mock_version):
        mock_engine = mock.Mock()
        self.plugin.engine = mock_engine

        pause_events = [
            ('compute.instance.update',
             dict(state_description='pausing', state='active',
                  old_task_state='pausing', new_task_state='pausing'),
             '2016-06-17 19:52:13.523135'),
            ('compute.instance.pause.start',
             dict(state_description='pausing', state='active'),
             '2016-06-17 19:52:13.628180'),
            ('compute.instance.update',
             dict(state_description='', state='paused',
                  old_task_state='pausing', new_task_state=None),
             '2016-06-17 19:52:13.771604'),
            ('compute.instance.pause.end',
             dict(state_description='', state='paused'),
             '2016-06-17 19:52:13.808362')
        ]

        for event in pause_events:
            event[1]["instance_id"] = u"a380287d-1f61-4887-959c-8c5ab8f75f8f"

        handler = self.plugin.get_notification_handler()
        event_handlers = handler.get_event_handlers()

        def handle_message(message, expected_event_type, expect_handled=True):
            self.assertEqual(expected_event_type, message[0],
                             "Expected event type doesn't match test "
                             "message type.")
            # type, payload, timestamp
            type_handler = event_handlers.get(message[0], None)
            if type_handler:
                type_handler(message[1], message[2])
            else:
                if expect_handled:
                    self.fail("Expected event '%s' to be handled" %
                              expected_event_type)

        with mock.patch.object(self.plugin.index_helper,
                               'save_documents') as mock_save, \
            mock.patch.object(self.plugin.index_helper,
                              'get_document') as mock_es_getter, \
            mock.patch(nova_server_getter,
                       return_value=self.instance1) as nova_getter:

                def assert_call_counts(get=0, save=0, es_gets=0):
                    # Helper to reduce copy pasta
                    self.assertEqual(get, nova_getter.call_count)
                    self.assertEqual(save, mock_save.call_count)
                    self.assertEqual(es_gets, mock_es_getter.call_count)

                handle_message(pause_events[0],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=1)

                handle_message(pause_events[1],
                               "compute.instance.pause.start",
                               expect_handled=False)
                assert_call_counts(get=0, save=0, es_gets=1)

                handle_message(pause_events[2],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=1)

                handle_message(pause_events[3],
                               "compute.instance.pause.end",
                               expect_handled=False)
                assert_call_counts(get=1, save=1, es_gets=1)

    @mock.patch(nova_version_getter, return_value=fake_version_list)
    def test_reboot_state_change_notifications(self, mock_version):
        mock_engine = mock.Mock()
        self.plugin.engine = mock_engine

        reboot_events = [
            ('compute.instance.update',
             dict(state_description='rebooting', state='active',
                  old_task_state='rebooting', new_task_state='rebooting'),
             '2016-07-17 19:52:13.523135'),
            ('compute.instance.reboot.start',
             dict(state_description='rebooting', state='active'),
             '2016-07-17 19:52:13.628180'),
            ('compute.instance.update',
             dict(state_description='', state='active',
                  old_task_state='rebooting', new_task_state='reboot_pending'),
             '2016-07-17 19:52:13.771604'),
            ('compute.instance.update',
             dict(state_description='', state='active',
                  old_task_state='reboot_pending',
                  new_task_state='reboot_started'),
             '2016-07-17 19:52:13.781605'),
            ('compute.instance.update',
             dict(state_description='', state='active',
                  old_task_state='reboot_started', new_task_state=None),
             '2016-07-17 19:52:13.791605'),
            ('compute.instance.reboot.end',
             dict(state_description='', state='active'),
             '2016-07-17 19:52:13.808362')
        ]

        for event in reboot_events:
            event[1]["instance_id"] = u"a380287d-1f61-4887-959c-8c5ab8f75f8f"

        handler = self.plugin.get_notification_handler()
        event_handlers = handler.get_event_handlers()

        def handle_message(message, expected_event_type, expect_handled=True):
            self.assertEqual(expected_event_type, message[0],
                             "Expected event type doesn't match test "
                             "message type.")
            # type, payload, timestamp
            type_handler = event_handlers.get(message[0], None)
            if type_handler:
                type_handler(message[1], message[2])
            else:
                if expect_handled:
                    self.fail("Expected event '%s' to be handled" %
                              expected_event_type)

        with mock.patch.object(self.plugin.index_helper,
                               'save_documents') as mock_save, \
            mock.patch.object(self.plugin.index_helper,
                              'get_document') as mock_es_getter, \
            mock.patch(nova_server_getter,
                       return_value=self.instance1) as nova_getter:

                def assert_call_counts(get=0, save=0, es_gets=0):
                    # Helper to reduce copy pasta
                    self.assertEqual(get, nova_getter.call_count)
                    self.assertEqual(save, mock_save.call_count)
                    self.assertEqual(es_gets, mock_es_getter.call_count)

                handle_message(reboot_events[0],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=1)

                handle_message(reboot_events[1],
                               "compute.instance.reboot.start",
                               expect_handled=False)
                assert_call_counts(get=0, save=0, es_gets=1)

                handle_message(reboot_events[2],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=2)

                handle_message(reboot_events[3],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=3)

                handle_message(reboot_events[4],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=3)

                handle_message(reboot_events[5],
                               "compute.instance.reboot.end",
                               expect_handled=False)
                assert_call_counts(get=1, save=1, es_gets=3)

    @mock.patch(nova_version_getter, return_value=fake_version_list)
    def test_shelve_state_change_notifications(self, mock_version):
        mock_engine = mock.Mock()
        self.plugin.engine = mock_engine

        shelve_events = [
            ('compute.instance.update',
             dict(state_description='shelving', state='active',
                  old_task_state='shelving', new_task_state='shelving'),
             '2016-07-17 19:52:13.523135'),
            ('compute.instance.shelve.start',
             dict(state_description='shelving', state='active'),
             '2016-07-17 19:52:13.628180'),
            ('compute.instance.update',
             dict(state_description='', state='active',
                  old_task_state='shelving',
                  new_task_state='shelving_image_pending_upload'),
             '2016-07-17 19:52:13.771604'),
            ('compute.instance.update',
             dict(state_description='', state='active',
                  old_task_state='shelving_image_pending_upload',
                  new_task_state='shelving_image_uploading'),
             '2016-07-17 19:52:13.781605'),
            ('compute.instance.update',
             dict(state_description='', state='active',
                  old_task_state='shelving_image_uploading',
                  new_task_state='shelving_image_pending_upload'),
             '2016-07-17 19:52:13.791605'),
            ('compute.instance.update',
             dict(state_description='', state='active',
                  old_task_state='shelving_image_pending_upload',
                  new_task_state='shelving_image_uploading'),
             '2016-07-17 19:52:13.801605'),
            ('compute.instance.update',
             dict(state_description='', state='shelved',
                  old_task_state='shelving_image_uploading',
                  new_task_state='shelving_offloading'),
             '2016-07-17 19:52:13.811605'),
            ('compute.instance.update',
             dict(state_description='', state='shelved',
                  old_task_state='shelving_offloading',
                  new_task_state='shelving_offloading'),
             '2016-07-17 19:52:13.821605'),
            ('compute.instance.update',
             dict(state_description='', state='shelved_offloaded',
                  old_task_state='shelving_offloading',
                  new_task_state=None),
             '2016-07-17 19:52:13.831605'),
            ('compute.instance.shelve.end',
             dict(state_description='', state='active'),
             '2016-07-17 19:52:13.858362')
        ]

        for event in shelve_events:
            event[1]["instance_id"] = u"a380287d-1f61-4887-959c-8c5ab8f75f8f"

        handler = self.plugin.get_notification_handler()
        event_handlers = handler.get_event_handlers()

        def handle_message(message, expected_event_type, expect_handled=True):
            self.assertEqual(expected_event_type, message[0],
                             "Expected event type doesn't match test "
                             "message type.")
            # type, payload, timestamp
            type_handler = event_handlers.get(message[0], None)
            if type_handler:
                type_handler(message[1], message[2])
            else:
                if expect_handled:
                    self.fail("Expected event '%s' to be handled" %
                              expected_event_type)

        with mock.patch.object(self.plugin.index_helper,
                               'save_documents') as mock_save, \
            mock.patch.object(self.plugin.index_helper,
                              'get_document') as mock_es_getter, \
            mock.patch(nova_server_getter,
                       return_value=self.instance1) as nova_getter:

                def assert_call_counts(get=0, save=0, es_gets=0):
                    # Helper to reduce copy pasta
                    self.assertEqual(get, nova_getter.call_count)
                    self.assertEqual(save, mock_save.call_count)
                    self.assertEqual(es_gets, mock_es_getter.call_count)

                handle_message(shelve_events[0],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=1)

                handle_message(shelve_events[1],
                               "compute.instance.shelve.start",
                               expect_handled=False)
                assert_call_counts(get=0, save=0, es_gets=1)

                handle_message(shelve_events[2],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=2)

                handle_message(shelve_events[3],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=3)

                handle_message(shelve_events[4],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=4)

                handle_message(shelve_events[5],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=5)

                handle_message(shelve_events[6],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=6)

                handle_message(shelve_events[7],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=6)

                handle_message(shelve_events[8],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=6)

                handle_message(shelve_events[9],
                               "compute.instance.shelve.end",
                               expect_handled=False)
                assert_call_counts(get=1, save=1, es_gets=6)

    @mock.patch(nova_version_getter, return_value=fake_version_list)
    def test_unshelve_state_change_notifications(self, mock_version):
        mock_engine = mock.Mock()
        self.plugin.engine = mock_engine

        unshelve_events = [
            ('compute.instance.update',
             dict(state_description='unshelving', state='shelved_offloaded',
                  old_task_state='unshelving', new_task_state='unshelving'),
             '2016-07-17 19:52:13.523135'),
            ('compute.instance.unshelve.start',
             dict(state_description='unshelving', state='shelved_offloaded'),
             '2016-07-17 19:52:13.628180'),
            ('compute.instance.update',
             dict(state_description='', state='shelved_offloaded',
                  old_task_state='unshelving', new_task_state='unshelving'),
             '2016-07-17 19:52:13.771604'),
            ('compute.instance.update',
             dict(state_description='', state='shelved_offloaded',
                  old_task_state='unshelving',
                  new_task_state='spawning'),
             '2016-07-17 19:52:13.781605'),
            ('compute.instance.update',
             dict(state_description='', state='shelved_offloaded',
                  old_task_state='spawning', new_task_state='spawning'),
             '2016-07-17 19:52:13.791605'),
            ('compute.instance.update',
             dict(state_description='', state='active',
                  old_task_state='spawning', new_task_state=None),
             '2016-07-17 19:52:13.801605'),
            ('compute.instance.unshelve.end',
             dict(state_description='', state='active'),
             '2016-07-17 19:52:13.818362')
        ]

        for event in unshelve_events:
            event[1]["instance_id"] = u"a380287d-1f61-4887-959c-8c5ab8f75f8f"

        handler = self.plugin.get_notification_handler()
        event_handlers = handler.get_event_handlers()

        def handle_message(message, expected_event_type, expect_handled=True):
            self.assertEqual(expected_event_type, message[0],
                             "Expected event type doesn't match test "
                             "message type.")
            # type, payload, timestamp
            type_handler = event_handlers.get(message[0], None)
            if type_handler:
                type_handler(message[1], message[2])
            else:
                if expect_handled:
                    self.fail("Expected event '%s' to be handled" %
                              expected_event_type)

        with mock.patch.object(self.plugin.index_helper,
                               'save_documents') as mock_save, \
            mock.patch.object(self.plugin.index_helper,
                              'get_document') as mock_es_getter, \
            mock.patch(nova_server_getter,
                       return_value=self.instance1) as nova_getter:

                def assert_call_counts(get=0, save=0, es_gets=0):
                    # Helper to reduce copy pasta
                    self.assertEqual(get, nova_getter.call_count)
                    self.assertEqual(save, mock_save.call_count)
                    self.assertEqual(es_gets, mock_es_getter.call_count)

                handle_message(unshelve_events[0],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=1)

                handle_message(unshelve_events[1],
                               "compute.instance.unshelve.start",
                               expect_handled=False)
                assert_call_counts(get=0, save=0, es_gets=1)

                handle_message(unshelve_events[2],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=2)

                handle_message(unshelve_events[3],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=3)

                handle_message(unshelve_events[4],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=3)

                handle_message(unshelve_events[5],
                               "compute.instance.update")
                assert_call_counts(get=0, save=0, es_gets=3)

                handle_message(unshelve_events[6],
                               "compute.instance.unshelve.end",
                               expect_handled=False)
                assert_call_counts(get=1, save=1, es_gets=3)

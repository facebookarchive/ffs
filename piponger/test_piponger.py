#! /usr/bin/python3
# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from main import (app, db, metadata, models, tasks, get_local_free_port,
                  pipong_is_pinger, pipong_is_ponger, pipong_is_master,
                  get_local_ip)
import unittest

import sqlalchemy as sa
from sqlalchemy import desc
import socket
import json


class PipongerTestCase(unittest.TestCase):
    """
    Tests for a piponger node
    """

    def setUp(self):
        """
        Prepare DB: drop all tables, and recreate DB
        :return:
        """
        app.config['TESTING'] = True
        app.config['LOGIN_DISABLED'] = True
        app.config['DEBUG'] = True
        app.config['IS_PINGER'] = True
        app.config['IS_PONGER'] = True
        app.config['IS_MASTER'] = True

        self.app = app

        app.config.update(
            TESTING=True,
            LOGIN_DISABLED=True,
            DEBUG=True,
            IS_PINGER=True,
            IS_PONGER=True,
            IS_MASTER=True,
        )

        self.client = self.app.test_client()
        self.auth_header = {'Authorization': ' Basic dXNlcjE6MDAwMA=='}

        engine = sa.create_engine(
            app.config['SQLALCHEMY_DATABASE_URI'])
        metadata.bind = engine
        self.metadata = metadata

        with self.app.app_context():
            db.reflect()
            db.drop_all()

        self.metadata.create_all()
        self.populateDb()

    def tearDown(self):
        """
        Recreate DB with only basic data
        :return:
        """
        with self.app.app_context():
            db.reflect()
            db.drop_all()

        self.metadata.create_all()
        self.populateDb()

    def populateDb(self):
        """
        Insert base data into database
        :return:
        """
        with self.app.app_context():
            s = db.session()
            s.add(models.PingerIterationStatusType(type_id='CREATED'))
            s.add(models.PingerIterationStatusType(type_id='RUNNING'))
            s.add(models.PingerIterationStatusType(type_id='FINISHED'))
            s.add(models.PingerIterationStatusType(type_id='ERROR'))
            s.add(models.TaskStatusType(type_id='PENDING'))
            s.add(models.TaskStatusType(type_id='STARTED'))
            s.add(models.TaskStatusType(type_id='SUCCESS'))
            s.add(models.TaskStatusType(type_id='FAILURE'))
            s.add(models.TaskStatusType(type_id='RETRY'))
            s.add(models.TaskStatusType(type_id='REVOKED'))
            s.commit()

    def get_dummy_pinger_results(self):
        """
        Pinger results to alert "spine4" node
        :return:
        """

        pinger_results = [[{
            'ponger_address':
            '10.0.3.10',
            'dst_port':
            4000,
            'lost_percent':
            0,
            'path':
            ['10.0.1.1', '10.0.33.2', '10.0.132.2', '10.0.122.1', '10.0.12.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.3.11',
            'dst_port':
            4001,
            'lost_percent':
            0,
            'path':
            ['10.0.1.1', '10.0.33.2', '10.0.131.2', '10.0.111.1', '10.0.11.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.3.12',
            'dst_port':
            4002,
            'lost_percent':
            0,
            'path':
            ['10.0.1.1', '10.0.33.2', '10.0.132.2', '10.0.122.1', '10.0.12.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.3.13',
            'dst_port':
            4003,
            'lost_percent':
            0,
            'path':
            ['10.0.1.1', '10.0.33.2', '10.0.131.2', '10.0.111.1', '10.0.11.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.3.14',
            'dst_port':
            4004,
            'lost_percent':
            0,
            'path':
            ['10.0.1.1', '10.0.33.2', '10.0.131.2', '10.0.111.1', '10.0.11.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.2.10',
            'dst_port':
            4000,
            'lost_percent':
            48.9608,
            'path':
            ['10.0.1.1', '10.0.33.2', '10.0.131.2', '10.0.111.1', '10.0.21.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.2.11',
            'dst_port':
            4001,
            'lost_percent':
            0,
            'path':
            ['10.0.1.1', '10.0.33.2', '10.0.132.2', '10.0.122.1', '10.0.22.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.2.12',
            'dst_port':
            4002,
            'lost_percent':
            48.934491,
            'path':
            ['10.0.1.1', '10.0.33.2', '10.0.131.2', '10.0.111.1', '10.0.21.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.2.13',
            'dst_port':
            4003,
            'lost_percent':
            0,
            'path':
            ['10.0.1.1', '10.0.33.2', '10.0.132.2', '10.0.122.1', '10.0.22.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.2.14',
            'dst_port':
            4004,
            'lost_percent':
            0,
            'path':
            ['10.0.1.1', '10.0.33.2', '10.0.132.2', '10.0.122.1', '10.0.22.1'],
            'src_port':
            40000
        }], [{
            'ponger_address':
            '10.0.1.10',
            'dst_port':
            4000,
            'lost_percent':
            49.013418,
            'path':
            ['10.0.2.1', '10.0.21.2', '10.0.111.2', '10.0.131.1', '10.0.33.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.1.11',
            'dst_port':
            4001,
            'lost_percent':
            0,
            'path':
            ['10.0.2.1', '10.0.22.2', '10.0.122.2', '10.0.132.1', '10.0.33.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.1.12',
            'dst_port':
            4002,
            'lost_percent':
            51.101574,
            'path':
            ['10.0.2.1', '10.0.21.2', '10.0.111.2', '10.0.131.1', '10.0.33.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.1.13',
            'dst_port':
            4003,
            'lost_percent':
            0.026309,
            'path':
            ['10.0.2.1', '10.0.22.2', '10.0.122.2', '10.0.132.1', '10.0.33.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.1.14',
            'dst_port':
            4004,
            'lost_percent':
            0,
            'path':
            ['10.0.2.1', '10.0.22.2', '10.0.122.2', '10.0.132.1', '10.0.33.1'],
            'src_port':
            40000
        }, {
            'ponger_address': '10.0.3.10',
            'dst_port': 4000,
            'lost_percent': 0,
            'path': ['10.0.2.1', '10.0.22.2', '10.0.12.1'],
            'src_port': 40000
        }, {
            'ponger_address': '10.0.3.11',
            'dst_port': 4001,
            'lost_percent': 28.702545,
            'path': ['10.0.2.1', '10.0.21.2', '10.0.11.1'],
            'src_port': 40000
        }, {
            'ponger_address': '10.0.3.12',
            'dst_port': 4002,
            'lost_percent': 0,
            'path': ['10.0.2.1', '10.0.22.2', '10.0.12.1'],
            'src_port': 40000
        }, {
            'ponger_address': '10.0.3.13',
            'dst_port': 4003,
            'lost_percent': 52.617732,
            'path': ['10.0.2.1', '10.0.21.2', '10.0.11.1'],
            'src_port': 40000
        }, {
            'ponger_address': '10.0.3.14',
            'dst_port': 4004,
            'lost_percent': 48.987109,
            'path': ['10.0.2.1', '10.0.21.2', '10.0.11.1'],
            'src_port': 40000
        }], [{
            'ponger_address':
            '10.0.1.10',
            'dst_port':
            4000,
            'lost_percent':
            0,
            'path':
            ['10.0.3.1', '10.0.12.2', '10.0.122.2', '10.0.132.1', '10.0.33.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.1.11',
            'dst_port':
            4001,
            'lost_percent':
            0,
            'path':
            ['10.0.3.1', '10.0.11.2', '10.0.111.2', '10.0.131.1', '10.0.33.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.1.12',
            'dst_port':
            4002,
            'lost_percent':
            0,
            'path':
            ['10.0.3.1', '10.0.12.2', '10.0.122.2', '10.0.132.1', '10.0.33.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.1.13',
            'dst_port':
            4003,
            'lost_percent':
            0,
            'path':
            ['10.0.3.1', '10.0.11.2', '10.0.111.2', '10.0.131.1', '10.0.33.1'],
            'src_port':
            40000
        }, {
            'ponger_address':
            '10.0.1.14',
            'dst_port':
            4004,
            'lost_percent':
            0,
            'path':
            ['10.0.3.1', '10.0.11.2', '10.0.111.2', '10.0.131.1', '10.0.33.1'],
            'src_port':
            40000
        }, {
            'ponger_address': '10.0.2.10',
            'dst_port': 4000,
            'lost_percent': 0,
            'path': ['10.0.3.1', '10.0.12.2', '10.0.22.1'],
            'src_port': 40000
        }, {
            'ponger_address': '10.0.2.11',
            'dst_port': 4001,
            'lost_percent': 48.9608,
            'path': ['10.0.3.1', '10.0.11.2', '10.0.21.1'],
            'src_port': 40000
        }, {
            'ponger_address': '10.0.2.12',
            'dst_port': 4002,
            'lost_percent': 0,
            'path': ['10.0.3.1', '10.0.12.2', '10.0.22.1'],
            'src_port': 40000
        }, {
            'ponger_address': '10.0.2.13',
            'dst_port': 4003,
            'lost_percent': 48.987109,
            'path': ['10.0.3.1', '10.0.11.2', '10.0.21.1'],
            'src_port': 40000
        }, {
            'ponger_address': '10.0.2.14',
            'dst_port': 4004,
            'lost_percent': 48.9608,
            'path': ['10.0.3.1', '10.0.11.2', '10.0.21.1'],
            'src_port': 40000
        }]]

        return pinger_results

    def test_if_master(self):
        """
        Check if instance is master
        :return:
        """
        assert pipong_is_master() is True

    def test_if_pinger(self):
        """
        Check if instance is pinger
        :return:
        """
        assert pipong_is_pinger() is True

    def test_if_ponger(self):
        """
        Check if instance is ponger
        :return:
        """
        assert pipong_is_ponger() is True

    def test_main_page_online(self):
        """
        Test if root of the system "/" is working
        :return:
        """
        rv = self.client.get('/', headers=self.auth_header)
        assert 'application/json' in rv.headers['content-type']

    def test_register_pinger_ponger(self):
        """
        Test if register ponger/pinger is working
        :return:
        """
        rv = self.client.post(
            '/api/v1.0/master/register_ponger',
            data=json.dumps(dict(api_port='1234', api_protocol='http://')),
            follow_redirects=True,
            headers=self.auth_header,
            content_type='application/json')

        assert b'success' in rv.data

        rv = self.client.post(
            '/api/v1.0/master/register_pinger',
            data=json.dumps(dict(api_port='1234', api_protocol='http://')),
            follow_redirects=True,
            headers=self.auth_header,
            content_type='application/json')
        assert b'success' in rv.data

    def test_get_valid_local_ip(self):
        ip = get_local_ip()
        assert self.is_valid_ipv4_address(ip) is True

    def is_valid_ipv4_address(self, address):
        try:
            socket.inet_pton(socket.AF_INET, address)
        except AttributeError:  # no inet_pton here, sorry
            try:
                socket.inet_aton(address)
            except socket.error:
                return False
            return address.count('.') == 3
        except socket.error:  # not a valid address
            return False

        return True

    def test_outlier(self):
        node_score = {
            '10.0.33.2': 16.7546175,
            '10.0.131.2': 33.509235,
            '10.0.111.1': 33.509235,
            '10.0.11.1': 33.509235,
            '10.0.132.2': 0.0,
            '10.0.122.1': 0.0,
            '10.0.12.1': 0.0,
        }

        node_score2 = {
            '10.0.33.2': 0.0,
            '10.0.132.2': 0.0,
            '10.0.122.1': 5.599531,
            '10.0.22.1': 0.0,
            '10.0.12.1': 30.665494
        }

        node_score3 = {
            '10.0.21.0': 50.84486233333333,
            '10.0.11.0': 50.38194127777778,
            '10.0.131.0': 49.17669183333334,
            '10.0.111.0': 49.17669183333334,
            '10.0.3.0': 30.918426099999998,
            '10.0.2.0': 24.803998999999997,
            '10.0.1.0': 24.784506,
            '10.0.33.0': 18.19589433333333,
            '10.0.122.0': 0.0,
            '10.0.12.0': 0.0,
            '10.0.132.0': 0.0,
            '10.0.22.0': 0.0
        }

        v = list(node_score.values())
        k = list(node_score.keys())
        out1 = tasks.master_tasks.get_outliers(v)
        out1_k = [k[i] for i in out1]
        assert all(elem in out1_k
                   for elem in ['10.0.131.2', '10.0.111.1', '10.0.11.1'])

        v = list(node_score2.values())
        k = list(node_score2.keys())
        out2 = tasks.master_tasks.get_outliers(v)
        out2_k = [k[i] for i in out2]
        assert all(elem in out2_k for elem in ['10.0.12.1'])

        v = list(node_score3.values())
        k = list(node_score3.keys())
        out3 = tasks.master_tasks.get_outliers(v)
        out3_k = [k[i] for i in out3]
        assert all(
            elem in out3_k
            for elem in ['10.0.21.0', '10.0.11.0', '10.0.131.0', '10.0.111.0'])

    def test_create_master_iteration(self):
        """
        Create a master iteration
        :return:/
        """
        with self.app.app_context():
            tasks.master_tasks.create_iteration()
            master_count = db.session.query(models.MasterIteration).order_by(
                desc(models.MasterIteration.created_date)).count()

        assert master_count == 1

    def test_create_pinger_iteration(self):
        """
        Create a master iteration and a pinger iteration
        :return:
        """
        with self.app.app_context():
            tasks.master_tasks.create_iteration()
            master_it = db.session.query(models.MasterIteration).order_by(
                desc(models.MasterIteration.created_date)).first()

        rv = self.client.post(
            '/api/v1.0/start_session',
            data=json.dumps({
                'hosts': {
                    "127.0.0.1": {
                        "api_port": 5000,
                        "api_protocol": "http://",
                    }
                },
                'tracert_qty': 1,
                'master_iteration_id': master_it.id
            }),
            follow_redirects=True,
            headers=self.auth_header,
            content_type='application/json')
        assert b'success' in rv.data

        with self.app.app_context():
            pinger_it_count = db.session.query(models.PingerIteration).count()
            assert pinger_it_count > 0

    def remove_old_nodes(self):
        """
        Add old pinger/ponger nodes, and check for deletion
        :return:
        """
        with self.app.app_context():
            s = db.session()
            s.add(
                models.RegisteredPingerNode(
                    address='127.0.0.1',
                    api_protocol='http://',
                    api_port='5000',
                    created_date='2004-10-19 10:23:54',
                    last_updated_date=''))

            s.add(
                models.RegisteredPongerNode(
                    address='127.0.0.1',
                    api_protocol='http://',
                    api_port='5000',
                    created_date='2004-10-19 10:23:54',
                    last_updated_date=''))
            s.commit()

        tasks.master_tasks.remove_old_nodes()
        with self.app.app_context():
            pinger_count = db.session.query(
                models.RegisteredPingerNode).count()
            ponger_count = db.session.query(
                models.RegisteredPongerNode).count()

        assert pinger_count <= 0
        assert ponger_count <= 0

    def test_create_iperf_server(self):
        """
        Test to rise an iperf server
        :return:
        """
        open_port = get_local_free_port()
        result = tasks.ponger_tasks.create_iperf_server(open_port)
        assert result is True

    def verify_chrod_callback(results):
        print("{}: Task iperf results:{}".format(
            "test_call_iperf_client_multiple_ports", results))
        return 123

    def test_dublin_tracert(self):
        """
        Execute an dublin tracert to 8.8.8.8
        :return:
        """
        rv = self.client.post(
            '/api/v1.0/start_session',
            data=json.dumps({
                'hosts': {
                    "8.8.8.8": {
                        "api_port": 5000,
                        "api_protocol": "http://",
                    }
                },
                'tracert_qty': 1,
                'master_iteration_id': 1
            }),
            follow_redirects=True,
            headers=self.auth_header,
            content_type='application/json')

        assert b'success' in rv.data
        json_data = json.loads(str(rv.data, 'utf-8'))

        dst_port = get_local_free_port()
        src_port = get_local_free_port()

        with self.app.app_context():
            s = db.session()

            ponger_port_t = models.PongerPort(
                ponger_id=1,
                dst_port=dst_port,
                src_port_min=src_port,
                src_port_max=src_port + 1)
            s.add(ponger_port_t)
            s.flush()

            tracert_t = models.Tracert(
                pinger_iteration_id=json_data['ping_iteration_id'],
                status='PENDING',
                ponger_port_id=ponger_port_t.id,
            )
            s.add(tracert_t)
            s.flush()

            tracert_id = tracert_t.id

            tasks.pinger_tasks.do_dublin_tracert(
                json_data['ping_iteration_id'])

            tracert_t = s.query(
                models.Tracert).filter_by(id=tracert_id).first()
            tracert_result = tracert_t.result
            s.commit()
            s.close_all()

            assert "flows" in tracert_result

    def test_register_pinger_result(self):
        """
        Register pinger results
        :return:
        """

        rv = self.client.post(
            '/api/v1.0/master/register_pinger',
            data=json.dumps(dict(api_port='1234', api_protocol='http://')),
            follow_redirects=True,
            headers=self.auth_header,
            content_type='application/json')
        assert b'success' in rv.data

        with self.app.app_context():
            tasks.master_tasks.create_iteration()
            master_count = db.session.query(models.MasterIteration).order_by(
                desc(models.MasterIteration.created_date)).count()

            assert master_count == 1

            dummy_res = self.get_dummy_pinger_results()

            rv = self.client.post(
                '/api/v1.0/master/register_pinger_result',
                data=json.dumps({
                    "master_remote_id": 1,
                    "local_port": 1234,
                    "result": dummy_res[0]
                }),
                follow_redirects=True,
                headers=self.auth_header,
                content_type='application/json')

        assert b'success' in rv.data

    def test_analyse_result(self):
        """
        Analyse pinger results
        :return:
        """

        rv = self.client.post(
            '/api/v1.0/master/register_pinger',
            data=json.dumps(dict(api_port='1234', api_protocol='http://')),
            follow_redirects=True,
            headers=self.auth_header,
            content_type='application/json')
        assert b'success' in rv.data

        with self.app.app_context():
            tasks.master_tasks.create_iteration()
            master_count = db.session.query(models.MasterIteration).order_by(
                desc(models.MasterIteration.created_date)).count()

            assert master_count == 1

            dummy_res = self.get_dummy_pinger_results()

            for i in range(len(dummy_res)):
                rv = self.client.post(
                    '/api/v1.0/master/register_pinger_result',
                    data=json.dumps({
                        "master_remote_id": 1,
                        "local_port": 1234,
                        "result": dummy_res[i]
                    }),
                    follow_redirects=True,
                    headers=self.auth_header,
                    content_type='application/json')

            analyse_result = tasks.master_tasks.analyse_iteration(1)
            assert '10.0.21.0' in analyse_result


if __name__ == '__main__':
    unittest.main(verbosity=2)

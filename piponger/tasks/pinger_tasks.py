#! /usr/bin/python3
# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import dublintraceroute
import time
import models
import traceback
from celery import chord
from celery.exceptions import SoftTimeLimitExceeded
import subprocess
import requests
import json
from requests.auth import HTTPBasicAuth as requestHTTPAuth
import inspect

from main import app, db, celery, logger


@celery.task(time_limit=12000, soft_time_limit=11000)
def do_iperf3_client(ponger_id):
    """
    Petform a iperf3 client connection to a remote host
    The data from the connection is obtained from the db
    :param ponger_id: the ID of the ponger
    :return:
    """
    current_f_name = inspect.currentframe().f_code.co_name

    logger.info("{}: Do_iperf3_client ponger_id:{}".format(
        current_f_name, ponger_id))

    iperf_query = db.session.query(
        models.Iperf, models.PongerPort, models.Ponger).filter(
            models.Iperf.ponger_port_id == models.PongerPort.id).filter(
                models.PongerPort.ponger_id == models.Ponger.id).filter(
                    models.Ponger.id == ponger_id).all()

    if iperf_query is None:
        logger.error("{}: No Iperf rows found with ponger_id: {}".format(
            current_f_name, ponger_id))
        return None

    try:
        for join_result in iperf_query:
            iperf_t = join_result.Iperf
            ponger_t = join_result.Ponger

            logger.debug(
                "{}: Performing iperf id:{} address:{} srcport:{} dstport:{}".
                format(current_f_name, iperf_t.id,
                       str(iperf_t.ponger_port.ponger.address),
                       str(iperf_t.src_port),
                       str(iperf_t.ponger_port.dst_port)))

            max_tries = 20
            client_tries = 0
            success = False

            cmd_result_str = ""

            while client_tries < max_tries and success is False:
                iperf_t.status = "STARTED"
                db.session.commit()

                api_port = ""
                if ponger_t.api_port != "":
                    api_port = ":" + str(ponger_t.api_port)

                post_url = "{}{}{}/api/v1.0/iperf/server".format(
                    ponger_t.api_protocol, ponger_t.address, api_port)
                logger.debug(
                    "{}: Asking for new iperf server post_url: {}".format(
                        current_f_name, post_url))

                try:
                    req_res = requests.post(
                        post_url,
                        auth=requestHTTPAuth(app.config['HTTP_AUTH_USER'],
                                             app.config['HTTP_AUTH_PASS']),
                        timeout=10)
                except Exception as e:
                    logger.error("{}: Error requesting servers: {}".format(
                        current_f_name, str(e)))
                    client_tries += 1
                    time.sleep(5)
                    continue

                if req_res.status_code != 200:
                    logger.error(
                        "{}: Error creating servers: {} returned status: {}".
                        format(current_f_name, post_url, req_res.status_code))
                    client_tries += 1
                    time.sleep(5)
                    continue

                json_data = req_res.json()
                if 'port' not in json_data or 'result' not in json_data or \
                        json_data['result'] != 'success':
                    logger.error("{}: Json data invalid: {}".format(
                        current_f_name, json_data))
                    client_tries += 1
                    time.sleep(5)
                    continue

                logger.debug("{}: Host:{}{}{} Json data: {}".format(
                    current_f_name, ponger_t.api_protocol, ponger_t.address,
                    api_port, json_data))

                cmd = [
                    app.config['IPERF3_CLIENT_SCRIPT_LOCATION'],
                    str(iperf_t.ponger_port.ponger.address),
                    str(iperf_t.ponger_port.dst_port),
                    str(iperf_t.src_port),
                ]

                try:
                    cmd_result_str = subprocess.check_output(cmd).decode(
                        "utf-8")
                    if "lost_percent" in cmd_result_str:
                        success = True
                        iperf_res = json.loads(cmd_result_str)

                        result_dict = {
                            "seconds": iperf_res['end']['sum']['seconds'],
                            "bytes": iperf_res['end']['sum']['bytes'],
                            "bits_per_second": iperf_res['end']['sum']['bits_per_second'],
                            "lost_percent": iperf_res['end']['sum']['lost_percent'],
                            "cpu_utilization_percent": iperf_res['end']['cpu_utilization_percent']
                        }

                        logger.debug(
                            "{}: Iperf client results summarized: "
                            "host:{} src_port:{} dst_port:{} res:{}".format(
                                current_f_name,
                                str(iperf_t.ponger_port.ponger.address),
                                str(iperf_t.src_port),
                                str(iperf_t.ponger_port.dst_port),
                                result_dict))
                    else:
                        logger.debug(
                            "{}: Iperf client error: no lost_percent found on "
                            "cmd_result_str: {}/{} host:{} src_port:{} "
                            "dst_port:{} {}".format(
                                current_f_name, client_tries, max_tries,
                                str(iperf_t.ponger_port.ponger.address),
                                str(iperf_t.src_port),
                                str(iperf_t.ponger_port.dst_port),
                                cmd_result_str))
                except subprocess.CalledProcessError as e:
                    output = e.output.decode()
                    logger.debug("{}: Iperf client error: {}".format(
                        current_f_name, output))

                client_tries += 1
                time.sleep(5)

            if not success:
                iperf_t.status = "FAILURE"
                db.session.commit()

                logger.error("{}: Iperf client cannot communicate with "
                             "iperf server at: {}".format(
                                 current_f_name,
                                 iperf_t.ponger_port.ponger.address))
            else:
                iperf_t.status = "SUCCESS"
                iperf_t.result = cmd_result_str
                db.session.commit()

    except SoftTimeLimitExceeded:
        # todo: add failure to all iperf that exceeded time limit
        return None


# noinspection PyBroadException
@celery.task(time_limit=12000, soft_time_limit=11000)
def do_dublin_tracert(tracert_id):
    """
    Perform a dublin traceroute against a remote host on a remote port
    The parameters for this traceroute execution are defined on the db
    :param tracert_id: the ID of the iteration to get the tracerts
    :return:
    """
    current_f_name = inspect.currentframe().f_code.co_name

    logger.info("{}: do_dublin_tracert tracert_id:{}".format(
        current_f_name, tracert_id))

    tracert_t = db.session.query(models.Tracert).filter_by(
        id=tracert_id, status='PENDING').first()
    if tracert_t is None:
        logger.error("{}: Tracert not found with tracert_id: {}".format(
            current_f_name, tracert_id))
        return None

    try:
        tracert_t.status = "STARTED"
        db.session.commit()

        npaths = tracert_t.ponger_port.src_port_max - \
            tracert_t.ponger_port.src_port_min
        logger.info("{}: do_dublin_tracert started address:{} "
                    "srcport:{} dstport:{} npaths:{}".format(
                        current_f_name,
                        str(tracert_t.ponger_port.ponger.address),
                        tracert_t.ponger_port.src_port_min,
                        tracert_t.ponger_port.dst_port, npaths))

        dublin = dublintraceroute.DublinTraceroute(
            str(tracert_t.ponger_port.ponger.address),
            sport=tracert_t.ponger_port.src_port_min,
            dport=tracert_t.ponger_port.dst_port,
            use_srcport_for_path_generation=True,
            delay=25,
            npaths=npaths)

        success = False
        tracert_results = ""
        try:
            tracert_results = dublin.traceroute()

            if "flows" not in tracert_results.keys() or len(
                    tracert_results['flows']) <= 0:
                logger.debug("{}: Invalid tracert result:{}".format(
                    current_f_name, tracert_results))
            else:
                success = True
        except Exception:
            logger.debug("{}: Tracert client error: {}".format(
                current_f_name, traceback.format_exc()))

        if not success:
            tracert_t.status = "FAILURE"
            db.session.commit()

            logger.error(
                "{}: Tracert client cannot generate trace for server at:{}".
                format(current_f_name, tracert_t.ponger_port.ponger.address))

        tracert_t.status = "SUCCESS"
        tracert_t.result = json.dumps(tracert_results)
        db.session.commit()

        logger.debug("{}: result:{}".format(current_f_name, tracert_results))
    except SoftTimeLimitExceeded:
        tracert_t.status = "FAILED"
        db.session.commit()
        return None
    except Exception as e:
        logger.error("{}: Error calling do_dublin_tracert {} "
                     "src port:{}~{} dst port:{} error:{}".format(
                         current_f_name,
                         str(tracert_t.ponger_port.ponger.address),
                         str(tracert_t.ponger_port.src_port_min),
                         str(tracert_t.ponger_port.src_port_max),
                         str(tracert_t.ponger_port.dst_port), str(e)))
        return None

    return True


@celery.task(time_limit=1200, soft_time_limit=1100)
def perform_pipong_iteration_3(result, pinger_iteration_id):
    """
    Third iteration of the discovery and monitor
    Get the results, compile them into a JSON string and then
    them to the master node

    :param result: previous result
    :param pinger_iteration_id: the iteration id from the db
    :return:
    """

    current_f_name = inspect.currentframe().f_code.co_name

    logger.info("{}: Perform_pipong_iteration_3".format(current_f_name))
    logger.info("{}: Input:{} pinger_iteration_id:{}".format(
        current_f_name, result, pinger_iteration_id))

    iter_t = db.session.query(
        models.PingerIteration).filter_by(id=pinger_iteration_id).first()
    if iter_t is None:
        logger.error("{}: Iteration not found with ID: {}".format(
            current_f_name, pinger_iteration_id))
        return

    master_remote_id = iter_t.remote_id

    s = db.session()
    iter_t.status = "RUNNING_FINISHING"
    s.commit()

    iteration_result = []
    iperf_t = db.session.query(models.Iperf).filter_by(
        pinger_iteration_id=pinger_iteration_id, status='SUCCESS')
    for iperf in iperf_t:
        tracert_t = db.session.query(models.Tracert).filter_by(
            pinger_iteration_id=pinger_iteration_id,
            ponger_port_id=iperf.ponger_port_id,
            status='SUCCESS').first()

        iperf_res = json.loads(iperf.result)

        logger.info(
            "{}: tracert_t.ponger_port_id:{} iperf.ponger_port_id:{}".format(
                current_f_name, tracert_t.ponger_port_id,
                iperf.ponger_port_id))

        if tracert_t:
            result_dict = {
                "ponger_address": str(iperf.ponger_port.ponger.address),
                "src_port": int(iperf.src_port),
                "dst_port": int(iperf.ponger_port.dst_port)
            }

            try:
                tracert_res = json.loads(tracert_t.result)

                tracert_path = []
                src_ip = tracert_res['flows'][str(
                    iperf.src_port)][0]['sent']['ip']['src']

                for flow in tracert_res['flows'][str(iperf.src_port)]:
                    flow_name = flow['name']
                    if flow_name is not "":
                        ip_addr_node = flow['received']['ip']['src']
                        if ip_addr_node != src_ip and ip_addr_node != str(
                                iperf.ponger_port.ponger.address):
                            tracert_path.append(ip_addr_node)

                result_dict["path"] = tracert_path
                result_dict["seconds"] = iperf_res['end']['sum']['seconds']
                result_dict["bytes"] = iperf_res['end']['sum']['bytes']
                result_dict["bits_per_second"] = iperf_res['end']['sum'][
                    'bits_per_second']
                result_dict["lost_percent"] = iperf_res['end']['sum'][
                    'lost_percent']
                iteration_result.append(result_dict)
            except Exception as e:
                logger.error(
                    "{}: Error obtaining data from iperf iteration:{} "
                    "lost_percent for this host:{} result_dict:{}".format(
                        current_f_name, str(e),
                        str(iperf.ponger_port.ponger.address),
                        str(result_dict)))
                # result_dict["path"] = [str(iperf.ponger_port.ponger.address)]
                # result_dict["lost_percent"] = 999
                pass

    master_host = app.config['MASTER_SERVER']
    master_port = app.config['MASTER_PORT']

    http_user = app.config['HTTP_AUTH_USER']
    http_pass = app.config['HTTP_AUTH_PASS']

    try:
        post_url = ("http://{}:{}/api/v1.0/master/"
                    "register_pinger_result".format(master_host, master_port))

        iter_t.status = "FINISHED"
        s.commit()

        try:
            post_data = {
                "master_remote_id": master_remote_id,
                "local_port": app.config['API_PORT'],
                "result": iteration_result
            }

            req = requests.post(
                post_url,
                auth=requestHTTPAuth(http_user, http_pass),
                json=post_data,
                timeout=10)
            logger.info("{}: Sent pinger result response:{} data:{}".format(
                current_f_name, req.text, post_data))
            return True
        except Exception as e:
            logger.error("{}: Error registering pinger in master: {}".format(
                current_f_name, str(e)))

        return None
    except SoftTimeLimitExceeded:
        logger.error("{}: Error SoftTimeLimitExceeded".format(current_f_name))
        return None


@celery.task(time_limit=1200, soft_time_limit=1100)
def perform_pipong_iteration_2(result, pinger_iteration_id):
    """
    Second iteration of the discovery and monitor
    With the tracert information when find the unique paths
    and use those ports to create multiple iperf sessions
    :param result: previous result
    :param pinger_iteration_id: the iteration id from the db
    :return:
    """

    current_f_name = inspect.currentframe().f_code.co_name

    logger.info("{}: Perform_pipong_iteration_2".format(current_f_name))
    logger.info("{}: Input:{} pinger_iteration_id:{}".format(
        current_f_name, result, pinger_iteration_id))

    s = db.session()

    ponger_t = db.session.query(
        models.Ponger).filter_by(pinger_iteration_id=pinger_iteration_id)
    for pong in ponger_t:
        logger.info("{}: Iterating for pong id:{} {}".format(
            current_f_name, pong.id, pong.address))
        tracert_t = []
        for pport in pong.ponger_port:
            tracert_t.append(
                db.session.query(models.Tracert).filter_by(
                    pinger_iteration_id=pinger_iteration_id,
                    ponger_port_id=pport.id).first())

        paths_port = []
        for row in tracert_t:
            try:
                logger.debug("{}: Task tracert id:{} status:{}".format(
                    current_f_name, row.id, row.status))
                json_res = json.loads(row.result)

                for src_port in json_res['flows']:
                    local_path = []

                    for flow in json_res['flows'][src_port]:
                        flow_name = flow['name']
                        if flow_name is not "":
                            ip_addr_node = flow['received']['ip']['src']
                            local_path.append(ip_addr_node)

                        if flow['is_last'] or (len(local_path) > 0 and
                                               local_path[-1] == pong.address):
                            if len(local_path) > 0:
                                if local_path[-1] == pong.address:
                                    # delete the last element that contains
                                    # the target
                                    del local_path[-1]

                                paths_port.append({
                                    'ponger_port_id':
                                    row.ponger_port.id,
                                    'src_port':
                                    flow['sent']['udp']['sport'],
                                    'dst_port':
                                    flow['sent']['udp']['dport'],
                                    'path':
                                    local_path,
                                })

            except Exception as e:
                logger.error("{}: Error loading data from json result. "
                             "Tracert id: {} result:{} error:{}".format(
                                 current_f_name, row.id, row.result, str(e)))
                continue

        unique_paths = [
            list(x) for x in set(tuple(x['path']) for x in paths_port)
        ]

        unique_path_port = []
        for path in unique_paths:
            for data in paths_port:
                data_path = data['path']
                if path == data_path:
                    unique_path_port.append(data)
                    break

        logger.info("{}: Unique_path_port for ponger: {} {}".format(
            current_f_name, pong.address, unique_path_port))

        for path_port in unique_path_port:
            logger.debug(
                "{}: Creating iperf pinger_iteration_id:{} ponger_port_id:{} ".
                format(current_f_name, pinger_iteration_id,
                       path_port['ponger_port_id']))

            iperf_n_t = models.Iperf(
                pinger_iteration_id=pinger_iteration_id,
                status='PENDING',
                ponger_port_id=path_port['ponger_port_id'],
                src_port=path_port['src_port'])
            s.add(iperf_n_t)
            s.flush()
        s.commit()

    task_list = []
    ponger_t = db.session.query(
        models.Ponger).filter_by(pinger_iteration_id=pinger_iteration_id)
    for pong in ponger_t:
        logger.debug("{}: Task creating iperf tasks ponger_id:{}".format(
            current_f_name, pong.id))
        task_list.append(do_iperf3_client.s(pong.id))

    iter_t = db.session.query(
        models.PingerIteration).filter_by(id=pinger_iteration_id).first()
    if iter_t:
        iter_t.status = "RUNNING_IPERF"
        s.commit()

    chord(task_list)(perform_pipong_iteration_3.s(pinger_iteration_id))


@celery.task(time_limit=12000, soft_time_limit=12000)
def perform_pipong_iteration_1(pinger_iteration_id):
    """
    First iteration of the discovery and monitor
    Create all tracert configurations on the DB perform the tasks
    asynchronously
    When all task are finished a callback is performed to the second
    iteration step

    :param pinger_iteration_id: the iteration id from the db
    :return:
    """
    current_f_name = inspect.currentframe().f_code.co_name

    logger.info("{}: Perform_pipong_iteration_1".format(current_f_name))

    iter_t = db.session.query(
        models.PingerIteration).filter_by(id=pinger_iteration_id).first()
    if iter_t is None:
        logger.error("{}: Iteration not found with ID: {}".format(
            current_f_name, pinger_iteration_id))
        return

    if iter_t.status != "CREATED":
        logger.error(
            "{}: Iteration ID:{} is not with in CREATED status: {}".format(
                current_f_name, pinger_iteration_id, iter_t.status))
        return

    s = db.session()
    iter_t.status = "RUNNING"
    s.flush()
    s.commit()

    src_port_start = 40000

    for ponger in iter_t.ponger:
        api_port = ""
        if ponger.api_port != "":
            api_port = ":" + str(ponger.api_port)

        post_url = "{}{}{}/api/v1.0/iperf/server".format(
            ponger.api_protocol, ponger.address, api_port)
        logger.debug("{}: post_url: {}".format(current_f_name, post_url))

        try:
            req_res = requests.post(
                post_url,
                auth=requestHTTPAuth(app.config['HTTP_AUTH_USER'],
                                     app.config['HTTP_AUTH_PASS']),
                timeout=10)
        except Exception as e:
            logger.error("{}: Error requesting servers: {}".format(
                current_f_name, str(e)))
            continue

        if req_res.status_code != 200:
            logger.error(
                "{}: Error creating servers: {} returned status: {}".format(
                    current_f_name, post_url, req_res.status_code))
            continue

        json_data = req_res.json()
        if 'port' not in json_data or 'result' not in json_data or \
                json_data['result'] != 'success':
            logger.error("{}: Json data invalid: {}".format(
                current_f_name, json_data))
            continue

        logger.debug("{}: Host:{}{}{} Json data: {}".format(
            current_f_name, ponger.api_protocol, ponger.address, api_port,
            json_data))
        dst_port = json_data['port']

        # register the tracerts
        src_port_end = src_port_start + iter_t.tracert_qty

        ponger_port_t = models.PongerPort(
            ponger_id=ponger.id,
            dst_port=dst_port,
            src_port_max=src_port_end,
            src_port_min=src_port_start)
        s.add(ponger_port_t)
        s.flush()

        src_port_start = src_port_end + 1

        logger.debug(
            "{}: Creating tracert pinger_iteration_id:{} ponger_port_id:{} ".
            format(current_f_name, pinger_iteration_id, ponger_port_t.id))

        tracert_t = models.Tracert(
            pinger_iteration_id=pinger_iteration_id,
            status='PENDING',
            ponger_port_id=ponger_port_t.id)
        s.add(tracert_t)
        s.flush()

    task_list = []
    tracert_qt = db.session.query(models.Tracert).filter_by(
        pinger_iteration_id=pinger_iteration_id, status='PENDING')
    for row in tracert_qt:
        logger.debug("{}: Task creating tracert tasks tracert_id:{}".format(
            current_f_name, row.id))
        task_list.append(do_dublin_tracert.s(row.id))

    iter_t.status = "RUNNING_TRACEROUTE"
    s.flush()
    s.commit()

    # run async tasks with callback
    chord(task_list)(perform_pipong_iteration_2.s(pinger_iteration_id))

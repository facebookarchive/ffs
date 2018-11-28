#! /usr/bin/python3
# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from datetime import datetime, timedelta
import models
import requests
from requests.auth import HTTPBasicAuth as requestHTTPAuth
from sqlalchemy import or_
from sqlalchemy import desc
import inspect
import numpy as np
import ast
import collections
import ipcalc
import networkx as nx
from networkx.readwrite import json_graph
import json

from main import app, db, celery, logger, pipong_is_master


def outliers_z_score(ys):
    threshold = 0.9

    mean_y = np.mean(ys)
    stdev_y = np.std(ys)
    z_scores = [(y - mean_y) / stdev_y for y in ys]
    return np.where(np.abs(z_scores) > threshold)


def upper_outliers_modified_z_score(ys):
    threshold = 0.5

    median_y = np.median(ys)
    median_absolute_deviation_y = np.median([np.abs(y - median_y) for y in ys])
    modified_z_scores = [
        0.6745 * (y - median_y) / median_absolute_deviation_y for y in ys
    ]
    return np.where(np.array(modified_z_scores) > threshold)


def upper_outliers_iqr(ys):
    """
    This method will return a list of indices of outliers scores
    :param ys: A list of scores
    :return: the indices where the hosts scores are outliers
    """
    quartile_1, quartile_3 = np.percentile(ys, [25, 75])
    iqr = quartile_3 - quartile_1
    upper_bound = quartile_3 + (iqr * 1.5)
    return np.flatnonzero(ys > upper_bound)


def get_outliers(values):
    values = list(values)
    counter = collections.Counter(values)

    more_50p_equal = False
    half_sample_size = len(values) // 2
    for _k, v in counter.items():
        if v > half_sample_size:
            more_50p_equal = True
            break

    if more_50p_equal:
        return outliers_z_score(values)[0]
    else:
        return upper_outliers_modified_z_score(values)[0]


def get_network(ip, netmask=24):
    addr = ipcalc.IP(ip, mask=netmask)
    network_with_cidr = str(addr.guess_network())
    bare_network = network_with_cidr.split('/')[0]
    return addr, network_with_cidr, bare_network


@celery.task(time_limit=1200, soft_time_limit=1100)
def analyse_iteration(master_iteration_id):
    """
    Analyse a iteration, the results of this iteration will be added to the
    'master_iteration_result' table.
    This use a simple approach to detect problematic nodes:
        - the lost_percent using iperf must be 0 for healty paths
        - if the paths have a lost_percent > 0 then this is a problematic path
        - for every pinger result the addresses of the hops are grouped by
            their network address
        - for every network addres on a pinger result a packet_loss
            result is stored
        - then a voting mechanism is performed, if more than half of the
            packet loss value for a single hop have the same value (generally
            this would be 0), then we use this value for the packet loss
            if there is no majority value, then we use the aritmetic mean
            of those packet loss values as the single packet loss of this hop
            * this voting mecanism helps to remove noise in the readings
        - finally the results of all pingers are joined, and for every hop
            there is a list of values assigned from
            every pinger that had touch that hop on a path
        - then its calculated the mean of those measurements
        - the scores are then classified using a 25% outlier percentile metric
        - the outliers are then added to the database
    :return:
    """
    current_f_name = inspect.currentframe().f_code.co_name

    network_segmentation = app.config['DEFAULT_NETWORK_SEGMENTATION']
    logger.debug("{}: Analyse_iteration called".format(current_f_name))

    pinger_iteration_t = db.session.query(
        models.MasterIterationPinger).filter_by(
        master_iteration_id=master_iteration_id, status="FINISHED")

    logger.debug("{}: Found: {} results".format(current_f_name,
                                                pinger_iteration_t.count()))

    s = db.session()

    node_data = []
    edges = set()
    for p_iter in pinger_iteration_t:
        try:
            json_data = ast.literal_eval(p_iter.result)
        except Exception as e:
            logger.error(
                "{}: Error loading data. Master pinger {} result:{} error:{}".
                    format(current_f_name, p_iter.id, p_iter.result, str(e)))
            continue

        node_data_local = {}

        for ping_result in json_data:
            src = ping_result['pinger_address']
            dst = ping_result['ponger_address']
            packet_loss = ping_result['lost_percent']

            path = ping_result['path']

            logger.debug(
                "{}: Testing path:{} src:{} dst:{} lost_percent:{}".format(
                    current_f_name, path, src, dst, packet_loss))

            for i in range(len(path)):
                hop = path[i]
                # remove repeated paths
                if hop == "?":
                    continue

                a1, n1, bn1 = get_network(hop, netmask=network_segmentation)

                if i < len(path) - 1:
                    hop2 = path[i + 1]
                    a2, n2, bn2 = get_network(
                        hop2, netmask=network_segmentation)
                    edges.add((bn1, bn2))

                if bn1 not in node_data_local.keys():
                    node_data_local[bn1] = {'samples': [packet_loss]}
                else:
                    node_data_local[bn1] = {
                        'samples':
                            node_data_local[bn1]['samples'] + [packet_loss]
                    }

        # calculate loss by voting (if it is 0) or by mean
        for k, v in node_data_local.items():
            # count the number of samples
            samples = v['samples']
            max_e = max(samples, key=samples.count)
            count_max_e = samples.count(max_e)

            if count_max_e > len(samples) / 2:
                v['loss'] = max_e
                logger.debug(
                    "{}: k:{} loss:{} using max value:{} count:{}".format(
                        current_f_name, k, v['loss'], max_e, count_max_e))
            else:
                # or calculate the mean
                v['loss'] = sum(samples) / len(samples)
                logger.debug("{}: k:{} loss:{} using mean:{}".format(
                    current_f_name, k, v['loss'], samples))
            pass

        node_data.append(node_data_local)

    # after filtering the information locally for every trace
    # now the traces are joined and the information shared
    node_data_final = {}
    for nd in node_data:
        for k, v in nd.items():
            if k in node_data_final.keys():
                node_data_final[k] = {
                    'samples': node_data_final[k]['samples'] + [v['loss']]
                }
            else:
                node_data_final[k] = {'samples': [v['loss']]}
    for _k, v in node_data_final.items():
        v['mean'] = sum(v['samples']) / len(v['samples'])

    sorted_by_value = sorted(
        node_data_final.items(), key=lambda kv: kv[1]['mean'], reverse=True)
    logger.debug("{}: Node score:{}".format(current_f_name, sorted_by_value))

    problematic_nodes = []

    if len(sorted_by_value) > 0:
        values = [e[1]['mean'] for e in sorted_by_value]
        outliers_index = get_outliers(values)
        logger.debug("{}: outliers_index:{}".format(current_f_name,
                                                    outliers_index))
        for i in outliers_index:
            k = sorted_by_value[i][0]
            score = sorted_by_value[i][1]['mean']
            logger.debug("{}: problematic host:{} score:{}".format(
                current_f_name, k, score))

            s.add(
                models.MasterIterationResult(
                    master_iteration_id=master_iteration_id,
                    problematic_host=k,
                    score=score))

            problematic_nodes.append(k)

        s.commit()

    # generate the graph with the probabilities
    G = nx.DiGraph()
    for k, v in node_data_final.items():
        G.add_node(k, mean=v['mean'])

    G.add_edges_from([(k[0], k[1]) for k in list(edges)])

    g_json = json_graph.node_link_data(G)
    logger.debug("{}: Json graph:{}".format(current_f_name, g_json))

    master_it = db.session.query(models.MasterIteration).filter_by(id=master_iteration_id).first()
    if master_it:
        master_it.json_graph = json.dumps(g_json)
        s.commit()

    return problematic_nodes


@celery.task(time_limit=120, soft_time_limit=120)
def create_iteration():
    """
    Create a new iteration in a master node
    This will run at intervals on the master server and will
    trigger the analysis of the previouly finished iteration and generate
    a new master iteration with the registrered pingers

    :return:
    """
    current_f_name = inspect.currentframe().f_code.co_name

    logger.debug("{}: Create_iteration called".format(current_f_name))

    if not pipong_is_master():
        return None

    ponger_t = db.session.query(models.RegisteredPongerNode).all()
    logger.debug("{}: Ponger_t: {}".format(current_f_name, ponger_t))

    ponger_list = {}
    for row in ponger_t:
        ponger_list[row.address] = {
            'api_port': row.api_port,
            'api_protocol': row.api_protocol
        }

    logger.debug("{}: Ponger list: {}".format(current_f_name, ponger_list))

    http_user = app.config['HTTP_AUTH_USER']
    http_pass = app.config['HTTP_AUTH_PASS']
    tracert_qty = app.config['MASTER_TRACERT_QTY']

    s = db.session()

    # get last iteration
    previous_master_iter = db.session.query(models.MasterIteration).order_by(
        desc(models.MasterIteration.created_date)).limit(1).first()

    if previous_master_iter:
        logger.debug("{}: Previous_master_iter: {} status:{}".format(
            current_f_name, previous_master_iter.id, previous_master_iter.status))

        if previous_master_iter.status != 'FINISHED':
            logger.error(
                "{}: Cannot start a new iteration while the previous one (id:{}) is not FINISHED (status:{})".format(
                    current_f_name, previous_master_iter.id, previous_master_iter.status))
            return None

    # create a new master iteration
    master_ite_t = models.MasterIteration()
    s.add(master_ite_t)
    s.flush()
    s.commit()

    # start the pinger sessions
    pinger_t = db.session.query(models.RegisteredPingerNode).all()
    for pinger in pinger_t:
        plist = dict(ponger_list)
        if pinger.address in plist.keys():
            del plist[pinger.address]

        if len(plist.keys()) > 0:
            s.add(
                models.MasterIterationPinger(
                    master_iteration_id=master_ite_t.id,
                    registered_pinger_id=pinger.id,
                    status="RUNNING"))
            s.commit()
        else:
            # dont call any pinger that does not have pongers to query
            continue

        post_url = "http://{}:{}/api/v1.0/start_session".format(
            pinger.address, pinger.api_port)
        post_json = {
            "hosts": plist,
            "tracert_qty": tracert_qty,
            "master_iteration_id": master_ite_t.id
        }
        try:
            logger.debug("post url: {} json:{}".format(post_url, post_json))
            requests.post(
                post_url,
                auth=requestHTTPAuth(http_user, http_pass),
                json=post_json,
                timeout=5)
        except Exception as e:
            logger.error(
                "{}: Error calling create session on pinger {}:{} {}".format(
                    current_f_name, pinger.address, pinger.api_port, str(e)))

    logger.debug("{}: Create_iteration finished".format(current_f_name))


@celery.task(time_limit=120, soft_time_limit=120)
def remove_old_nodes():
    """
    Delete older pinger and pongers registered in more than 30 minutes
    :return:
    """
    current_f_name = inspect.currentframe().f_code.co_name

    logger.info("{}: Remove_old_nodes called".format(current_f_name))

    if not pipong_is_master():
        return None

    since = datetime.now() - timedelta(minutes=30)

    s = db.session()

    pinger_t = db.session.query(models.RegisteredPingerNode).filter(
        or_(models.RegisteredPingerNode.last_updated_date is None,
            models.RegisteredPingerNode.last_updated_date < since))

    logger.debug("{}: Old pingers: {}".format(current_f_name,
                                              pinger_t.count()))
    pinger_t.delete()

    ponger_t = db.session.query(models.RegisteredPongerNode).filter(
        or_(models.RegisteredPongerNode.last_updated_date is None,
            models.RegisteredPongerNode.last_updated_date < since))

    logger.debug("{}: Old pongers: {}".format(current_f_name,
                                              ponger_t.count()))
    ponger_t.delete()

    s.commit()


@celery.task(time_limit=120, soft_time_limit=120)
def check_master_iteration_done(master_iteration_id):
    """
    Check if for the specific iteration all the pingers have sent their results
    :return:
    """

    current_f_name = inspect.currentframe().f_code.co_name
    # logger.info("{}: check_master_iteration_done called".format(current_f_name))
    is_finished = False

    master_it = db.session.query(models.MasterIteration).filter_by(id=master_iteration_id).first()
    if master_it is None:
        logger.error("{}: No MasterIteration found with id: {}".format(
            current_f_name, master_iteration_id))
        return {'is_finished': is_finished, 'percentage': 0.0}

    count = 0
    pinger_size = len(master_it.master_iteration_pinger)
    for master_pinger_it in master_it.master_iteration_pinger:
        if master_pinger_it.status == "FINISHED":
            count += 1

    if count >= pinger_size:
        s = db.session()
        is_finished = True
        master_it.status = 'FINISHED'
        s.commit()

    if count > pinger_size:
        logger.warn("{}: count > pinger_size {}>{}".format(
            current_f_name, count, pinger_size))
        count = pinger_size

    percent = 0
    if pinger_size > 0:
        percent = (count / float(pinger_size)) * 100

    return {'is_finished': is_finished, 'percentage': percent, 'count': count,
            'total': pinger_size}


@celery.task(time_limit=120, soft_time_limit=120)
def finish_old_iterations():
    """
    Finish the iterations that are older than 30 minutes
    :return:
    """
    current_f_name = inspect.currentframe().f_code.co_name

    logger.info("{}: Remove_old_nodes called".format(current_f_name))

    if not pipong_is_master():
        return None

    since = datetime.now() - timedelta(minutes=30)

    s = db.session()

    master_t = db.session.query(models.MasterIteration).filter(
        or_(models.MasterIteration.created_date is None,
            models.MasterIteration.created_date < since))

    logger.debug("{}: Old iterations: {}".format(current_f_name,
                                                 master_t.count()))

    for e in master_t:
        e.status = "FINISHED"

    s.commit()

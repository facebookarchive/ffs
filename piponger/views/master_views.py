# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from flask import request, abort, jsonify, send_from_directory
import models
import tasks.master_tasks
from main import app, db, auth, logger, pipong_is_master
from datetime import datetime
import inspect
from sqlalchemy import inspect as isql


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key) for c in isql(obj).mapper.column_attrs}


@app.route('/force_create_iteration')
@auth.login_required
def force_create_iteration():
    """
    Force the generation of a new piponger iteration
    (instead of waiting ~30 minutes per iteration)
    :return:
    """
    current_f_name = inspect.currentframe().f_code.co_name

    logger.info('{} force_create_iteration called'.format(current_f_name))

    tasks.master_tasks.create_iteration.apply_async(args=[], kwargs={})

    return jsonify({'result': 'success', 'msg': 'Force new iteration called'})


@app.route('/api/v1.0/master/register_pinger_result', methods=['POST'])
@auth.login_required
def register_pinger_result():
    """
    Register a pinger results in this master node
    The results came in JSON format and are related to the iperf
    session performed on the pinger node
    :return:
    """

    current_f_name = inspect.currentframe().f_code.co_name

    logger.info("{}: called".format(current_f_name))

    if not pipong_is_master():
        logger.info("{}: pipong_is_master:{}".format(current_f_name,
                                                     pipong_is_master()))
        return jsonify({
            'result': 'failure',
            'msg': 'this server is not a master'
        })

    data = request.get_json()

    ip_addr = request.remote_addr
    master_iteration_id = data['master_remote_id']
    pinger_port = data['local_port']
    pinger_result = data['result']

    registrered_t = db.session.query(models.RegisteredPingerNode).filter_by(
        address=ip_addr, api_port=pinger_port).first()

    if not registrered_t:
        logger.error(
            "{}: Error, the pinger node was not registered {}:{}".format(
                current_f_name, ip_addr, pinger_port))
        return jsonify({
            'result': 'failure',
            'msg': 'the pinger node was not registered'
        })

    pinger_iteration_t = db.session.query(
        models.MasterIterationPinger).filter_by(
            master_iteration_id=master_iteration_id,
            registered_pinger_id=registrered_t.id).first()

    if not pinger_iteration_t:
        logger.error("{}: Error, the master pinger iteration was not found. "
                     "Master iter:{} registered pinger:{}".format(
                         current_f_name, master_iteration_id,
                         registrered_t.id))
        return jsonify({
            'result': 'failure',
            'msg': 'the master pinger iteration was not found'
        })

    if pinger_iteration_t.status == "FINISHED":
        logger.error("{}: Error, the pinger iteration was finished. "
                     "Pinger iteration:{} status:{}".format(
                         current_f_name, pinger_iteration_t.id,
                         pinger_iteration_t.status))
        return jsonify({
            'result':
            'failure',
            'msg':
            ' the master pinger iteration is already finished'
        })

    s = db.session()
    for e in pinger_result:
        e['pinger_address'] = ip_addr

    pinger_iteration_t.result = str(pinger_result)
    pinger_iteration_t.status = "FINISHED"
    s.commit()

    logger.info(
        "{}: Pinger result registrered. Pinger address:{} result: {}".format(
            current_f_name, ip_addr, str(pinger_result)))

    return jsonify({'result': 'success'})


@app.route('/api/v1.0/master/register_ponger', methods=['POST'])
@auth.login_required
def register_ponger():
    """
    Register a ponger in this master node
    :return:
    """

    current_f_name = inspect.currentframe().f_code.co_name

    if not pipong_is_master():
        return jsonify({
            'result': 'failure',
            'msg': 'this server is not a master'
        })

    data = request.get_json()

    ip_addr = request.remote_addr
    api_port = data['api_port']
    api_protocol = data['api_protocol']
    registrered_t = db.session.query(models.RegisteredPongerNode).filter_by(
        address=ip_addr, api_port=api_port).first()

    s = db.session()

    if not registrered_t:
        pingp_t = models.RegisteredPongerNode(
            address=ip_addr, api_port=api_port, api_protocol=api_protocol)
        s.add(pingp_t)
        logger.debug(
            "{}: Registering pong: host:{} api_port:{} api_protocol:{}".format(
                current_f_name, ip_addr, api_port, api_protocol))
    else:
        registrered_t.last_updated_date = datetime.now()

    s.commit()

    return jsonify({'result': 'success'})


@app.route('/api/v1.0/master/register_pinger', methods=['POST'])
@auth.login_required
def register_pinger():
    """
    Register a pinger in this master node
    :return:
    """

    current_f_name = inspect.currentframe().f_code.co_name

    if not pipong_is_master():
        return jsonify({
            'result': 'failure',
            'msg': 'this server is not a master'
        })

    data = request.get_json()

    ip_addr = request.remote_addr
    api_port = data['api_port']
    api_protocol = data['api_protocol']
    registrered_t = db.session.query(models.RegisteredPingerNode).filter_by(
        address=ip_addr, api_port=api_port).first()

    s = db.session()

    if not registrered_t:
        pingp_t = models.RegisteredPingerNode(
            address=ip_addr, api_port=api_port, api_protocol=api_protocol)
        s.add(pingp_t)
        logger.debug(
            "{}: Registering ping: host:{} api_port:{} api_protocol:{}".format(
                current_f_name, ip_addr, api_port, api_protocol))
    else:
        registrered_t.last_updated_date = datetime.now()

    s.commit()

    return jsonify({'result': 'success'})


@app.route('/get_last_result_plot', methods=['GET'])
@auth.login_required
def get_result_plot():
    """
    Get the last result plot using matplotlib
    :return:
    """

    inspect.currentframe().f_code.co_name

    if not pipong_is_master():
        abort(404)

    return send_from_directory(
        '/tmp/', 'last_iter_result.png', as_attachment=False)

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from flask import request
from flask import jsonify
import models
import tasks.pinger_tasks
import traceback
from main import app, db, auth, logger, pipong_is_pinger
import inspect


@app.route('/api/v1.0/start_session', methods=['POST'])
@auth.login_required
def start_session():
    """
    Receive a json with the configuration of a new iteration.
    The json follows this configuration:
    {
        "hosts": {
            "127.0.0.1": {
                "api_port": 5003,
                "api_protocol": "http://",
            }
        },
        "tracert_qty": 20,
        "master_iteration_id": "myremoteid02"
    }
    :return:
    """
    current_f_name = inspect.currentframe().f_code.co_name

    logger.info('{}: Start_session called'.format(current_f_name))

    if not pipong_is_pinger():
        return jsonify({
            'result': 'failure',
            'msg': 'this server is not a pinger'
        })

    response = {'result': 'success'}
    data = request.get_json()
    logger.info(data)

    try:
        host_list = data['hosts']
        remote_id = data['master_iteration_id']
        tracert_qty = data['tracert_qty']
        ip_addr = request.remote_addr

        exists = db.session.query(
            db.session.query(models.PingerIteration).filter_by(
                remote_id=str(remote_id)).exists()).scalar()

        if not exists:
            s = db.session()
            iter_t = models.PingerIteration(
                status="CREATED",
                remote_id=str(remote_id),
                remote_address=ip_addr,
                tracert_qty=tracert_qty)
            s.add(iter_t)
            s.flush()

            for k, v in host_list.items():
                api_port = v['api_port']
                api_protocol = v['api_protocol']
                ponger_t = models.Ponger(
                    address=k,
                    pinger_iteration_id=iter_t.id,
                    api_port=api_port,
                    api_protocol=api_protocol)
                s.add(ponger_t)
                s.flush()

            s.commit()

            logger.info('{}: New pinger iteration ID:{}'.format(
                current_f_name, iter_t.id))

            tasks.pinger_tasks.perform_pipong_iteration_1.apply_async(
                args=[iter_t.id], kwargs={})
            response['ping_iteration_id'] = iter_t.id
        else:
            logger.error(
                '{}: Remote id already registered'.format(current_f_name))
            return jsonify({
                'result': 'failure',
                'msg': 'remote id already registered'
            })

        logger.info('{}: port_list:{} ip_addr:{} exists:{}'.format(
            current_f_name, host_list, ip_addr, exists))
    except Exception:
        exception_log = traceback.format_exc()
        logger.debug('{}: e:{}'.format(current_f_name, exception_log))
        jsonify({'result': 'failure', 'msg': exception_log})

    return jsonify(response)

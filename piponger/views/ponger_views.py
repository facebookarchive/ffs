# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from flask import request
from flask import jsonify
import models
import tasks.ponger_tasks
from main import app, db, auth, logger, pipong_is_ponger
import inspect


@app.route('/api/v1.0/iperf/server', methods=['POST'])
@auth.login_required
def request_iperf_server():
    """
    This method is to be executed by a pinger.
    The ponger reserves a port to be used exclusivelly by the requesting pinger
    :return:
    """
    current_f_name = inspect.currentframe().f_code.co_name

    logger.info("{}: Request_iperf_servers".format(current_f_name))

    if not pipong_is_ponger():
        return jsonify({
            'result': 'failure',
            'msg': 'this server is not a ponger'
        })

    ip_addr = request.remote_addr
    pingerp_t = db.session.query(
        models.AllocatedPingerPort).filter_by(address=ip_addr).first()

    if not pingerp_t:
        all_t = db.session.query(models.AllocatedPingerPort).all()
        all_ports = [row.port for row in all_t]
        possible_ports = list(
            range(app.config['RESERVED_PORT_RANGE_MIN'],
                  app.config['RESERVED_PORT_RANGE_MAX']))
        available_ports = sorted(list(set(possible_ports) - set(all_ports)))
        port = available_ports[0]
        logger.debug("{}: For host:{} new selected port generated:{}".format(
            current_f_name, ip_addr, port))

        s = db.session()
        pingp_t = models.AllocatedPingerPort(address=ip_addr, port=port)
        s.add(pingp_t)
        s.commit()

    else:
        port = pingerp_t.port
        logger.debug("{}: For host:{} selected port:{}".format(
            current_f_name, ip_addr, port))

    result = tasks.ponger_tasks.create_iperf_server.delay(port)
    creation_status = result.get()

    if not creation_status:
        return jsonify({
            'result': 'failure',
            'msg': 'cannot start iperf server'
        })

    return jsonify({'result': 'success', 'port': port})

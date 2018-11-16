# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from flask import jsonify, Blueprint, url_for
import models
from main import (app, db, auth, logger, pipong_is_pinger, pipong_is_ponger,
                  pipong_is_master)
from sqlalchemy import desc
import inspect

bp = Blueprint('common', __name__)


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)


@bp.route('/', methods=('GET', 'POST'))
@auth.login_required
def home():
    """
    index view
    return the status of this node:
        if ponger returns the pinger registrered in this node
        if pinger returns the list of pongers and last iteration status
        if master returns list of pongers and pingers and last iteration result
    :return:
    """
    current_f_name = inspect.currentframe().f_code.co_name

    logger.info('{}: home called'.format(current_f_name))

    result_dict = {}

    is_pinger = pipong_is_pinger()
    is_ponger = pipong_is_ponger()
    is_master = pipong_is_master()

    result_dict['capabilities'] = {
        'is_pinger': is_pinger,
        'is_ponger': is_ponger,
        'is_master': is_master
    }

    if is_pinger:
        last_iteration_status = {}
        ponger_list = []

        iteration = db.session.query(models.PingerIteration).order_by(
            desc(models.PingerIteration.created_date)).limit(1).first()
        if iteration:
            last_iteration_status = {
                'remote_address': iteration.remote_address,
                'status': iteration.status,
                'tracert_qty': iteration.tracert_qty,
                'created_date': iteration.created_date
            }

            for p in iteration.ponger:
                ponger_list.append({
                    'address': p.address,
                    'api_port': p.api_port,
                    'api_protocol': p.api_protocol
                })

        result_dict['pinger_info'] = {
            'last_iteration_status': last_iteration_status,
            'ponger_list': ponger_list
        }

    if is_ponger:
        pinger_port_list = []

        pinger_port_t = db.session.query(models.AllocatedPingerPort)
        for p in pinger_port_t:
            pinger_port_list.append({'address': p.address, 'port': p.port})

        result_dict['ponger_info'] = {'pinger_port_list': pinger_port_list}

    if is_master:
        last_iteration_status = {}
        registrered_pingers = []
        registrered_pongers = []

        previous_master_iter = db.session.query(
            models.MasterIteration).filter_by(status='FINISHED').order_by(
                desc(models.MasterIteration.created_date)).limit(1).first()

        if previous_master_iter:
            logger.debug("{}: Previous_master_iter: {}".format(
                current_f_name, previous_master_iter.id))
            last_iteration_status[
                'created_date'] = previous_master_iter.created_date
            last_iteration_status['problematic_hosts'] = [
                it_res.problematic_host
                for it_res in previous_master_iter.master_iteration_result
            ]

        r_pingers_t = db.session.query(models.RegisteredPingerNode)
        for pinger in r_pingers_t:
            registrered_pingers.append({
                'address': pinger.address,
                'api_port': pinger.api_port,
                'api_protocol': pinger.api_protocol
            })

        r_pongers_t = db.session.query(models.RegisteredPongerNode)
        for ponger in r_pongers_t:
            registrered_pongers.append({
                'address': ponger.address,
                'api_port': ponger.api_port,
                'api_protocol': ponger.api_protocol
            })

        result_dict['master_info'] = {
            'last_iteration_status': last_iteration_status,
            'registrered_pingers': registrered_pingers,
            'registrered_pongers': registrered_pongers
        }

    return jsonify(result_dict)


@bp.route("/site-map", methods=('GET', 'POST'))
def site_map():
    links = []
    for rule in app.url_map.iter_rules():
        if has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append({url: [rule.endpoint, list(rule.methods)]})

    return jsonify(links)
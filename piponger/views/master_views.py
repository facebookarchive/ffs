# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from flask import request, abort, jsonify, send_from_directory, Blueprint, render_template
import models
import tasks.master_tasks
from main import db, auth, logger, pipong_is_master
from datetime import datetime
import inspect
from sqlalchemy import inspect as isql
from sqlalchemy import desc
import networkx as nx
import matplotlib.pyplot as plt
from networkx.readwrite import json_graph
import json
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io
from flask import Response

bp = Blueprint('master', __name__, template_folder='templates')


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key) for c in isql(obj).mapper.column_attrs}


@bp.route('/monitor')
@auth.login_required
def monitor():
    """
    HTML template to monitor and start iterations
    :return:
    """

    current_f_name = inspect.currentframe().f_code.co_name
    logger.info('{} called'.format(current_f_name))

    return render_template('master/monitor.html', title='Monitor')


@bp.route('/force_create_iteration')
@auth.login_required
def force_create_iteration():
    """
    Force the generation of a new piponger iteration
    (instead of waiting ~30 minutes per iteration)
    :return:
    """

    current_f_name = inspect.currentframe().f_code.co_name
    logger.info('{} force_create_iteration called'.format(current_f_name))

    # get last iteration
    previous_master_iter = db.session.query(models.MasterIteration).order_by(
        desc(models.MasterIteration.created_date)).limit(1).first()

    if previous_master_iter and previous_master_iter.status != 'FINISHED':
        return jsonify({'result': 'failure', 'msg': 'Previous iteration is not FINISHED (status: {})'.format(
            previous_master_iter.status)})

    tasks.master_tasks.create_iteration.apply_async(args=[], kwargs={})
    return jsonify({'result': 'success', 'msg': 'Force new iteration called'})


@bp.route('/api/v1.0/master/register_pinger_result', methods=['POST'])
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

    res = tasks.master_tasks.check_master_iteration_done(master_iteration_id)
    logger.debug(
        "{}: check_master_iteration_done: {}".format(
            current_f_name, res))

    if res['is_finished']:

        # big info message on the logs for easy visualization
        logger.info("{}: ################################".format(current_f_name))
        logger.info("{}: # ITERATION id:{} FINISHED".format(current_f_name, master_iteration_id))
        logger.info("{}: ################################".format(current_f_name))

        # analyse last iteration results
        tasks.master_tasks.analyse_iteration.apply_async(args=[master_iteration_id], kwargs={})

    return jsonify({'result': 'success'})


@bp.route('/api/v1.0/master/register_ponger', methods=['POST'])
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


@bp.route('/api/v1.0/master/register_pinger', methods=['POST'])
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


@bp.route('/get_result_plot/<master_iteration_id>', methods=['GET'])
@auth.login_required
def get_result_plot(master_iteration_id):
    """
    Get the last result plot using matplotlib
    :return:
    """

    current_f_name = inspect.currentframe().f_code.co_name

    if not pipong_is_master():
        logger.debug(
            "{}: This node is not a master}".format(
                current_f_name))
        abort(404)

    master_it = db.session.query(models.MasterIteration).filter_by(id=master_iteration_id).first()
    if master_it is None:
        logger.error("{}: No MasterIteration found with id: {}".format(
            current_f_name, master_iteration_id))
        abort(404)

    if not master_it.json_graph:
        logger.error("{}: Empty json_graph for id: {}".format(
            current_f_name, master_iteration_id))
        abort(404)

    js_graph = json.loads(master_it.json_graph)
    G = json_graph.node_link_graph(js_graph)

    pos = nx.drawing.nx_agraph.graphviz_layout(G, prog='dot')
    node_labels = {}
    for k, v in G.nodes(data=True):
        node_labels[k] = '{}\n{:.2f}%'.format(k, v['mean'])

    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=5)

    node_colors = [G.node[n]['mean'] for n in G.nodes()]

    nx.draw_networkx_nodes(
        G,
        pos,
        node_color=node_colors,
        node_size=600,
        node_shape='o',
        cmap=plt.cm.OrRd,
        vmin=0.,
        vmax=100.)
    nx.draw_networkx_edges(
        G, pos, arrowstyle='-|>', arrowsize=20, edge_color='black', width=1)

    fig = plt.gcf()
    fig.set_size_inches(30, 20)
    plt.savefig('/tmp/last_generated_result.png', dpi=250)

    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')


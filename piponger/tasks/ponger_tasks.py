#! /usr/bin/python3
# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import time
from celery.exceptions import SoftTimeLimitExceeded
import subprocess
import inspect
import traceback

from main import app, celery, logger


@celery.task(time_limit=120, soft_time_limit=120)
def create_iperf_server(port):
    """
    Create iperf servers at random ports
    The max number of servers is defined by parameters
    :param port: the port used to start the server
    :return:
    """
    current_f_name = inspect.currentframe().f_code.co_name

    try:
        # kill program using this port
        cmd = ['lsof', '-t', '-i:{}'.format(port)]
        popen_obj = subprocess.Popen(
            cmd,
            close_fds=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = popen_obj.communicate()
        pid_port = out.strip()

        if pid_port:
            logger.info("{}: iperfserver already running with pid: {}".format(
                current_f_name, pid_port))

            cmd = ['kill', '-9', pid_port]
            popen_obj = subprocess.Popen(
                cmd,
                close_fds=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            out, err = popen_obj.communicate()

        cmd = [
            'timeout', '6000', app.config['IPERF3_SERVER_SCRIPT_LOCATION'],
            str(port)
        ]

        popen_obj = subprocess.Popen(cmd, close_fds=True)
        time.sleep(2)

        # poll() returns None when the process is still running
        # https://docs.python.org/3/library/subprocess.html#popen-objects
        poll_msg = popen_obj.poll()
        if poll_msg is None:
            return True

        logger.info("{}: Error opening iperf server: {}. Command: {}".format(
            current_f_name, poll_msg, ''.join(str(e) for e in cmd)))
        logger.info("{}: Command: {}".format(current_f_name, cmd))

        return False
    except SoftTimeLimitExceeded:
        return False
    except Exception as e:
        logger.error("{}: Error creating iperf server: {} {}".format(
            current_f_name, str(e), traceback.format_exc()))
        return False

#! /usr/bin/python3
# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from celery.exceptions import SoftTimeLimitExceeded
import requests
from requests.auth import HTTPBasicAuth as requestHTTPAuth
import inspect

from main import app, celery, logger, pipong_is_pinger, pipong_is_ponger


@celery.task(time_limit=120, soft_time_limit=120)
def report_to_master(local_port, local_protocol):
    """
    Report current status to master (up status as ponger or pinger)
    Ponger and pinger capabilities can be defined on config file
    IS_PINGER = True # pinger node will generate a 'ping' like communication
                        with the pongers
    IS_PONGER = True # a ponger will receive a pinger message and
                        respond to it
    IS_MASTER = True # define if this server is going to be the master
                        of puppets
                     # master keeps a log of pingers and pongers starts,
                     # orchestrates new iterations
                     # and receive results from the pingers
    :return:
    """
    current_f_name = inspect.currentframe().f_code.co_name

    master_host = app.config['MASTER_SERVER']
    master_port = app.config['MASTER_PORT']

    http_user = app.config['HTTP_AUTH_USER']
    http_pass = app.config['HTTP_AUTH_PASS']

    try:
        if pipong_is_pinger():
            post_url = "http://{}:{}/api/v1.0/master/register_pinger".format(
                master_host, master_port)
            try:
                requests.post(
                    post_url,
                    auth=requestHTTPAuth(http_user, http_pass),
                    json={
                        "api_port": local_port,
                        "api_protocol": local_protocol
                    },
                    timeout=5)
            except Exception as e:
                logger.error(
                    "{}: Error registering pinger in master: {}".format(
                        current_f_name, str(e)))

        if pipong_is_ponger():
            post_url = "http://{}:{}/api/v1.0/master/register_ponger".format(
                master_host, master_port)
            try:
                requests.post(
                    post_url,
                    auth=requestHTTPAuth(http_user, http_pass),
                    json={
                        "api_port": local_port,
                        "api_protocol": local_protocol
                    },
                    timeout=5)

            except Exception as e:
                logger.error(
                    "{}: Error registering ponger in master: {}".format(
                        current_f_name, str(e)))

        return str("success")
    except SoftTimeLimitExceeded:
        return None
#!/usr/bin/env bash
# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

if [ $# -ne 1 ]; then
    echo "usage: ./create_iperf_server.sh port" >> /dev/stderr
    exit 1
fi

port=$1

if [ -z "$port" ]
then
      echo "A port must be defined as second argument" >> /dev/stderr
      exit 1
fi

clean_port=`echo $port | tr -dc '[0-9]'`
current_ip=`hostname --all-ip-addresses | awk '{print $1;}'`

result=`iperf3 --server --port $clean_port --version4 -1`

echo $result

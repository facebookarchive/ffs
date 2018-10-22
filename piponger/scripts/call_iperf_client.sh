#!/usr/bin/env bash
# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

if [ $# -ne 3 ]; then
    echo "usage: ./call_iperf_client.sh remote_host remote_port local_port" >> /dev/stderr
    exit 1
fi

remote_host=$1
remote_port=$2
local_port=$3

if [ -z "$remote_host" ]
then
      echo "A host must be defined as first argument" >> /dev/stderr
      exit 1
fi

if [ -z "$remote_port" ]
then
      echo "A remote port must be defined as second argument" >> /dev/stderr
      exit 1
fi

if [ -z "$local_port" ]
then
      echo "A local port must be defined as third argument" >> /dev/stderr
      exit 1
fi

clean_remote_host=`echo $remote_host | tr -dc '[:alnum:]\.\-'`
clean_remote_port=`echo $remote_port | tr -dc '[0-9]'`
clean_local_port=`echo $local_port | tr -dc '[0-9]'`
current_ip=`hostname --all-ip-addresses | awk '{print $1;}'`

result=`iperf3 --version4 --udp --client $clean_remote_host --port $clean_remote_port --bind $current_ip --cport $clean_local_port --zerocopy --json --bandwidth 10M --time 25`

echo $result

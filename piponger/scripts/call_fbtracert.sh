#!/usr/bin/env bash
# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

if [ $# -ne 3 ]; then
    echo "usage: ./call_fbtracert.sh remote_host remote_port local_port" >> /dev/stderr
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

fbtracert_resut=`/usr/bin/fbtracert -srcAddr $current_ip -v 99 -baseSrcPort $clean_local_port -targetPort $clean_remote_port -alsologtostderr -maxSrcPorts 1 -showAll -logtostderr=true -jsonOutput $clean_remote_host`

echo $fbtracert_resut

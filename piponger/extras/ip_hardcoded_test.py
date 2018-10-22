# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import dublintraceroute
import json
import subprocess
import time
import numpy as np
import collections


class Target:
    def __init__(self, ip, src_port, dst_port, route, packet_loss=0.0):
        self.ip = ip
        self.src_port = src_port
        self.dst_port = dst_port
        if route:
            self.route = route
        else:
            self.route = []
        self.packet_loss = packet_loss


class IpExperiment:
    def __init__(
            self,
            target_l,
            iperf_script_path="/srv/piponger/scripts/call_iperf_client.sh"):
        self.target_l = target_l
        self.iperf_script_path = iperf_script_path

    def perform_tracert(self):
        print("Performing tracert...")
        for t in self.target_l:

            dublin = dublintraceroute.DublinTraceroute(
                t.ip,
                npaths=1,
                delay=25,
                dport=t.dst_port,
                sport=t.src_port,
                broken_nat=False,
                iterate_sport=False)
            results = dublin.traceroute()

            local_path = []
            for sport in results['flows']:

                port_res = results['flows'][sport]

                for flow in port_res:
                    flow_name = flow['name']
                    if flow_name is not "":
                        local_path.append(flow['received']['ip']['src'])

                    if flow['is_last'] or (len(local_path) > 0
                                           and local_path[-1] == t.ip):
                        if len(local_path) > 0:
                            if local_path[-1] == t.ip:
                                del local_path[-1]
                            break

                print("ip:{} sport:{} dport:{} path:{}", t.ip, t.src_port,
                      t.dst_port, local_path)
                if len(local_path) <= 0:
                    local_path = [t.ip]
                    print(
                        "ERROR ip:{} has path with len 0, adding "
                        "ip to path:{}".
                        format(t.ip, local_path))

                t.route = local_path
        pass

    def perform_iperf(self):
        print("Performing iperf...")
        for t in self.target_l:
            max_tries = 5
            client_tries = 0
            success = False

            while client_tries < max_tries and success is False:
                cmd = [
                    self.iperf_script_path,
                    str(t.ip),
                    str(t.dst_port),
                    str(t.src_port),
                ]

                print("iperf cmd: {}".format(cmd))

                try:
                    cmd_result_str = subprocess.check_output(cmd).decode(
                        "utf-8")
                    print("iperf cmd_result_str: {}".format(cmd_result_str))

                    if "lost_percent" in cmd_result_str:
                        success = True
                        iperf_res = json.loads(cmd_result_str)
                        t.packet_loss = iperf_res['end']['sum']['lost_percent']

                        print("IPERF ip:{} sport:{} dport:{} packet_loss:{}".
                              format(t.ip, t.src_port, t.dst_port,
                                     t.packet_loss))
                    else:
                        print(
                            "ERROR IPERF no lost_percent found "
                            "on cmd_result_str: {}/{} host:{} {}".
                            format(client_tries, max_tries, str(t.ip),
                                   cmd_result_str))

                except subprocess.CalledProcessError as e:
                    output = e.output.decode()
                    print("ERROR IPERF: {}".format(output))

                if not success:
                    client_tries += 1
                    time.sleep(5)

            if not success:
                print(
                    "ERROR IPERF cannot communicate with iperf server at: {}".
                    format(t.ip))

        pass

    @staticmethod
    def outliers_z_score(ys):
        threshold = 0.9

        mean_y = np.mean(ys)
        stdev_y = np.std(ys)
        z_scores = [(y - mean_y) / stdev_y for y in ys]
        # print('z_scores:', z_scores)
        return np.where(np.abs(z_scores) > threshold)

    @staticmethod
    def upper_outliers_modified_z_score(ys):
        threshold = 0.5

        median_y = np.median(ys)
        median_absolute_deviation_y = np.median(
            [np.abs(y - median_y) for y in ys])
        modified_z_scores = [
            0.6745 * (y - median_y) / median_absolute_deviation_y for y in ys
        ]
        # print(modified_z_scores)
        return np.where(np.array(modified_z_scores) > threshold)

    @staticmethod
    def get_outliers(values):
        values = list(values)
        counter = collections.Counter(values)

        more_50p_equal = False
        half_sample_size = len(values) // 2
        for _k, v in counter.items():
            if v > half_sample_size:
                more_50p_equal = True
                break

        if more_50p_equal:
            return IpExperiment.outliers_z_score(values)[0]
        else:
            return IpExperiment.upper_outliers_modified_z_score(values)[0]

    def compute_results(self):
        print("Computing results...")
        node_data = {}

        for t in self.target_l:
            print("Target('{}', {}, {}, {}, {}),".format(
                t.ip, t.src_port, t.dst_port, t.route, t.packet_loss))

            for node in t.route:
                # remove repeated paths
                if node == "?":
                    continue

                if node not in node_data.keys():
                    node_data[node] = {
                        'count': 1,
                        'lost_percent': t.packet_loss
                    }
                else:
                    node_data[node]['count'] += 1
                    node_data[node]['lost_percent'] += t.packet_loss

        node_score = {
            node:
            node_data[node]['lost_percent'] / float(node_data[node]['count'])
            for node in node_data.keys()
        }
        print("node score:{}".format(node_score))

        problematic_nodes = []

        if len(node_score) > 0:
            values = list(node_score.values())
            outliers_index = IpExperiment.get_outliers(values)
            print("outliers_index:{}".format(outliers_index))

            node_keys = list(node_score.keys())
            for i in outliers_index:
                k = node_keys[i]
                score = node_score[k]
                print("problematic host:{} score:{}".format(k, score))
                problematic_nodes.append(k)

        return problematic_nodes


def main():
    print('Starting...')

    targets_l = [
        Target('192.168.1.176', 40000, 4000),
        Target('192.168.1.176', 40001, 4000),
        Target('192.168.1.176', 40002, 4000)
    ]
    print(targets_l)

    ip_exp = IpExperiment(targets_l)
    ip_exp.perform_tracert()

    print("ACTIVATE ACL NOW!")
    timeout = 60
    for i in range(timeout):
        print("{}/{}".format(i, timeout))
        time.sleep(1)

    ip_exp.perform_iperf()
    ip_exp.compute_results()


if __name__ == "__main__":
    main()

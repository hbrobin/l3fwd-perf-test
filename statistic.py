import paramiko
import os
import json
import session
import flowgen
import l3fwd
import time
import nclib
import threading
import paramiko
import re
import locale
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pkg_size_list = ('64', '128', '256', '512', '1024', '1280', '1518')
core_list = ('1','2', '4', '6', '8', '10', '12', '14', '16')
exitFlag = 0


class Statistic:
    def __init__(self, cfg_file):
        with open(cfg_file) as config_file:
            config_list = json.load(config_file)
            self.pktgen_cli = None
            for index in range(len(config_list)):
                server_config = config_list[index]
                if "xmit" == server_config["server_info"]["mode"]:
                    self.config = config_list[index]
        print("Load flowgen configuration file success.")
        self.m = session.DirectSession(self.config['server_info']['host_name'], self.config['server_info']['host_port'], self.config['server_info']['username'],
                                  self.config['server_info']['password'])
        statistic_src_path = self.config["path"]["repo_path"] + (self.config["pkg_list"])["eth_stat"]
        statistic_dst_path = self.config["path"]["tool_path"]
        self.m.sshclient_execmd("mkdir -p " + statistic_dst_path + ";"
                                "cp " + statistic_src_path + " " + statistic_dst_path + ";"
                                "chmod +rx " + statistic_dst_path + (self.config["pkg_list"])["eth_stat"])
        self.df = pd.DataFrame(np.zeros(len(pkg_size_list) * len(core_list)).reshape(len(pkg_size_list), len(core_list)),
                          index=pkg_size_list, columns=core_list)

    def start_statistic(self, core_num, pkt_len):
        global exitFlag
        exitFlag = 0
        threadList = ["PPS-Collection-Thread"]
        # nameList = ["One", "Two", "Three", "Four", "Five"]
        # queueLock = threading.Lock()
        # workQueue = Queue.Queue(10)
        threads = []
        threadID = 1

        # create new thread
        for tName in threadList:
            self.pps_thread = ppsThread(self, threadID, tName, core_num, pkt_len)
            self.pps_thread.start()
            threads.append(self.pps_thread)
            threadID += 1

    def stop_statistic(self):
        global exitFlag
        exitFlag = 1
        self.pps_thread.terminate()
        self.pps_thread.join()

    def save_to_csv(self, file_name):
        abs_path = self.config["path"]["report_path"]
        type = self.config["server_info"]["dut_type"]
        self.df.to_csv(abs_path + type + "_" + file_name + ".csv", index=True, sep=',')


class ppsThread(threading.Thread):
    def __init__(self, statistic, threadID, name, core_num, pkt_len):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.statistic = statistic
        self.core_num = core_num
        self.pkt_len = str(pkt_len)
        # self.q = q

    def run(self):
        print("Starting " + self.name)
        self.collect_data()
        print("Exiting " + self.name)

    def terminate(self):
        pkill_cmd = "pkill eth_stat.sh"
        self.statistic.m.execute(pkill_cmd)
        print("terminate " + self.name)

    def collect_data(self):
        tx_pps_seq = []
        rx_pps_seq = []

        locale.setlocale(locale.LC_NUMERIC, 'English_US')

        print("exitFlag = %d, %s processing..." % (exitFlag, self.name))
        statistic_dst_path = self.statistic.config["path"]["tool_path"]
        cmd = statistic_dst_path + self.statistic.config["pkg_list"]["eth_stat"]
        print(cmd)
        while not exitFlag:
            try:
                s = paramiko.SSHClient()
                s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                s.connect(hostname=self.statistic.config['server_info']['host_name'], port=self.statistic.config['server_info']['host_port'],
                          username=self.statistic.config['server_info']['username'], password=self.statistic.config['server_info']['password'])
                stdin, stdout, stderr = s.exec_command(cmd)

                for line in stdout:
                    line = line.strip("\n")
                    if 'SUM' in line:
                        # remove redundant space
                        line = re.sub(r"\s{2,}", " ", line)
                        print(line)
                        line_array = line.split(' ')
                        tx_pps_seq.append(locale.atoi(line_array[3]))
                        rx_pps_seq.append(locale.atoi(line_array[6]))
                        print(line_array)
                        print(line_array[3] + " " + line_array[6])
            except Exception as e:
                print("execute command %s error, error message is %s" % (cmd, e))
                return ""
        print(tx_pps_seq)
        avg_tx_pps = average(tx_pps_seq)
        print(avg_tx_pps)
        print(rx_pps_seq)
        avg_rx_pps = average(rx_pps_seq)
        avg_rx_mpps = float(avg_rx_pps / 1000000)
        print("raw: %d, mpps: %f" % (avg_rx_pps, avg_rx_mpps))
        avg_rx_mpps = round(avg_rx_mpps, 2)
        # avg_rx_mpps = round(avg_rx_mpps + 0.001, 2)
        print("round mpps: %.2f" % avg_rx_mpps)
        self.statistic.df[self.core_num][self.pkt_len] = avg_rx_mpps
        # self.statistic.df[self.pkt_len][self.core_num] = avg_rx_pps
        # print(self.core_num + " " + self.pkt_len)


def average(seq):
    return int(sum(seq) / len(seq))
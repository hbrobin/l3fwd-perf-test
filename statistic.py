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
from locale import *
import pandas as pd


# import pexpect

exitFlag = 0

class Statistic:
    def __init__(self, cfg_file):
        with open(cfg_file) as config_file:
            config_list = json.load(config_file)
            self.pktgen_cli = None
            for index in range(len(config_list)):
                server_config = config_list[index]
                if "xmit" == server_config["server_type"]:
                    self.config = config_list[index]
        print("Load flowgen configuration file success.")
        self.m = session.DirectSession(self.config['host_name'], self.config['host_port'], self.config['username'],
                                  self.config['password'])
        statistic_src_path = self.config["repo_path"] + (self.config["pkg_list"])["eth_stat"]
        statistic_dst_path = self.config["tool_path"]
        self.m.sshclient_execmd("mkdir -p " + statistic_dst_path + ";"
                                "cp " + statistic_src_path + " " + statistic_dst_path + ";"
                                "chmod +rx " + statistic_dst_path + (self.config["pkg_list"])["eth_stat"])

    def start_statistic(self):
        threadList = ["PPS-Collection-Thread"]
        # nameList = ["One", "Two", "Three", "Four", "Five"]
        # queueLock = threading.Lock()
        # workQueue = Queue.Queue(10)
        threads = []
        threadID = 1

        # 创建新线程
        for tName in threadList:
            self.pps_thread = ppsThread(self, threadID, tName)
            self.pps_thread.start()
            threads.append(self.pps_thread)
            threadID += 1

    def stop_statistic(self):
        global exitFlag
        exitFlag = 1
        self.pps_thread.terminate()


class ppsThread(threading.Thread):
    def __init__(self, statistic, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.statistic = statistic
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

        setlocale(LC_NUMERIC, 'English_US')

        print("exitFlag = %d, %s processing..." % (exitFlag, self.name))
        statistic_dst_path = self.statistic.config["tool_path"]
        cmd = statistic_dst_path + self.statistic.config["pkg_list"]["eth_stat"]
        print(cmd)
        while not exitFlag:
            try:
                s = paramiko.SSHClient()
                s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                s.connect(hostname=self.statistic.config['host_name'], port=self.statistic.config['host_port'],
                          username=self.statistic.config['username'], password=self.statistic.config['password'])
                stdin, stdout, stderr = s.exec_command(cmd)

                for line in stdout:
                    line = line.strip("\n")
                    if 'SUM' in line:
                        # remove redundant space
                        line = re.sub(r"\s{2,}", " ", line)
                        # print(line)
                        line_array = line.split(' ')
                        tx_pps_seq.append(atoi(line_array[3]))
                        rx_pps_seq.append(atoi(line_array[6]))
                        # print(line_array)
                        # print(line_array[3] + " " + line_array[6])
            except Exception as e:
                print("execute command %s error, error message is %s" % (cmd, e))
                return ""
        print(tx_pps_seq)
        avg_tx = average(tx_pps_seq)
        print(avg_tx)
        print(rx_pps_seq)
        avg_rx = average(rx_pps_seq)
        print(avg_rx)

def average(seq):
    return int(sum(seq) / len(seq))
    # return float(sum(seq)) / len(seq)
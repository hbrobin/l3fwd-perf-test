import paramiko
import os
import json
import session
import flowgen
import l3fwd
import statistic
import time
import nclib

core_list = ('2', '4', '6', '8', '10', '12', '14', '16')
# core_list = ('8')
pkt_len_list = (64, 128, 256, 512, 1024, 1280, 1518)
# pkt_len_list = (64, 128)

class L3Perf:
    def __init__(self, l3_cfg_file):
        with open(l3_cfg_file) as config_file:
            self.config_list = json.load(config_file)
            self.pktgen_cli = None
        print("Load L3 perf configuration file success.")

def upload_install_l3_perf():
    fg = flowgen.PktGen("config.json")
    fg.upload_pkgs()
    fg.install_pkgs()
    l3 = l3fwd.L3Fwd("config.json")
    l3.upload_pkgs()
    l3.install_pkgs()

def run_unidirection_l3_perf():
    try:
        fg = flowgen.PktGen("config.json")
        fg.run_pktgen()
        l3 = l3fwd.L3Fwd("config.json")

        pps = statistic.Statistic("config.json")

        for pkt_len in pkt_len_list:
            for core_num in core_list:
                fg.set_pktgen_range(pkt_len)
                l3.run_l3fwd(core_num)
                fg.start_pktgen('1')
                # waiting to reach max pps
                time.sleep(5)
                pps.start_statistic(core_num, pkt_len)
                # time of testing duration
                time.sleep(30)
                pps.stop_statistic()
                fg.stop_pktgen('1')
                l3.stop_l3fwd()

        fg.quit_pktgen()
        file_name = os.path.splitext(__file__)[0]
        print(file_name)
        file_name_array = file_name.split("\\")
        print(file_name_array)
        print(file_name_array[-1])
        now = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
        file_name = 'unidirection_' + str(file_name_array[-1]) + '_mpps_' + now
        pps.save_to_csv(file_name)
    finally:
        fg.quit_pktgen()
        l3.stop_l3fwd()


def run_bidirection_l3_perf():
    try:
        fg = flowgen.PktGen("config.json")
        fg.run_pktgen()
        l3 = l3fwd.L3Fwd("config.json")

        pps = statistic.Statistic("config.json")

        for pkt_len in pkt_len_list:
            for core_num in core_list:
                fg.set_pktgen_range(pkt_len)
                l3.run_l3fwd(core_num)
                fg.start_pktgen('all')
                # waiting to reach max pps
                time.sleep(5)
                pps.start_statistic(core_num, pkt_len)
                # time of testing duration
                time.sleep(30)
                pps.stop_statistic()
                fg.stop_pktgen('all')
                l3.stop_l3fwd()

        fg.quit_pktgen()
        file_name = os.path.splitext(__file__)[0]
        print(file_name)
        file_name_array = file_name.split("\\")
        print(file_name_array)
        print(file_name_array[-1])
        now = time.strftime('%Y%m%d%H%M',time.localtime(time.time()))
        file_name = 'bidirection_' + str(file_name_array[-1]) + '_mpps_' + now
        pps.save_to_csv(file_name)
    finally:
        fg.quit_pktgen()
        l3.stop_l3fwd()

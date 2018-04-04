import paramiko
import os
import json
import session
import flowgen
import l3fwd
import statistic
import time
import nclib

class L3Perf:
    def __init__(self, l3_cfg_file):
        with open(l3_cfg_file) as config_file:
            self.config_list = json.load(config_file)
            self.pktgen_cli = None
        print("Load L3 perf configuration file success.")

def run_l3_perf():
    core_list = ['2', '4', '6', '8', '10', '12', '14', '16']

    try:
        fg = flowgen.FlowGen("config.json")
        # fg.upload_pkgs()
        # fg.install_pkgs()
        fg.run_pktgen()
        fg.set_pktgen_range(64)

        l3 = l3fwd.L3Fwd("config.json")
        # l3.upload_pkgs()
        # l3.install_pkgs()


        pps = statistic.Statistic("config.json")

        for core_num in core_list:
            l3.run_l3fwd(core_num)
            fg.start_pktgen('1')
            # waiting to reach max pps
            time.sleep(5)
            pps.start_statistic(core_num)
            time.sleep(20)
            pps.stop_statistic()
            fg.stop_pktgen('1')
            l3.stop_l3fwd()
        fg.quit_pktgen()
    finally:
        fg.quit_pktgen()
        l3.stop_l3fwd()




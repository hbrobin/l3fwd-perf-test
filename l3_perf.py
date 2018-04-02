import paramiko
import os
import json
import session
import flowgen
import l3fwd
import time
import nclib
# import pexpect

class L3Perf:
    def __init__(self, l3_cfg_file):
        with open(l3_cfg_file) as config_file:
            self.config_list = json.load(config_file)
            self.pktgen_cli = None
        print("Load L3 perf configuration file success.")

def run_l3_perf():
    fg = flowgen.FlowGen("config.json")
    fg.upload_pkgs()
    fg.install_pkgs()
    fg.run_pktgen()
    fg.set_pktgen_range(64)

    l3 = l3fwd.L3Fwd("config.json")
    l3.upload_pkgs()
    l3.install_pkgs()
    l3.run_l3fwd(1)

    fg.start_pktgen('1')
    time.sleep(30)
    fg.stop_pktgen('1')
    fg.quit_pktgen()
    l3.stop_l3fwd()



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
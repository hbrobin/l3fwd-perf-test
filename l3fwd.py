import paramiko
import os
import json
import session
import flowgen
import time
import nclib
# import pexpect

# 2 queue
_2q_cores_dict = {"2": "-l 24-25 -n 6 -- -p 0x3 --config '(0,0,24),(0,1,24),(1,0,25),(1,1,25)'",
                 "4": "-l 24-27 -n 6 -- -p 0x3 --config '(0,0,24),(0,1,24),(0,2,25),(0,3,25),"
                      "(1,0,26),(1,1,26),(1,2,27),(1,3,27)'",
                 "6": "-l 24-29 -n 6 -- -p 0x3 --config '(0,0,24),(0,1,24),(0,2,25),(0,3,25),(0,4,26),"
                      "(0,5,26),(1,0,27),(1,1,27),(1,2,28),(1,3,28),(1,4,29),(1,5,29)'",
                 "8": "-l 24-31 -n 6 -- -p 0x3 --config '(0,0,24),(0,1,24),(0,2,25),(0,3,25),(0,4,26),"
                      "(0,5,26),(0,6,27),(0,7,27),(1,0,28),(1,1,28),(1,2,29),(1,3,29),(1,4,30),(1,5,30),"
                      "(1,6,31),(1,7,31)'",
                 "10": "-l 24-33 -n 6 -- -p 0x3 --config '(0,0,24),(0,1,24),(0,2,25),(0,3,25),(0,4,26),"
                      "(0,5,26),(0,6,27),(0,7,27),(0,8,28),(0,9,28),(1,0,29),(1,1,29),(1,2,30),(1,3,30),"
                      "(1,4,31),(1,5,31),(1,6,32),(1,7,32),(1,8,33),(1,9,33)'",
                 "12": "-l 24-35 -n 6 -- -p 0x3 --config '(0,0,24),(0,1,24),(0,2,25),(0,3,25),(0,4,26),"
                      "(0,5,26),(0,6,27),(0,7,27),(0,8,28),(0,9,28),(0,10,29),(0,11,29),(1,0,30),(1,1,30),"
                      "(1,2,31),(1,3,31),(1,4,32),(1,5,32),(1,6,33),(1,7,33),(1,8,34),(1,9,34),(1,10,35),(1,11,35)'",
                 "14": "-l 24-37 -n 6 -- -p 0x3 --config '(0,0,24),(0,1,24),(0,2,25),(0,3,25),(0,4,26),"
                      "(0,5,26),(0,6,27),(0,7,27),(0,8,28),(0,9,28),(0,10,29),(0,11,29),(0,12,30),(0,13,30),"
                      "(1,0,31),(1,1,31),(1,2,32),(1,3,32),(1,4,33),(1,5,33),(1,6,34),(1,7,34),(1,8,35),(1,9,35),"
                      "(1,10,36),(1,11,36),(1,12,37),(1,13,37)'",
                 "16": "-l 24-39 -n 6 -- -p 0x3 --config '(0,0,24),(0,1,24),(0,2,25),(0,3,25),(0,4,26),"
                      "(0,5,26),(0,6,27),(0,7,27),(0,8,28),(0,9,28),(0,10,29),(0,11,29),(0,12,30),(0,13,30),"
                      "(0,14,31),(0,15,31),(1,0,32),(1,1,32),(1,2,33),(1,3,33),(1,4,34),(1,5,34),(1,6,35),(1,7,35),"
                      "(1,8,36),(1,9,36),(1,10,37),(1,11,37),(1,12,38),(1,13,38),(1,14,39),(1,15,39)'"}


class L3Fwd:
    def __init__(self, cfg_file):
        with open(cfg_file) as config_file:
            config_list = json.load(config_file)
            self.shell_cli = None
            for index in range(len(config_list)):
                server_config = config_list[index]
                if "forward" == server_config["server_type"]:
                    self.config = config_list[index]
        print("Load l3fwd configuration file success.")

    def upload_pkgs(self):
        m = session.DirectSession(self.config['host_name'], self.config['host_port'], self.config['username'],
                                  self.config['password'])
        m.sync_sw_repo(self.config)

    def install_pkgs(self):
        m = session.DirectSession(self.config['host_name'], self.config['host_port'], self.config['username'],
                                  self.config['password'])

        # create sw installation folders
        dpdk_dst_path = self.config["dpdk_path"]
        mnlx_dst_path = self.config["mnlx_path"]
        m.sshclient_execmd("mkdir -p " + dpdk_dst_path)
        m.sshclient_execmd("mkdir -p " + mnlx_dst_path)
        dpdk_src_path = self.config["repo_path"] + (self.config["pkg_list"])["dpdk_pkg"]
        mnlx_src_path = self.config["repo_path"] + (self.config["pkg_list"])["ofed_pkg"]

        # extract packages
        m.sshclient_execmd("tar -zxf " + dpdk_src_path + " -C " + dpdk_dst_path)
        m.sshclient_execmd("tar -zxf " + mnlx_src_path + " -C " + mnlx_dst_path)

        # install mnlx_ofed 4.3
        ofed_ver = None
        ofed_ver = m.sshclient_execmd("ofed_info -s")
        ofed_ver = str(ofed_ver, encoding="utf-8")
        #print("ofed_ver:"+ofed_ver)
        ofed_v43 = "MLNX_OFED_LINUX-4.3"
        #print("ofed_v43:" + ofed_v43)
        if ofed_v43 not in ofed_ver:
            print("Begin install OFED in " + self.config["server_type"] + " server.")
            mnlx_dst_path = self.config["mnlx_path"]+(self.config["pkg_list"])["ofed_pkg"]
            mnlx_dst_path = mnlx_dst_path.rsplit('.', 1)[0]
            print(mnlx_dst_path)
            m.sshclient_execmd(mnlx_dst_path + "/mlnxofedinstall --dpdk --with-mlnx-ethtool --with-mft --with-mstflint --add-kernel-support --upstream-libs")
        else:
            print("Already installed OFED in " + self.config["server_type"] + " server.")

        # compile dpdk package
        dpdk_dst_path = self.config["dpdk_path"]+(self.config["pkg_list"])["dpdk_pkg"]
        dpdk_dst_path = dpdk_dst_path.rsplit('.', 2)[0]
        print(dpdk_dst_path)
        m.sshclient_execmd("cd " + dpdk_dst_path + ";"
                            "export RTE_TARGET=" + self.config["rte_target"] + ";"
                            "make config T=${RTE_TARGET};"
                            r"sed -ri 's,(LIBRTE_MLX5_PMD=).*,\1y,' build/.config;"
                            "make -j24;"
                            r"sed -i 's/\(CONFIG_RTE_LIBRTE_MLX5_PMD=\)n/\1y/g' config/common_base;"
                            "make -j24 install T=${RTE_TARGET}")

        # patch l3fwd
        if 'l3fwd_patch' in self.config["pkg_list"]:
            # step 1: cp patch for l3fwd
            l3fwd_patch_path = self.config["repo_path"] + (self.config["pkg_list"])["l3fwd_patch"]
            dpdk_examples_path = dpdk_dst_path + "/examples/"
            m.sshclient_execmd("cp " + l3fwd_patch_path + " " + dpdk_examples_path)
            # step 2 patch patch file
            m.sshclient_execmd("cd " + dpdk_examples_path + ";" +
                            "patch -p1 < " + (self.config["pkg_list"])["l3fwd_patch"])

        # compile l3fwd
        dpdk_dst_path = self.config["dpdk_path"] + (self.config["pkg_list"])["dpdk_pkg"]
        dpdk_dst_path = dpdk_dst_path.rsplit('.', 2)[0]
        print(dpdk_dst_path)
        m.sshclient_execmd("cd " + dpdk_dst_path + ";"
                            "export RTE_TARGET=" + self.config["rte_target"] + ";"
                            "export RTE_SDK=" + dpdk_dst_path + ";"
                            "make -C " + self.config["l3fwd_sub_path"])

    # core_num: core number of each forwarding direction
    def run_l3fwd(self, core_num):
        print("Starting l3fwd...")
        m = session.DirectSession(self.config['host_name'], self.config['host_port'],
                                  self.config['username'], self.config['password'])
        l3fwd_path = (self.config["dpdk_path"] + (self.config["pkg_list"])["dpdk_pkg"]).rsplit('.', 2)[0]
        l3fwd_bin_name = 'l3fwd'
        print("l3fwd_path: " + l3fwd_path + ", l3fwd_bin_name: " + l3fwd_bin_name)
        # ssh = paramiko.SSHClient()
        # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # ssh.connect(hostname=server_config['host_name'], port=server_config['host_port'], username=server_config['username'], password=server_config['password'])
        # channel = ssh.invoke_shell()

        # self.pktgen_cli = session.PktgenSession(server_config['host_name'], server_config['host_port'],
        #                            server_config['username'], server_config['password'])
        execmd = "cd " + l3fwd_path + '/' + self.config["l3fwd_sub_path"] + "/build;" \
                 "export RTE_TARGET=" + self.config["rte_target"] + ";" \
                 "export RTE_SDK=" + l3fwd_path + ";" + \
                 "nohup ./" + l3fwd_bin_name + ' ' + \
                 _2q_cores_dict[core_num] + \
                 " --parse-ptype &"
        print(execmd)
        self.shell_cli = session.ShellSession(self.config['host_name'], self.config['host_port'],
                                                self.config['username'], self.config['password'])
        # output = self.pktgen_cli.execute(execmd)
        # output = m.ShellSession(execmd)
        output = self.shell_cli.execute(execmd)
        print(output)
        #output_str = str(output, encoding="utf-8")

    def stop_l3fwd(self):
        print("Stopping l3fwd...")
        execmd = "pkill l3fwd"
        print(execmd)
        self.shell_cli = session.ShellSession(self.config['host_name'], self.config['host_port'],
                                                self.config['username'], self.config['password'])
        # output = self.pktgen_cli.execute(execmd)
        # output = m.ShellSession(execmd)
        output = self.shell_cli.execute(execmd)
        print(output)
        #output_str = str(output, encoding="utf-8")
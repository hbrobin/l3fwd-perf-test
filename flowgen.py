import paramiko
import os
import json
import session
import time
import nclib
# import pexpect


class PktGen:
    def __init__(self, cfg_file):
        with open(cfg_file) as config_file:
            config_list = json.load(config_file)
            self.pktgen_cli = None
            for index in range(len(config_list)):
                server_config = config_list[index]
                if "xmit" == server_config["server_info"]["mode"]:
                    self.config = config_list[index]
        print("Load flowgen configuration file success.")

    def upload_pkgs(self):
        m = session.DirectSession(self.config['server_info']['host_name'], self.config['server_info']['host_port'], self.config['server_info']['username'],
                                  self.config['server_info']['password'])
        m.sync_sw_repo(self.config)

    def install_pkgs(self):
        m = session.DirectSession(self.config['server_info']['host_name'], self.config['server_info']['host_port'], self.config['server_info']['username'],
                                  self.config['server_info']['password'])

        # create sw installation folders
        dpdk_dst_path = self.config["path"]["dpdk_path"]
        mnlx_dst_path = self.config["path"]["mnlx_path"]
        m.sshclient_execmd("mkdir -p " + dpdk_dst_path)
        m.sshclient_execmd("mkdir -p " + mnlx_dst_path)
        dpdk_src_path = self.config["path"]["repo_path"] + (self.config["pkg_list"])["dpdk_pkg"]
        mnlx_src_path = self.config["path"]["repo_path"] + (self.config["pkg_list"])["ofed_pkg"]
        pktgen_src_path = self.config["path"]["repo_path"] + (self.config["pkg_list"])["pktgen_pkg"]

        # extract packages
        m.sshclient_execmd("tar -zxf " + dpdk_src_path + " -C " + dpdk_dst_path)
        m.sshclient_execmd("tar -zxf " + mnlx_src_path + " -C " + mnlx_dst_path)
        if "xmit" == self.config["server_info"]["mode"]:
            m.sshclient_execmd("tar -zxf " + pktgen_src_path + " -C " + dpdk_dst_path)

        # install mnlx_ofed 4.3
        ofed_ver = None
        ofed_ver = m.sshclient_execmd("ofed_info -s")
        ofed_ver = str(ofed_ver, encoding="utf-8")
        #print("ofed_ver:"+ofed_ver)
        ofed_v43 = "MLNX_OFED_LINUX-4.3"
        #print("ofed_v43:" + ofed_v43)
        if ofed_v43 not in ofed_ver:
            print("Begin install OFED in " + self.config["server_info"]["mode"] + " server.")
            mnlx_dst_path = self.config["path"]["mnlx_path"]+(self.config["pkg_list"])["ofed_pkg"]
            mnlx_dst_path = mnlx_dst_path.rsplit('.', 1)[0]
            print(mnlx_dst_path)
            m.sshclient_execmd(mnlx_dst_path + "/mlnxofedinstall --dpdk --with-mlnx-ethtool --with-mft --with-mstflint --add-kernel-support --upstream-libs")
        else:
            print("Already installed OFED in " + self.config["server_info"]["mode"] + " server.")

                #m.sshclient_execmd("tar -zxf " + pktgen_src_path + " -C " + dpdk_dst_path)

        # compile dpdk package
        dpdk_dst_path = self.config["path"]["dpdk_path"]+(self.config["pkg_list"])["dpdk_pkg"]
        dpdk_dst_path = dpdk_dst_path.rsplit('.', 2)[0]
        print(dpdk_dst_path)
        m.sshclient_execmd("cd " + dpdk_dst_path + ";"
                            "export RTE_TARGET=" + self.config["server_info"]["rte_target"] + ";"
                            "make config T=${RTE_TARGET};"
                            r"sed -ri 's,(LIBRTE_MLX5_PMD=).*,\1y,' build/.config;"
                            "make -j24;"
                            r"sed -i 's/\(CONFIG_RTE_LIBRTE_MLX5_PMD=\)n/\1y/g' config/common_base;"
                            "make -j24 install T=${RTE_TARGET}")

        # compile pktgen package
        pktgen_dst_path = self.config["path"]["dpdk_path"] + (self.config["pkg_list"])["pktgen_pkg"]
        pktgen_dst_path = pktgen_dst_path.rsplit('.', 2)[0]
        print(pktgen_dst_path)
        if 'pktgen_patch' in self.config["pkg_list"]:
            # step 1: cp patch for pktgen
            pktgen_patch_path = self.config["path"]["repo_path"] + (self.config["pkg_list"])["pktgen_patch"]
            m.sshclient_execmd("cp " + pktgen_patch_path + " " + pktgen_dst_path)
            # step 2 patch patch file
            m.sshclient_execmd("cd " + pktgen_dst_path + ";" +
                            "patch -p1 < " + (self.config["pkg_list"])["pktgen_patch"])
        # step 3 compile
        m.sshclient_execmd("cd " + pktgen_dst_path + ";"
                           "export RTE_TARGET=" + self.config["server_info"]["rte_target"] + ";"
                           "export RTE_SDK=" + dpdk_dst_path + ";"
                           "make -j 24")

    def run_pktgen(self):
        print("Enable socket port 22022 on firewall...")
        m = session.DirectSession(self.config['server_info']['host_name'], self.config['server_info']['host_port'],
                                  self.config['server_info']['username'], self.config['server_info']['password'])
        m.sshclient_execmd("firewall-cmd --zone=public --add-port=22022/tcp --permanent")
        m.sshclient_execmd("firewall-cmd --reload")
        print("Set NIC to 40G mode...")
        mnlx_nics = m.sshclient_execmd("mst status -v | awk '/ConnectX/ { print $5 }'")
        print(mnlx_nics)
        # mnlx_nics_str = str(mnlx_nics)
        mnlx_nics_str = mnlx_nics.decode("utf-8")
        print(mnlx_nics_str)
        mnlx_nics = mnlx_nics_str.split("\n")
        print(mnlx_nics)
        while '' in mnlx_nics:
            mnlx_nics.remove('')
        for mnlx_nic in mnlx_nics:
            print(mnlx_nic)
            mnlx_nic_array = mnlx_nic.split('-')
            print("Set mnlx_nic: %s" % mnlx_nic_array[1])
            m.sshclient_execmd("ethtool -s " + mnlx_nic_array[1] + " speed 40000 duplex full autoneg off")
        print("Starting pktgen...")
        # m = session.DirectSession(server_config['server_info']['host_name'], server_config['server_info']['host_port'],
        #                           server_config['server_info']['username'], server_config['server_info']['password'])
        # server_config = self.config_list[index]
        pktgen_path = (self.config["path"]["dpdk_path"] + (self.config["pkg_list"])["pktgen_pkg"]).rsplit('.', 2)[0]
        pktgen_bin_name = (self.config["pkg_list"])["pktgen_pkg"].rsplit('-', 1)[0]
        print("pktgen_path: " + pktgen_path + ", pktgen_bin_name: " + pktgen_bin_name)
        # ssh = paramiko.SSHClient()
        # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # ssh.connect(hostname=server_config['server_info']['host_name'], port=server_config['server_info']['host_port'], username=server_config['server_info']['username'], password=server_config['server_info']['password'])
        # channel = ssh.invoke_shell()

        self.pktgen_cli = session.PktgenSession(self.config['server_info']['host_name'], self.config['server_info']['host_port'],
                                                self.config['server_info']['username'], self.config['server_info']['password'])
        execmd = "cd " + pktgen_path + ";" + "app/" + self.config["server_info"]["rte_target"] + "/" + pktgen_bin_name + " " + \
                 "-l 1-35 -n 6 -w 0000:01:00.0 -w 0004:01:00.0 --file-prefix pktgen_ -- -G -P --crc-strip -m [2:22-28].0 -m [3:29-33].1 -f themes/white-black.theme"
        print(execmd)
        output = self.pktgen_cli.execute(execmd)
        print(output)
        #output_str = str(output, encoding="utf-8")

    def set_pktgen_range(self, pkt_len):
        logfile = open('log.txt', 'wb')
        pkt_len_str = 'pktgen_range_' + str(pkt_len) + 'B'
        if "vm" == self.config["server_info"]["dut_type"]:
            pktgen_cfg = self.config["path"]["local_cfg_path"] + (self.config["cfg_list_vm"])[pkt_len_str]
        else:
            pktgen_cfg = self.config["path"]["local_cfg_path"] + (self.config["cfg_list_host"])[pkt_len_str]
        lua_fd = open(pktgen_cfg, 'r')
        # lua_fd = open('/root/DPDK/L3_Xmit/config/test_range.lua', 'r')
        lua_range_str = lua_fd.read()
        lua_range_b = bytes(lua_range_str, encoding="utf8")
        nc = nclib.Netcat((self.config["server_info"]["host_name"], self.config["pktgen_port"]), verbose=True, log_send=logfile, log_recv=logfile)
        nc.echo_hex = True
        # nc.send(b'\x00\x0dpktgen.start("all");')
        nc.send(lua_range_b)
        nc.close()

    def wait_test_period(self):
        t = self.config["test_period_sec"]
        time.sleep(t)

    def start_pktgen(self, port):
        logfile = open('log.txt', 'wb')
        nc = nclib.Netcat((self.config["server_info"]["host_name"], self.config["pktgen_port"]), verbose=True,
                           log_send=logfile, log_recv=logfile)
        nc.echo_hex = True
        cmd_str = 'pktgen.start("' + port + '");\n'
        cmd_b = bytes(cmd_str, encoding="utf8")
        nc.send(cmd_b)
        nc.close()

    def stop_pktgen(self, port):
        logfile = open('log.txt', 'wb')
        nc = nclib.Netcat((self.config["server_info"]["host_name"], self.config["pktgen_port"]), verbose=True,
                           log_send=logfile, log_recv=logfile)
        nc.echo_hex = True
        cmd_str = 'pktgen.stop("' + port + '");\n'
        cmd_b = bytes(cmd_str, encoding="utf8")
        nc.send(cmd_b)
        nc.close()

    def quit_pktgen(self):
        quit_cmd = 'quit'
        output = self.pktgen_cli.execute(quit_cmd)
        print(output)

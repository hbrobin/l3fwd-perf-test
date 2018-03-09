import paramiko
import os
import json
import session
# import pexpect

class L3Perf:
    def __init__(self, l3_cfg_file):
        with open(l3_cfg_file) as config_file:
            self.config_list = json.load(config_file)
        print("Load L3 perf configuration file success.")

    def upload_pkgs(self, config_list):
        for index in range(len(config_list)):
            server_config = config_list[index]
            m = session.DirectSession(server_config['host_name'], server_config['host_port'], server_config['username'],
                              server_config['password'])
            m.sync_sw_repo(server_config)

    def install_pkgs(self, config_list):
        for index in range(len(config_list)):
            server_config = config_list[index]
            m = session.DirectSession(server_config['host_name'], server_config['host_port'], server_config['username'],
                              server_config['password'])

            # create sw installation folders
            dpdk_dst_path = server_config["dpdk_path"]
            mnlx_dst_path = server_config["mnlx_path"]
            m.sshclient_execmd("mkdir -p " + dpdk_dst_path)
            m.sshclient_execmd("mkdir -p " + mnlx_dst_path)
            dpdk_src_path = server_config["repo_path"] + (server_config["file_list"])["dpdk_pkg"]
            mnlx_src_path = server_config["repo_path"] + (server_config["file_list"])["ofed_pkg"]
            pktgen_src_path = server_config["repo_path"] + (server_config["file_list"])["pktgen_pkg"]

            # extract packages
            m.sshclient_execmd("tar -zxf " + dpdk_src_path + " -C " + dpdk_dst_path)
            m.sshclient_execmd("tar -zxf " + mnlx_src_path + " -C " + mnlx_dst_path)
            if "xmit" == server_config["server_type"]:
                m.sshclient_execmd("tar -zxf " + pktgen_src_path + " -C " + dpdk_dst_path)

            # install mnlx_ofed 4.3
            ofed_ver = None
            ofed_ver = m.sshclient_execmd("ofed_info -s")
            ofed_ver = str(ofed_ver, encoding="utf-8")
            #print("ofed_ver:"+ofed_ver)
            ofed_v43 = "MLNX_OFED_LINUX-4.3"
            #print("ofed_v43:" + ofed_v43)
            if ofed_v43 not in ofed_ver:
                print("Begin install OFED in " + server_config["server_type"] + " server.")
                mnlx_dst_path = server_config["mnlx_path"]+(server_config["file_list"])["ofed_pkg"]
                mnlx_dst_path = mnlx_dst_path.rsplit('.', 1)[0]
                print(mnlx_dst_path)
                m.sshclient_execmd(mnlx_dst_path + "/mlnxofedinstall --dpdk --with-mlnx-ethtool --with-mft --with-mstflint --add-kernel-support --upstream-libs")
            else:
                print("Already installed OFED in " + server_config["server_type"] + " server.")

                #m.sshclient_execmd("tar -zxf " + pktgen_src_path + " -C " + dpdk_dst_path)

            # compile dpdk package
            dpdk_dst_path = server_config["dpdk_path"]+(server_config["file_list"])["dpdk_pkg"]
            dpdk_dst_path = dpdk_dst_path.rsplit('.', 2)[0]
            print(dpdk_dst_path)
            m.sshclient_execmd("cd " + dpdk_dst_path + ";"
                               "export RTE_TARGET=arm64-armv8a-linuxapp-gcc;"
                               "make config T=${RTE_TARGET};"
                               r"sed -ri 's,(LIBRTE_MLX5_PMD=).*,\1y,' build/.config;"
                               "make -j24;"
                               r"sed -i 's/\(CONFIG_RTE_LIBRTE_MLX5_PMD=\)n/\1y/g' config/common_base;"
                               "make -j24 install T=${RTE_TARGET}")

            if "xmit" == server_config["server_type"]:
                # compile pktgen package
                pktgen_dst_path = server_config["dpdk_path"] + (server_config["file_list"])["pktgen_pkg"]
                pktgen_dst_path = pktgen_dst_path.rsplit('.', 2)[0]
                print(pktgen_dst_path)
                # step 1: cp patch for pktgen 3.4.5
                pktgen_patch_path = server_config["repo_path"] + (server_config["file_list"])["pktgen_patch"]
                m.sshclient_execmd("cp " + pktgen_patch_path + " " + pktgen_dst_path)
                # step 2 patch patch file
                m.sshclient_execmd("cd " + pktgen_dst_path + ";" +
                                   "patch -p1 < " + (server_config["file_list"])["pktgen_patch"])
                # step 3 compile
                m.sshclient_execmd("cd " + pktgen_dst_path + ";"
                                  "export RTE_TARGET=arm64-armv8a-linuxapp-gcc;"
                                  "export RTE_SDK=" + dpdk_dst_path + ";"
                                  "make -j 24")

    def run_l3fwd(self, config_list):
        print("Start forwarder.")

    def run_pktgen(self, config_list):
        for index in range(len(config_list)):
            server_config = config_list[index]
            if "xmit" == server_config["server_type"]:
                print("Starting pktgen...")
                # m = session.DirectSession(server_config['host_name'], server_config['host_port'],
                #                           server_config['username'], server_config['password'])
                server_config = config_list[index]
                pktgen_path = (server_config["dpdk_path"] + (server_config["file_list"])["pktgen_pkg"]).rsplit('.', 2)[0]
                pktgen_bin_name = (server_config["file_list"])["pktgen_pkg"].rsplit('-', 1)[0]
                print("pktgen_path: " + pktgen_path + ", pktgen_bin_name: " + pktgen_bin_name)
                # ssh = paramiko.SSHClient()
                # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                # ssh.connect(hostname=server_config['host_name'], port=server_config['host_port'], username=server_config['username'], password=server_config['password'])
                # channel = ssh.invoke_shell()

                sh = session.ShellSession(server_config['host_name'], server_config['host_port'],
                                           server_config['username'], server_config['password'])
                execmd = "cd " + pktgen_path + ";" + "app/" + server_config["rte_target"] + "/" + pktgen_bin_name + " " + \
                                            "-l 3-43 -n 6 -w 0000:01:00.0 -w 0003:01:00.0 -- -G -P --crc-strip -m [4:14-23].0 -m [24:34-43].1 -f themes/white-black.theme"
                print(execmd)
                output = sh.execute(execmd)
                #output_str = str(output, encoding="utf-8")
                print(output)



def run_l3_perf():
    l3_m = L3Perf("config.json")
    # l3_m.upload_pkgs(l3_m.config_list)
    # l3_m.install_pkgs(l3_m.config_list)
    l3_m.run_pktgen(l3_m.config_list)
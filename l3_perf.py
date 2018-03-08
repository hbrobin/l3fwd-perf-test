import paramiko
import os
import json
import session

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



def run_l3_perf():
    l3_m = L3Perf("config.json")
    l3_m.upload_pkgs(l3_m.config_list)
    l3_m.install_pkgs(l3_m.config_list)
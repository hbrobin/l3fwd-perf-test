import session
import l3_perf

def main():
    # hostname = '10.64.16.21'
    # port = 22
    # username = 'root'
    # password = 'toor4hxt'
    # execmd = "ofed_info -s"
    #
    # execmd21 = session.DirectSession(hostname, port, username, password)
    # ver = execmd21.sshclient_execmd(execmd)
    # print(ver)
    # ver_str = str(ver, encoding="utf-8")
    # print(ver_str)
    # ver_ok = "MLNX_OFED_LINUX-4.4"
    # result = ver_ok in ver_str
    # print(result) `

    l3_perf.upload_install_l3_perf()
    l3_perf.run_unidirection_l3_perf()
    l3_perf.run_bidirection_l3_perf()

if __name__ == "__main__":
    main()

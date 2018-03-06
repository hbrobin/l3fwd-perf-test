import session

def main():
    hostname = '10.64.16.21'
    port = 22
    username = 'root'
    password = 'root'
    execmd = "ofed_info -s"

    execmd21 = session.DirectSession(hostname, port, username, password)
    execmd21.sshclient_execmd(execmd)

    #sync21 = session.DirectSession(hostname, port, username, password)
    #execmd21.sync_sw_repo("config.json")
    session.upload_files("config.json")

if __name__ == "__main__":
    main()

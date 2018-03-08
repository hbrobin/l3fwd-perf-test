import json
import paramiko
import os



def list_file(file_path):
    return [file for file in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, file))]


class DirectSession:
    def __init__(self, ip, port, username, password):
        self.hostname = ip
        self.port = port
        self.username = username
        self.password = password

    def sshclient_execmd(self, execmd):
        paramiko.util.log_to_file("paramiko.log")

        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        s.connect(hostname=self.hostname, port=self.port, username=self.username, password=self.password)
        stdin, stdout, stderr = s.exec_command(execmd)
        stdin.write("Y")  # Generally speaking, the first connection, need a simple interaction.

        #print(stdout.read())
        str = stdout.read()
        s.close()

        print(str)

        return str

    def sync_sw_repo(self, cfg_dict):
        paramiko.util.log_to_file("paramiko_syncfile.log")

        try:
            transport = paramiko.Transport(self.hostname, self.port)
            transport.connect(username=self.username, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            print("Connect remote server success.")
            print("******************************* Synchronize Files -- Start")
            #for path in path_config:
            local_path = cfg_dict["local_path"]
            repo_path = cfg_dict["repo_path"]
            create_path_cmd = "mkdir -p "+repo_path
            self.sshclient_execmd(create_path_cmd)
            print(">>>>>>>>>>>>>>> Traverse local files -- Start")
            filenames = tuple(cfg_dict["file_list"].values())
            print(filenames)
            print(">>>>>>>>>>>>>>> Traverse local files -- Done")
            sync_file_count = 0
            for filename in filenames:
                sftp.put(local_path + filename, repo_path + filename)
                print("Sync local files: \"" + local_path + filename + "\"  to server path:\"" + repo_path + filename + "\"")
                sync_file_count += 1
            print("******************************* Synchronize " + str(sync_file_count) + " Files -- Done")
        finally:
            transport.close()
            sftp.close()

def upload_files(cfg_file):
    with open(cfg_file) as config_file:
        config_list = json.load(config_file)
    print("Load configuration file success.")
    for index in range(len(config_list)):
        server_config = config_list[index]
        m = DirectSession(server_config['host_name'], server_config['host_port'], server_config['username'], server_config['password'])
        m.sync_sw_repo(server_config)

    print("Load configuration file success.")
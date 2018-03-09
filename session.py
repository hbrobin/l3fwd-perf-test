import json
import paramiko
import os
import re



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

class ShellSession:
    def __init__(self, host, port, user, psw):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=user, password=psw, port=port)

        channel = self.ssh.invoke_shell()
        self.stdin = channel.makefile('wb')
        self.stdout = channel.makefile('r')

    def __del__(self):
        self.ssh.close()

    def execute(self, cmd):
        """

        :param cmd: the command to be executed on the remote computer
        :examples:  execute('ls')
                    execute('finger')
                    execute('cd folder_name')
        """
        cmd = cmd.strip('\n')
        self.stdin.write(cmd + '\n')
        finish = 'end of stdOUT buffer. finished with exit status'
        echo_cmd = 'echo {} $?'.format(finish)
        self.stdin.write(echo_cmd + '\n')
        shin = self.stdin
        self.stdin.flush()

        shout = []
        sherr = []
        exit_status = 0
        for line in self.stdout:
            if str(line).startswith(cmd) or str(line).startswith(echo_cmd):
                # up for now filled with shell junk from stdin
                shout = []
            # elif str(line).startswith(finish):
            #     # our finish command ends with the exit status
            #     exit_status = int(str(line).rsplit(maxsplit=1)[1])
            #     if exit_status:
            #         # stderr is combined with stdout.
            #         # thus, swap sherr with shout in a case of failure.
            #         sherr = shout
            #         shout = []
            #     break
            # else:
            #     # get rid of 'coloring and formatting' special characters
            #     shout.append(re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('', line).
            #                  replace('\b', '').replace('\r', ''))

        # first and last lines of shout/sherr contain a prompt
        if shout and echo_cmd in shout[-1]:
            shout.pop()
        if shout and cmd in shout[0]:
            shout.pop(0)
        if sherr and echo_cmd in sherr[-1]:
            sherr.pop()
        if sherr and cmd in sherr[0]:
            sherr.pop(0)

        return shin, shout, sherr

def upload_files(cfg_file):
    with open(cfg_file) as config_file:
        config_list = json.load(config_file)
    print("Load configuration file success.")
    for index in range(len(config_list)):
        server_config = config_list[index]
        m = DirectSession(server_config['host_name'], server_config['host_port'], server_config['username'], server_config['password'])
        m.sync_sw_repo(server_config)

    print("Load configuration file success.")
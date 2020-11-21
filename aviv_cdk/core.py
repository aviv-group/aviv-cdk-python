import os
import subprocess

def __auto_github():
    dirp =  os.path.dirname(os.path.dirname(__file__))
    # os.chdir(dirp)

    # output = subprocess.check_output("pwd; ls -la", shell=True)
    # print(output)
    repo_dir = subprocess.Popen(['git', 'rev-parse', '--show-toplevel'], stdout=subprocess.PIPE).communicate()  #[0].rstrip()
    print(str(repo_dir[0].decode('UTF-8')))

    output = subprocess.check_output("git name-rev --name-only HEAD", shell=True)

    print("got: {}".format(output))

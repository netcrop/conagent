# Conagent
Conagent is a Openssh key managment script, written in Bash/Python3.

  Create, distribute and manage Openssh keys across virtual machines and dockers.
## Install, maintain and uninstall

* For linux/unix system:  
```
required commands and packages:
Bash version 4.4+
Python 3+
gnupg 2.2+
coreutils
openssh
sudo
```
## Using conagent
```
> cd conagent/
> source conagent.sh
> agent.py.install 
# Create new key and save in backup dir
> conagent.genkey backupdir/
> conagent.changepass backupdir/eva_node_rsa_20190208091201
# Add all keys inside ~/.ssh/ to ssh-agent cache
# And export SSH_AGENT_PID SSH_AUTH_SOCK to current interactive shell session
> conagent.addkey
# Send public key to remote host and append to ~/.ssh/authorized_keys  
> conagent.sendkey sample/eva_node_rsa_20190208091201.pub [hostname]
# Establish localhost:socket and remote-host:socket
> conagent.socks [hostname] opt: [remote port] [remote user] [local port] 
```
## For developers
```
# Enable debugging flag
> agent.py.install 1
```
## Reporting a bug and security issues

github.com/netcrop/conagent/pulls

## License

[GNU General Public License version 2 (GPLv2)](https://github.com/netcrop/conagent/blob/master/LICENSE)

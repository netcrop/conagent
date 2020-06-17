# Conagent
Conagent is a Openssh key managment script, written in Bash/Python3.

  It can be used to create and distribute Openssh keys across virtual machines.
## Install, maintain and uninstall

* For linux/unix system:  
```
required commands and packages:
Bash version 4.4+
Python 3.8+
coreutils
openssh
sudo
gnupg
```
## Using conagent
```
node1@eva > cd conagent/
node1@eva > source conagent.sh
node1@eva > conagent.genkey sample/ ${USER} ${HOSTNAME} rsa 1
node1@eva > conagent.changepass sample/eva_node1_rsa_20190208091201 1
node1@eva > conagent.addkey
node1@eva > conagent.sendkey sample/eva_node1_rsa_20190208091201 node2
```
## For developers

We use rolling releases.

## Reporting a bug and security issues

github.com/netcrop/conagent/pulls

## License

[GNU General Public License version 2 (GPLv2)](https://github.com/netcrop/conagent/blob/master/LICENSE)

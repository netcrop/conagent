# Conagent
Conagent is a Openssh key managment script, written in Bash/SHELL.

  It can be used to create and distribute Openssh keys across virtual machines.
## Install, maintain and uninstall

* For linux/unix system:  
```
required commands and packages:
Bash version 4.4+
coreutils
openssh
sudo
openpgp

## Recommended usage.
Add
source conagent/conagent.sh
inside ~/.bashrc

node1@eva > cd conagent/
node1@eva > conagent.genkey sample/ ${USER} ${HOSTNAME} rsa 1
node1@eva > conagent.changepass sample/eva_node1_rsa_20190208091201 1
node1@eva > conagent.addkey
node1@eva > conagent.sendkey sample/eva_node1_rsa_20190208091201 node2
```
## For developers

We use rolling releases.

## Reporting a bug and security issues

github.com/netcrop/conagent/issues

## License

[GNU General Public License version 2 (GPLv2)](https://github.com/netcrop/conagent/blob/master/LICENSE)

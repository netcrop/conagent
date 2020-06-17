#! /bin/env /bin/python3.8
from time import sleep
from datetime import datetime
from getpass import getuser
from socket import gethostname
from random import randint
from os import stat,getuid,environ,unlink,chmod,getenv
from subprocess import Popen, PIPE,call, run
def genkey():
    proc = run('tty',stdout=PIPE,text=True)
    curtty = proc.stdout.rstrip('\n')
    ttyuid = stat(curtty).st_uid
    if ttyuid != uid:
        print("User uid:",uid,"needs to became the owner of", curtty)
        return

    run(['mkdir','-p',sshdir])
    tmpfh = open(tmpfile,'w')
    proc = run(['pwgen','--capitalize','--numerals',
    '--num-passwords=1','--secure'],stdout=tmpfh,stderr=PIPE)
    environ['GPG_TTY'] = curtty
    passfh = open(passasc,'w')
    tmpfh = open(tmpfile,'r')
    proc = run(['gpg','--symmetric','--no-verbose','--quiet',
    '--armor'],stdin=tmpfh,stdout=passfh,stderr=PIPE)
    tmpfh = open(tmpfile,'w')
    print ("""#!/bin/env /bin/bash
builtin declare -x GPG_TTY=%s 
gpg --decrypt --no-verbose --quiet %s"""%(curtty,passasc),file=tmpfh)
    environ['DISPLAY'] = ':0'
    environ['SSH_ASKPASS'] = tmpfile
    chmod(tmpfile,0o700)
    tmp = username + '@' + hostname
    arg = ['ssh-keygen','-C',tmp ,'-t', keytype,'-f', keyfile]
    proc = run(arg,stdin=None)
#    unlink(tmpfile)
if __name__ == '__main__':
    keytype = 'rsa'
    hostname = gethostname()
    uid = getuid()
    username = getuser()
    homedir = environ.get('HOME')
    sshdir = homedir+'/tmp/'
    tmpfile = '/var/tmp/' + str(randint(10000,99999))
    date = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    keyfile = sshdir + username + '_' + hostname + '_' + keytype + '_' + date
    passasc = keyfile + '_pass.asc'
    genkey()

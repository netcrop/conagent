#! /bin/env /bin/python3.8
import sys
import os
from glob import glob
from time import sleep
from datetime import datetime
from getpass import getuser
from socket import gethostname
from random import randint
from os import stat,getuid,environ,unlink,chmod,getenv,access
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
    chmod(tmpfile,0o700)
    tmpfh = open(tmpfile,'w')
    print ("""#!/bin/env /bin/bash
builtin declare -x GPG_TTY=%s 
gpg --decrypt --no-verbose --quiet %s"""%(curtty,passasc),file=tmpfh)
    tmpfh.close()
    environ['DISPLAY'] = ':0'
    environ['SSH_ASKPASS'] = tmpfile
    nullfh = open('/dev/null','r')
    cmd = ['ssh-keygen','-C',userhost ,'-t', keytype,'-f', keyfile]
    proc = run(cmd,stdin=nullfh)
    cmd = ' '.join(glob(sshdir + '*'))
    cmd = 'cp -av ' + cmd + ' ' + backupdir
    run(cmd.split()) 
    unlink(tmpfile)
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(sys.argv[0],'[backup dir]')
        exit()
    backupdir = sys.argv[1]
    if not (access(backupdir,os.X_OK) and access(backupdir,os.W_OK)):
        print(backupdir,'inaccessible')
        exit()
    keytype = 'rsa'
    hostname = gethostname()
    uid = getuid()
    username = getuser()
    userhost = username + '@' + hostname
    homedir = environ.get('HOME')
    sshdir = homedir+'/tmp/'
    tmpfile = '/var/tmp/' + str(randint(10000,99999))
    date = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    keyfile = sshdir + username + '_' + hostname + '_' + keytype + '_' + date
    passasc = keyfile + '_pass.asc'
    genkey()

#! /bin/env /bin/python3.8
from sys import argv
from glob import glob
from time import sleep
from datetime import datetime
from getpass import getuser
from socket import gethostname
from random import randint
from os import stat,getuid,environ,unlink,chmod,getenv,access,X_OK,W_OK,R_OK
from subprocess import Popen, PIPE,call, run
def genkey():
    proc = run('tty',stdout=PIPE,text=True)
    curtty = proc.stdout.rstrip('\n')
    ttyuid = stat(curtty).st_uid
    if ttyuid != uid:
        print("User uid:",uid,"needs to became the owner of", curtty)
        exit()
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
    files = ' '.join(glob(sshdir + '*'))
    cmd = 'chmod u=r,go= ' + files
    run(cmd.split())
    cmd = 'cp -av ' + files + ' ' + backupdir
    run(cmd.split()) 
if __name__ == '__main__':
    if len(argv) != 2:
        print(argv[0],'[backup dir]')
        exit()
    backupdir = argv[1]
    if not (access(backupdir,X_OK) and access(backupdir,W_OK)):
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
    try:
        genkey()
    finally:
        if (access(tmpfile,R_OK) and access(tmpfile,W_OK)):
            unlink(tmpfile)

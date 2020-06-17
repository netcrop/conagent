#! /bin/env /bin/python3
from datetime import datetime
from getpass import getuser
from socket import gethostname
from random import randint
from os import stat,getuid,environ,unlink
from subprocess import Popen, PIPE,call, run
def genkey():
    p = run('tty',stdout=PIPE,text=True)
    curtty = p.stdout.rstrip('\n')
    ttyuid = stat(curtty).st_uid
    if ttyuid != uid:
        print("User uid:",uid,"needs to became the owner of", curtty)
        return

    run(['mkdir','-p',sshdir])
    fh = open(tmpfile,'w+')
    run(['pwgen','--capitalize','--numerals','--num-passwords=1','--secure'],stdout=fh)
    fh2 = open(passasc,'w')
    environ['GPG_TTY'] = curtty
    run(['gpg','--symmetric','--no-verbose','--quiet',
    '--output',passasc,'--armor'],stdin=fh)
    unlink(tmpfile)
if __name__ == '__main__':
    keytype = 'rsa'
    hostname = gethostname()
    uid = getuid()
    username = getuser()
    homedir = environ.get('HOME')
    sshdir = homedir+'/tmp/'
    tmpfile = '/tmp/' + str(randint(10000,99999))
    date = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    keyfile = sshdir + username + '_' + hostname + '_' + keytype + '_' + date
    passasc = keyfile + '_pass.asc'
    genkey()

#!/bin/env -S PATH=/usr/local/bin:/usr/bin /bin/python3.8 -I
from subprocess import *
import glob,io,subprocess,sys,os,socket,getpass,random,datetime
class Conagent:
    def __init__(self,*argv):
        self.message = {'-h':'print this help message.',
        '-g':'[backup dir]: generate new key and copy to user defined backup dir.',
        '-a':'[ssh dir] add existing keys from user defined dir@default: $HOME/.ssh/ into ssh-agent cache'}
        if len(argv[0]) == 1:
            self.usage()
        self.argv = argv
        self.option = { '-h':self.usage ,'-g':self.genkey, '-a':self.addkey }
        self.keytype = 'rsa'
        self.hostname = socket.gethostname()
        self.uid = os.getuid()
        self.username = getpass.getuser()
        self.userhost = self.username + '@' + self.hostname
        self.homedir = os.environ.get('HOME')
        self.sshdir = self.homedir + '.ssh/'
        self.tmpfile = '/var/tmp/' + str(random.randint(10000,99999))
        self.date = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        self.keyfile = self.sshdir + self.username + '_' + self.hostname + '_' + \
        self.keytype + '_' + self.date
        self.passasc = self.keyfile + '_pass.asc'
    def genkey(self):
        try:
            if len(self.argv[0]) != 3:
                self.usage(self.argv[0][1])
            self.backupdir = self.argv[0][2] 
            if not (os.access(self.backupdir,os.X_OK) 
            and os.access(self.backupdir,os.W_OK)):
                self.usage()
            self.checktty()
            run(['mkdir','-p',self.sshdir],check=True)
            self.tmpfh = open(self.tmpfile,'w+')
            run(['pwgen','--capitalize','--numerals',
            '--num-passwords=1','--secure'],stdout=self.tmpfh,check=True)
            os.environ['GPG_TTY'] = self.curtty
            self.passfh = open(self.passasc,'w')
            run(['gpg','--symmetric','--no-verbose','--quiet','--armor'],
            stdin=self.tmpfh,stdout=self.passfh,check=True)
            os.chmod(self.tmpfile,0o700)
            self.tmpfh = open(self.tmpfile,'w')
            self.script = ("""\
            #!/bin/env /bin/bash
            builtin declare -x GPG_TTY=%s
            /bin/gpg --decrypt --no-verbose --quiet %s""")
            print( self.script.replace("    ","") % (self.curtty,self.passasc),
            file=self.tmpfh)
            self.tmpfh.close()
            os.environ['DISPLAY'] = ':0'
            os.environ['SSH_ASKPASS'] = self.tmpfile
            self.nullfh = open('/dev/null','r')
            run(['ssh-keygen','-C',self.userhost,'-t',self.keytype,'-f',self.keyfile],
            check=True,stdin=self.nullfh)
            self.files = ' '.join(glob.glob(self.sshdir + '*'))
            self.cmd = 'chmod u=r,go= ' + self.files
            run(self.cmd.split(),check=True);
            self.cmd = 'cp -av ' + self.files + ' ' + self.backupdir
            run(self.cmd.split())
        finally:
#            print(self.__dict__)
            for i in self.__dict__.values():
                if isinstance(i,io.TextIOWrapper):
                    i.close()
            if ( os.access(self.tmpfile,os.R_OK) and os.access(self.tmpfile,os.W_OK) ):
                os.unlink(self.tmpfile)
                print('finally')

    def usage(self,option=1):
        try:
            print(self.message[option])
        except KeyError:
            for key in self.message:
                print(key,self.message[key].replace("@","\n    "))
        exit()

    def checktty(self):
        self.proc = run('tty',stdout=PIPE,text=True,check=True)
        self.curtty = self.proc.stdout.rstrip('\n')
        self.ttyuid = os.stat(self.curtty).st_uid
        if self.ttyuid != self.uid:
            print("User uid:",self.uid,"needs to became the owner of",self.curtty)
            exit()

    def addkey(self):
        if len(self.argv[0]) == 3:
            self.sshdir = self.argv[0][2]
        if not (os.access(self.sshdir,os.X_OK) 
        and os.access(self.sshdir,os.W_OK)):
            self.usage()
        self.checktty()
        os.environ['TTY'] = self.curtty
        print(os.environ.get('TTY'))
if __name__ == '__main__':
    agent = Conagent(sys.argv)
    try:
        agent.option[agent.argv[0][1]]()
    except KeyError:
        agent.usage()

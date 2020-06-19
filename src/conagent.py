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
        self.homedir = os.environ.get('HOME') + '/'
        self.sshdir = self.homedir + '.ssh/'
        self.tmpfile = '/var/tmp/' + str(random.randint(10000,99999))
 
    def genkey(self):
        try:
            if len(self.argv[0]) != 3:
                self.usage(self.argv[0][1])
            self.backupdir = self.argv[0][2] 
            if not (os.access(self.backupdir,os.X_OK) 
            and os.access(self.backupdir,os.W_OK)):
                self.usage(self.argv[0][1])
            self.tmpfile = '/var/tmp/' + str(random.randint(10000,99999))
            self.date = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
            self.keyfile = self.sshdir + self.username + '_' + self.hostname + '_' + \
            self.keytype + '_' + self.date
            self.pubkey = self.keyfile + '.pub'
            self.passasc = self.keyfile + '_pass.asc'
            self.checktty()
            os.environ['GPG_TTY'] = self.curtty

            run(['mkdir','-p',self.sshdir],check=True)

            with open(self.tmpfile,'w') as self.tmpfh:
                self.cmd = 'pwgen --capitalize --numerals --num-passwords=1 --secure'
                run(self.cmd.split(),stdout=self.tmpfh,check=True)

            with open(self.passasc,'w') as self.passfh:
                with open(self.tmpfile,'r') as self.tmpfh:
                    self.cmd = 'gpg --symmetric --no-verbose --quiet --armor'
                    run(self.cmd.split(),stdin=self.tmpfh,stdout=self.passfh,check=True)


            self.script = ("""\
            #!/bin/env /bin/bash
            builtin declare -x GPG_TTY=%s
            /bin/gpg --decrypt --no-verbose --quiet %s""")

            with open(self.tmpfile,'w') as self.tmpfh: 
                print( self.script.replace("    ","") %
                (self.curtty,self.passasc),file=self.tmpfh)

            os.chmod(self.tmpfile,0o700)
            os.environ['DISPLAY'] = ':0'
            os.environ['SSH_ASKPASS'] = self.tmpfile

            with open('/dev/null','r') as self.nullfh: 
                self.cmd = 'ssh-keygen -C ' + self.userhost + ' -t ' \
                + self.keytype + ' -f ' + self.keyfile
                run(self.cmd.split(),check=True,stdin=self.nullfh)

            self.files = self.keyfile + ' ' + self.pubkey + ' ' + self.passasc 
            self.cmd = 'chmod u=r,go= ' + self.files
            run(self.cmd.split(),check=True);

            self.cmd = 'cp -av ' + self.files + ' ' + self.backupdir
            run(self.cmd.split(),check=True)

        finally:
            if ( os.access(self.tmpfile,os.R_OK) and os.access(self.tmpfile,os.W_OK) ):
                os.unlink(self.tmpfile)
                print('finally')

    def usage(self,option=1):
        if option in self.message:
            print(self.message[option].replace("@","\n    "))
        else:
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
        try:
            if len(self.argv[0]) == 3:
                self.sshdir = self.argv[0][2]
            if not (os.access(self.sshdir,os.X_OK) and os.access(self.sshdir,os.W_OK)):
                self.usage(self.argv[0][1])
            self.checktty()
            os.environ['GPG_TTY'] = self.curtty
            os.environ['DISPLAY']=':0'
            self.files = glob.glob(self.sshdir + '*_*_*_*[0-9]')
            self.returncode = 0
            try:
                self.proc = run(['ssh-add','-L'],stdout=PIPE,text=True,check=True)
            except CalledProcessError as e:
                if e.returncode == 2:
                    print(e)
                    return
            self.cache = self.proc.stdout.rstrip('\n').split()
            self.fcontent = {}
            self.ccontent = {}
            for i in self.files:
                with open(i + '.pub','r') as self.tmpfh:
                    self.fcontent[self.tmpfh.read().split()[1]] = i
            for i in self.cache:
                self.ccontent[i] = 1
            for i in self.fcontent:
                if i in self.ccontent:
                    continue
                self.passasc = self.fcontent[i] + '_pass.asc'
                if not os.access(self.passasc,os.R_OK):
                    continue
                self.tmpfile = '/var/tmp/' + str(random.randint(10000,99999))
                os.environ['SSH_ASKPASS'] = self.tmpfile 
                self.cmd = 'gpg --no-tty --decrypt --no-verbose --output ' \
                + self.tmpfile + ' --quiet ' + self.passasc
                run(self.cmd.split(),check=True)
                with open(self.tmpfile,'r') as self.tmpfh:
                    print(self.tmpfh.read())
                os.unlink(self.tmpfile)
        finally:
            print('finally')
            with open('/tmp/agentlog','w') as self.logfh:
                print(self.__dict__,file=self.logfh)
if __name__ == '__main__':
    agent = Conagent(sys.argv)
    if agent.argv[0][1] in agent.option:
        agent.option[agent.argv[0][1]]()
    else:
        agent.usage()

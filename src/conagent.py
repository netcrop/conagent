#!/bin/env -S PATH=/usr/local/bin:/usr/bin python3 -I
import re,tempfile,resource,glob,io,subprocess,sys,os,socket,getpass,random,datetime
class Conagent:
    def __init__(self,*argv):
        self.message = {'-h':' print this help message.',
        '-g':' [backup dir]: generate new key and copy to user defined backup dir.',
        '-a':' [ssh dir] add existing keys from user defined dir@default:' +
        '$HOME/.ssh/ into ssh-agent cache',
        '-ks':'[host] [opt:user] [opt:port] stop connection.' +
        '@optional defaults User=$USER and Port refers to ssh_config.',
        '-s': ' start ssh-agent.',
        '-l': ' list keys inside ssh-agent cache.', 
        '-r': ' remove keys from ssh-agent cache.',
        '-socks':'[remote host] opt:[remote port][remote user][local sport][keyfile]',
        '-j': ' [remote host] opt:[port] [user]',
        '-sendkey': '[key.pub][remote host] opt:[port][user]'}
        self.argv = argv
        self.args = argv[0]
        self.argc = len(self.args)
        if self.argc == 1: self.usage()
        self.option = { '-h':self.usage ,'-g':self.genkey, '-a':self.addkey,
        '-ks':self.killsocks, '-t':self.test, '-p':self.pwgen, '-d':self.decrypt,
        '-s':self.start, '-l':self.listkeys, '-r':self.removekeys,
        '-socks':self.socks, '-j':self.join, '-checktty':self.checktty,
        '-sendkey':self.sendkey }

        self.keytype = 'rsa'
        self.hostname = socket.gethostname()
        self.uid = os.getuid()
        self.username = getpass.getuser()
        self.userhost = self.username + '@' + self.hostname
        self.homedir = os.environ.get('HOME') + '/'
        self.sshdir = self.homedir + '.ssh/'
        self.tmpdir = '/var/tmp/'
        self.debugging = DEBUGGING
        self.curtty = ''

    def sendkey(self):
        self.debug()
        remoteuser = self.username
        port = 'CONAGENTREMOTEPORT'
        if self.argc < 4: self.usage(self.args[1])
        if self.argc >= 3: keyfile = self.args[2] 
        if self.argc >= 4: remotehost = self.args[3] 
        if self.argc >= 5: port = self.args[4]
        if self.argc >= 6: remoteuser = self.args[5]
        ipversion = ''
        with open(keyfile,'r') as fh:
            keycontent = fh.read()
        cmd = 'ping -q -n -c 1 ' + remotehost
        proc = self.run(cmd=cmd,stdout=subprocess.PIPE,exit_errorcode=-1)
        if proc != None:
            if proc.stdout.split()[1].find('::') != -1: ipversion = ' -6 '
        port = ' -o port=' + port
        cmd = 'env -S TERM=xterm-256color ssh -T -F '
        cmd += self.homedir + '.ssh/ssh_config ' + ipversion
        cmd += ' -i ' + keyfile
        cmd += remoteuser + '@' + remotehost + port
        print(cmd)

    def join(self):
        self.debug()
        remoteuser = self.username
        port = 'CONAGENTREMOTEPORT'
        if self.argc < 3: self.usage(self.args[1])
        if self.argc >= 3: remotehost = self.args[2] 
        if self.argc >= 4: port = self.args[3]
        if self.argc >= 5: remoteuser = self.args[4]
        ipversion = ''
        self.addkey(arg=False)
        cmd = 'ping -q -n -c 1 ' + remotehost
        proc = self.run(cmd=cmd,stdout=subprocess.PIPE,exit_errorcode=-1)
        if proc != None:
            if proc.stdout.split()[1].find('::') != -1: ipversion = ' -6 '
        port = ' -o port=' + port
        cmd = 'env -S TERM=xterm-256color ssh -F ' + \
        self.homedir + '.ssh/ssh_config ' + ipversion
        cmd += remoteuser + '@' + remotehost + port
        self.run(cmd=cmd)
        self.debug(info='end')

    def socks(self):
        self.debug()
        socksport = 'CONAGENTLOCALPORT1'
        port = 'CONAGENTREMOTEPORT1'
        remoteuser = self.username
        keyfile = ''
        if self.argc < 3: self.usage(self.args[1])
        if self.argc >= 3: remotehost = self.args[2] 
        if self.argc >= 4: port = self.args[3]
        if self.argc >= 5: remoteuser = self.args[4]
        if self.argc >= 6: socksport = self.args[5]
        if self.argc >= 7: keyfile = ' -i ' + self.args[6]
        self.addkey(arg=False)
        proc = self.run(cmd='lsof -i',stdout=subprocess.PIPE,exit_errorcode=-1)
        if proc != None:
            for i in proc.stdout.split():
                if i.find(socksport) != -1: return
        port = ' -o port=' + port
        socksport = ' -D ' + socksport
        cmd = 'ssh -F ' + self.homedir + '.ssh/ssh_config -fTN '
        cmd += keyfile + ' ' + socksport + ' ' + remoteuser +\
        '@' + remotehost + port
        self.run(cmd=cmd)
        self.debug(info='end')

    def removekeys(self):
        self.start()
        self.run(cmd='ssh-add -D')

    def listkeys(self):
        self.start()
        self.run(cmd='ssh-add -l')

    def start(self):
        # connect to ssh-agent for this session only 
        # parent session has to source sshenv to connect the same ssh-agent.
        self.debug()
        self.checktty()
        os.environ['SSH_TTY'] = self.curtty
        self.sshenv = self.homedir + '.ssh/' + self.hostname + '-ssh' 
        self.pattern = re.compile('([^=]+)=([^=]+)');
        cmd = 'ps -C ssh-agent -o pid= -o user='
        proc = self.run(cmd=cmd,stdout=subprocess.PIPE,exit_errorcode=-1)
        if proc != None:
            for i in proc.stdout.split('\n'):
                self.match = re.search('([^ ]+) ([^ ]+)',i)
                if self.match == None:continue
                if self.match.group(2) != self.username:continue
                if os.access(self.sshenv,os.R_OK):
                    self.getenv(self.sshenv)
                    self.debug(info='end 1')
                    return
                self.run(cmd='kill -s KILL ' + self.match.group(1))
                self.run(cmd='ssh-agent',outfile=self.sshenv)
                self.getenv(self.sshenv)
                self.debug(info='end 2')
                return
        self.run(cmd='ssh-agent',outfile=self.sshenv)
        self.getenv(self.sshenv)
        self.debug(info='end 3')

    def getenv(self,infile=''):
        with open(self.sshenv,'r') as fh:
            self.content = fh.read().split('\n')[:2]
        with open(self.sshenv,'w') as fh:
            for i in self.content:
                print(i,file=fh)
                for j in i.split():
                    self.match = self.pattern.search(j)
                    if self.match == None:continue
                    os.environ[self.match.group(1)] = self.match.group(2).rstrip(';')

    def genkey(self):
        if self.argc != 3: self.usage(self.args[1])
        self.backupdir = self.args[2] 
        if not (os.access(self.backupdir,os.X_OK) 
        and os.access(self.backupdir,os.W_OK)):
            self.usage(self.args[1])
        self.date = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        self.keyfile = self.sshdir + self.username + '_' + self.hostname + '_' + \
        self.keytype + '_' + self.date
        self.pubkey = self.keyfile + '.pub'
        self.passasc = self.keyfile + '_pass.asc'
        self.checktty()
        os.environ['GPG_TTY'] = self.curtty

        self.run(cmd='mkdir -p ' + self.sshdir)
        with tempfile.NamedTemporaryFile(mode='w+',
            dir=self.tmpdir,delete=False) as self.pssfh: 
            self.pwgen(stdout=self.pssfh)
        cmd = 'gpg --symmetric --no-verbose --quiet --armor'
        self.run(cmd=cmd,infile=self.pssfh.name,outfile=self.passasc)

        self.askpass(infile=self.passasc,outfile=self.pssfh.name)
        os.chmod(self.pssfh.name,0o700)
        os.environ['DISPLAY'] = ':0'
        os.environ['SSH_ASKPASS'] = self.pssfh.name

        cmd = 'ssh-keygen -C ' + self.userhost + ' -t ' \
        + self.keytype + ' -f ' + self.keyfile
        self.run(cmd=cmd,infile='/dev/null')

        self.files = self.keyfile + ' ' + self.pubkey + ' ' + self.passasc 
        cmd = 'chmod u=r,go= ' + self.files
        self.run(cmd=cmd)

        cmd = 'cp -av ' + self.files + ' ' + self.backupdir
        self.run(cmd=cmd)

    def askpass(self, infile='', outfile='', passfile=''):
        if passfile != '':
            passfile = ' --no-tty --batch --no-verbose --quiet --passphrase-file '\
            + passfile
        self.script = ("""\
        #!/bin/env /bin/bash
        builtin declare -x GPG_TTY=%s
        /bin/gpg --decrypt --no-verbose --quiet %s %s""")

        with open(outfile,'w') as fh: 
            print( self.script.replace("    ","") %
            (self.curtty, passfile, infile),file=fh)

    def usage(self,option=1):
        if option in self.message:
            print(self.message[option].replace("@","\n    "))
        else:
            for key in self.message:
                print(key,self.message[key].replace("@","\n    "))
        exit()

    def checktty(self):
        proc = self.run(cmd='tty',stdout=subprocess.PIPE,exit_errorcode=-1)
        if proc == None: return
        self.curtty = proc.stdout
        self.ttyuid = os.stat(self.curtty).st_uid
        if self.ttyuid != self.uid:
            info = 'User uid:'+ str(self.uid) + 'maybe needs to became the owner of' + \
            str(self.curtty)
            self.debug(info=info)

    def addkey(self,arg=True):
        self.debug()
        if arg == True:
            if self.argc == 3: self.sshdir = self.args[2]
            if not (os.access(self.sshdir,os.X_OK) and os.access(self.sshdir,os.W_OK)):
                self.usage(self.args[1])
        self.start()
        os.environ['GPG_TTY'] = self.curtty
        os.environ['DISPLAY']=':0'
        self.cache = {}
        self.files = glob.glob(self.sshdir + '*_*_*_*[0-9]')
        proc = self.run(cmd='ssh-add -L',stdout=subprocess.PIPE,exit_errorcode=-1)
        if proc != None: self.cache = proc.stdout.rstrip('\n').split()
        self.fcontent = {}
        self.ccontent = {}
        for i in self.files:
            with open(i + '.pub','r') as fh:
                self.fcontent[fh.read().split()[1]] = i
        for i in self.cache: self.ccontent[i] = 1
        for i in self.fcontent:
            if i in self.ccontent: continue
            keyfile = self.fcontent[i]
            self.passasc = keyfile + '_pass.asc'
            self.gpgpassasc = keyfile + '_gpg.asc'
            if not os.access(self.passasc,os.R_OK):
                self.nopass()
                continue
            if not os.access(self.gpgpassasc,os.R_OK):
                self.manualpass(keyfile=keyfile)
                continue
            self.autopass(keyfile=keyfile)

    def pwgen(self, seed='',filepath='',length='8',outfile='',stdout=None):
        if seed == '': seed = str(random.randint(1000000,9999999))
        if not os.access(filepath,os.R_OK): filepath = '/dev/null'
        cmd ='pwgen --capitalize --numerals --num-passwords=1 --secure --sha1='\
         + filepath + '#' + seed + ' ' + length
        return self.run(cmd=cmd,outfile=outfile,stdout=stdout)

    def autopass(self,keyfile=''):
        self.debug()
        # file deleted as default, fileobj remain for later use 
        # file name remain for GPG, otherwise GPG report error.
        with tempfile.NamedTemporaryFile(dir=self.tmpdir) as self.pssfh: 
            with tempfile.NamedTemporaryFile(dir=self.tmpdir) as self.askpassfh: 
                os.environ['SSH_ASKPASS'] = self.askpassfh.name 

        self.infd,self.outfd = os.pipe()
        cmd ='gpg --no-tty --batch --decrypt --no-verbose --quiet '
        cmd += '--passphrase-fd ' + str(self.infd)
        cmd += ' --output ' + self.pssfh.name 
        cmd += ' ' + self.gpgpassasc
        with subprocess.Popen(cmd.split(),pass_fds=[self.infd],encoding='utf-8',
        stderr = subprocess.PIPE) as parentproc:
            os.close(self.infd)
            proc = self.pwgen(seed=os.path.
            basename(self.gpgpassasc),stdout=subprocess.PIPE)
            with open(self.outfd,'w',encoding='utf-8') as self.outfh:
                self.outfh.write(proc.stdout)
                proc.stdout = 0
            parentstderr = parentproc.communicate()[1].rstrip('\n')
            if parentstderr != '':
                print(parentstderr)
                exit()
        self.askpass(infile=self.passasc, passfile=self.pssfh.name,
        outfile=self.askpassfh.name)
        os.chmod(self.askpassfh.name,0o700)
        self.run(cmd='ssh-add ' + keyfile,infile='/dev/null')
        os.unlink(self.askpassfh.name)
        self.askpassfh = None

    def decrypt(self,infile='',outfile=''):
        if not os.access(infile,os.R_OK): return
        cmd = 'gpg --no-tty --batch --decrypt --no-verbose --quiet '
        self.run(cmd=cmd,outfile=outfile,infile=infile)

    def nopass(self):
        self.debug()

    def manualpass(self,keyfile=''):
        self.debug()
        # gpg-agent will remember user entered pass and reuse i next step.
        self.decrypt(infile=self.passasc, outfile='/dev/null')
        with tempfile.NamedTemporaryFile(mode='w+',
            dir=self.tmpdir,delete=False) as self.pssfh: 
            os.environ['SSH_ASKPASS'] = self.pssfh.name 
        self.askpass(infile=self.passasc,outfile=self.pssfh.name)
        try: os.chmod(self.pssfh.name,0o700) 
        except FileNotFoundError: return 1
        self.run(cmd='ssh-add ' + keyfile,infile='/dev/null')
        os.unlink(self.pssfh.name)
        self.pssfh = None

    def killsocks(self):
        self.port = ''
        if self.argc < 3: self.usage(self.args[1])
        if self.argc >= 3: self.host = self.args[2]
        if self.argc >= 4: self.username = self.args[3]
        if self.argc >= 5: self.port = ' -o port=' + self.args[4]
        self.userhost = self.username + '@' + self.host
        cmd = 'ssh -F ' + self.sshdir + 'ssh_config -fTN -O stop '\
        + self.userhost + self.port
        self.run(cmd=cmd) 

    def test(self):
        with tempfile.NamedTemporaryFile(mode='w+',
        dir=self.tmpdir,delete=False) as self.testfh:
            self.testfh.write('big')
        proc = self.run(cmd='cat',stdout=subprocess.PIPE,infile=self.testfh.name)
        if proc != None:print(proc.stdout)
        proc = self.run(stdout=subprocess.PIPE,infile='/etc/hostname')
        if proc != None:print(proc.stdout)
        self.run(cmd='date -u')

    def run(self, cmd='',infile='',outfile='',stdin=None,stdout=None,
        text=True,pass_fds=[],exit_errorcode='',shell=False):
        try:
            proc = None
            emit = __file__ + ':' + sys._getframe(1).f_code.co_name + ':' \
            + str(sys._getframe(1).f_lineno)
            if infile != '': stdin = open(infile,'r')
            if outfile != '': stdout = open(outfile,'w')
            proc = subprocess.run(cmd.split(),
            stdin=stdin,stdout=stdout,text=text,check=True,
            pass_fds=pass_fds,shell=shell)
            if infile != '': stdin.close() 
            if outfile != '': stdout.close()
            if not isinstance(proc,subprocess.CompletedProcess):
                self.debug(info='end 1',emit=emit)
                return None
            if isinstance(proc.stdout,str):
                proc.stdout = proc.stdout.rstrip('\n')
                self.debug(info='end 2',emit=emit)
                return proc
        except subprocess.CalledProcessError as e:
            emit += ':' + str(e.returncode)
            if exit_errorcode == '':
                if e.returncode != 0:
                    self.debug(info='end 3: ',emit=emit)
                    exit()
            elif e.returncode == exit_errorcode:
                self.debug(info='end 4',emit=emit)
                exit()
            return None

    def debug(self,info='',outfile='',emit=''):
        if not self.debugging: return
        emit = sys._getframe(1).f_code.co_name + ':' \
        + str(sys._getframe(1).f_lineno) + ':' + info + ':' + emit
        print(emit)

if __name__ == '__main__':
    agent = Conagent(sys.argv)
    if agent.args[1] not in agent.option: agent.usage()
    try: agent.option[agent.args[1]]()
    finally:
        agent.debug(info='session finally end')
        for key,value in agent.__dict__.items():
            if isinstance(value,io.TextIOWrapper):
                value.close()
                continue
            if isinstance(value,tempfile._TemporaryFileWrapper):
                value.close() 
                if os.access(value.name,os.R_OK): os.unlink(value.name)
#        if agent.debugging:
#            with open('/tmp/agentlog','w') as agent.logfh:
#                print(agent.__dict__,file=agent.logfh)

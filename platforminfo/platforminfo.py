# PlatformInfo v1.0.0
# Copyright (c) 2023 Tejas Raman et al.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.


import os
import subprocess
import sys

if sys.platform == "win32":
    import winreg


def subprocess_postproc(x):
    return x.stdout.read().strip().decode("utf-8")


class PlatformError(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def parse_file(filename, to_be_cut, basestr):
    with open(filename) as file:
        x = dict()
        for line in file:
            x[(line.split(to_be_cut)[0]).strip()] = (
                line.split(to_be_cut)[1]).strip()

            if (line.split(to_be_cut)[0]).strip() == basestr:
                break

        return_value = x[basestr].strip()
    return return_value


class Platform:
    def __init__(self):
        bases = {
            "win32": "windows",
            "darwin": "mac",
            "linux": "linux",
            "bsd": "bsd"
        }
        self.platform = bases[sys.platform]

    def base_platform(self):
        return self.platform

    def desktop_envoronment(self):
        if self.platform not in ["linux", "bsd"]:
            raise PlatformError(
                'DesktopEnvironment used on a non-Linux/BSD system')
        else:
            # FIXME: Make this apply to BSD, make this more universal
            env = os.environ['XDG_CURRENT_DESKTOP']
            return env

    def kenrel_version(self):
        if self.platform in ["mac", "linux", "bsd"]:
            kernel = subprocess.Popen("uname -r",
                                      shell=True,
                                      stdout=subprocess.PIPE)
            return subprocess_postproc(kernel)

        elif self.platform == "windows":
            version = ".".join((subprocess_postproc(
                subprocess.Popen(
                    "wmic os get version /VALUE",
                    stdout=subprocess.PIPE,
                )).split("|"))[0].split("=")[1].split(".")[:2])
            return version

    def os_architecture(self):
        if self.platform in ["mac", "linux", "bsd"]:
            return subprocess_postproc(
                subprocess.Popen("uname -m", shell=True,
                                 stdout=subprocess.PIPE))
        else:
            arch = os.environ['PROCESSOR_ARCHITECTURE']
            arches = {'AMD64': 'x86_64', 'ARM64': 'aarch64'}
            if arches[arch] != arch:
                return arches[arch]
            return arch

    def build_number(self):
        if self.platform == "mac":
            buildnum = subprocess_postproc(
                subprocess.Popen("sw_vers -buildVersion",
                                 shell=True,
                                 stdout=subprocess.PIPE))
            return buildnum

        elif self.platform == "windows":
            access_registry = winreg.ConnectRegistry(
                None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(
                access_registry,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            value = winreg.QueryValueEx(key, "CurrentBuild")
            return value
        else:
            raise PlatformError(
                "PlatformInfo: buildnumber function used on a non-Macintosh/Windows system"
            )

    def os_version(self):
        # BSD support here is WIP
        if self.platform == "linux":
            if os.path.isfile("/etc/os-release"):
                return parse_file("/etc/os-release", "=", "VERSION_ID")

            elif os.path.isfile("/usr/lib/os-release"):
                return parse_file("/usr/lib/os-release", "=", "VERSION_ID")

            elif os.path.isfile("/etc/lsb-release"):
                return parse_file("/etc/lsb-release", "=", "DISTRIB_RELEASE")

            elif os.path.isfile("/usr/bin/lsb-release"):
                version_sp = subprocess.Popen("/usr/bin/lsb_release -r",
                                              shell=True,
                                              stdout=subprocess.PIPE)
                version = (subprocess_postproc(version_sp).split(":"))[1]
                return version

        elif self.platform == "mac":
            return subprocess_postproc(
                subprocess.Popen("sw_vers -productVersion",
                                 shell=True,
                                 stdout=subprocess.PIPE))

        elif self.platform == "windows":
            version = (subprocess_postproc(
                subprocess.Popen(
                    "wmic os get Name /VALUE",
                    shell=True,
                    stdout=subprocess.PIPE)).split("|"))[0].split("=")[1]
            return version

    def cpu_prettyname(self):
        if self.platform == "linux":
            return (parse_file("/proc/cpuinfo", ":", "model name"))

        elif self.platform == "windows":
            access_registry = winreg.ConnectRegistry(
                None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(
                access_registry,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            value = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
            return value

    def cpu_cores(self, coreop):
        if self.platform == "linux":
            coretypes = {
                "physical": 'cpu cores',
                "logical": 'siblings'
            }
            return int(parse_file("/proc/cpuinfo", ":", coretypes[coreop]))

        elif self.platform == "windows":
            coretypes_win = {"physical": "NumberOfCores",
                             "logical": "NumberOfLogicalProcessors"}
            cores = subprocess_postproc(
                subprocess.Popen(
                    f"wmic cpu get {coretypes_win[coreop]} /VALUE",
                    stdout=subprocess.PIPE,
                )).split("=")[1]
            return cores

    def gpu_prettyname(self):
        if self.platform == "windows":
            access_registry = winreg.ConnectRegistry(
                None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(
                access_registry,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\WinSAT")
            value = winreg.QueryValueEx(key, "PrimaryAdapterString")[0].strip()
            return value

    def ram(self, format):
        formats = {
            "B": 1,
            "KB": 1000,
            "MB": 1000000,
            "GB": 1000000000,
            "TB": 1000000000000
        }

        if format not in formats.keys():
            raise PlatformError("Invalid RAM format sprcified")

        if self.platform == "windows":
            ram = subprocess_postproc(
                subprocess.Popen(
                    f"wmic ComputerSystem get TotalPhysicalMemory /VALUE",
                    stdout=subprocess.PIPE,
                )).split("=")[1]
            if format == "B":
                return int(ram)
            else:
                return int(ram) / formats[format]

# PlatformInfo v1.0.0
# Tejas Raman, 2023
# Licensed under MIT License

import os
import subprocess
import sys
from helper import platforminfolib

if sys.platform == "win32":
    import winreg


class Platform:

    def __init__(self):
        bases = {"win32": "windows", "darwin": "mac", "linux": "linux"}
        self.platform = bases[sys.platform]

    def basePlatform(self):
        return self.platform

    def kernelVersion(self):
        if self.platform in ["mac", "linux"]:
            kernel = subprocess.Popen(["uname", "-r"], stdout=subprocess.PIPE)
            return platforminfolib.subprocess_postproc(kernel)

        elif self.platform == "windows":
            version = ".".join((platforminfolib.subprocess_postproc(
                subprocess.Popen(
                    "wmic os get version /VALUE",
                    shell=True,
                    stdout=subprocess.PIPE,
                )).split("|"))[0].split("=")[1].split(".")[:2])
            return version

    def arch(self):
        if self.platform in ["mac", "linux"]:
            return platforminfolib.subprocess_postproc(
                subprocess.Popen(["uname", "-m"], stdout=subprocess.PIPE))
        else:
            arch = os.environ['PROCESSOR_ARCHITECTURE']
            arches = {'x86': 'x86', 'AMD64': 'x86_64', 'ARM64': 'aarch64'}
            return arch

    def buildNumber(self):
        if self.platform == "mac":
            buildnum = platforminfolib.subprocess_postproc(
                subprocess.Popen("sw_vers -buildVersion",
                                 shell=True,
                                 stdout=subprocess.PIPE))
            return buildnum

        elif self.platform == "windows":
            access_registry = winreg.ConnectRegistry(None,
                                                     winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(
                access_registry,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            value, type = winreg.QueryValueEx(key, "CurrentBuild")
            return value
        else:
            raise platforminfolib.PlatformError(
                "PlatformInfo: buildnumber function used on a non-Macintosh/Windows system"
            )

    def osVersion(self):
        if self.platform == "linux":
            if os.path.isfile("/etc/os-release"):
                return platforminfolib.Parser("/etc/os-release", "=",
                                              "VERSION_ID")

            elif os.path.isfile("/usr/lib/os-release"):
                return platforminfolib.Parser("/usr/lib/os-release", "=",
                                              "VERSION_ID")

            elif os.path.isfile("/etc/lsb-release"):
                return platforminfolib.Parser("/etc/lsb-release", "=",
                                              "DISTRIB_RELEASE")

            elif os.path.isfile("/usr/bin/lsb-release"):
                version_sp = subprocess.Popen("/usr/bin/lsb_release -r",
                                              shell=True,
                                              stdout=subprocess.PIPE)
                version = (platforminfolib.subprocess_postproc(
                    version_sp).split(":"))[1]
                return version

        elif self.platform == "mac":
            return platforminfolib.subprocess_postproc(
                subprocess.Popen(["sw_vers -productVersion"],
                                 shell=True,
                                 stdout=subprocess.PIPE))

        elif self.platform == "windows":
            version = (platforminfolib.subprocess_postproc(
                subprocess.Popen(
                    "wmic os get Name /VALUE",
                    shell=True,
                    stdout=subprocess.PIPE)).split("|"))[0].split("=")[1]
            return version

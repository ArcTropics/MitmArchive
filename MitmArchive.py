import os

import json
import argparse
import subprocess
from subprocess import PIPE

import pathlib
filepath = pathlib.Path(__file__).parent.resolve()

import sys
sys.path.append(filepath)

from modules.PipeProcessor import PipeProcessor




class MitmArchive:

    def __init__(self, port, archiveEn, extras):
        self.process=None
        self.port = port
        self.archiveEn = archiveEn
        self.extras = extras
        self.run()

    def processStdout(self, line):
        print(line)


    def processStderr(self, line):
        print(line)


    def openScopeFile(self, fileName):
        currentPath = pathlib.Path(os.getcwd()).resolve()
        homeDir = pathlib.Path(os.path.expanduser('~')).resolve()

        while len(str(currentPath)) >= len(str(homeDir)):
            
            path = currentPath / fileName

            if os.path.isfile(str(path)):
                return str(path)
            else:
                currentPath = currentPath.parent
            
        return None


    def patternExtractor(self, scopeFile):
        filename = self.openScopeFile(scopeFile)

        patterns=[]
        antipatterns=[]
        
        if filename:
            with open(filename) as f:
                for line in f.readlines():

                    line = line[:-1]
                    
                    if line[0] == "!":
                        line = line[1:]
                        antipatterns.append(line)
                    else:
                        patterns.append(line)

        return (patterns, antipatterns)

        
    def run(self):
        
        command = "mitmdump"
        command += " --listen-port " + str(self.port)

        command += " " + str(self.extras)

        patterns, antipatterns = self.patternExtractor(".scope")

        for p in patterns:
            print("allowing host: " + str(p))
            command += " --allow-hosts '" + p + ":443$'"
            command += " --allow-hosts '" + p + ":80$'"

        for ap in antipatterns:
            print("ignoring host: " + str(ap))
            command += " --ignore-hosts '" + ap + ":443$'"
            command += " --ignore-hosts '" + ap + ":80$'"
            
        if self.archiveEn:
            filepath = (pathlib.Path(__file__).parent / "MitmRoot.py").resolve()
            command += " -s " + str(filepath)

        print(command)
        
        self.process = subprocess.Popen(command, shell=True, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        self.stdoutProcessor = PipeProcessor(self.processStdout, self.process.stdout)
        self.stderrProcessor = PipeProcessor(self.processStdout, self.process.stderr)
        
        self.process.stdin.close()
        if self.process.wait() != 0:
            raise RuntimeError(self.process.returncode)

if __name__ == "__main__":


    # Construct the argument parser
    ap = argparse.ArgumentParser()

    # Add the arguments to the parser

    ap.add_argument("-d", "--dns_recording", required=False, default="None", help="-d/--dns-recording [interface] Activate Dns Recording on interface, this helps you to recover dns hostnames in case your configuration leaves you with ip addresses only")
    ap.add_argument("-t", "--soperand", required=False, help="second operand")
    ap.add_argument("-e", "--extra_args", required=False, default="", help="Additional Arguments for Mitmdump")
    ap.add_argument("-p", "--port", required=False, default=8080, help="The port on which the proxy is going to listen")
    ap.add_argument("-a", "--archive", required=False, default="True", help="Use this flag to disable archiving (Proxy without writing to disk)")
    

    args = vars(ap.parse_args())
    port = int(args['port'])
    archiveEn = False
    if args['archive'] == "True":
        archiveEn = True

    extras = args['extra_args']

    passedConfig = {}
    passedConfig["dns-recording"] = args["dns_recording"]

    with open(".archive_conf.json", "w") as f:
        f.write(json.dumps(passedConfig, indent = 4))
        
    archive = MitmArchive(port, archiveEn, extras)
    

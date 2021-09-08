import os
import re
import json

import multitimer
import subprocess

import pathlib
filepath = pathlib.Path(__file__).parent.resolve()

import sys
sys.path.append(filepath)

from modules.PipeProcessor import PipeProcessor


class DnsResolver:

    dnsTable = {}
    
    def __init__(self, interface):
        self.pipeProcessor = None
        self.process = None
        self.saveTimer = None
        self.interface = interface
        self.load()

    def load(self):
        try:
            with open("dnsRecords.json", "r") as f:
                jsonString = f.read()
                DnsResolver.dnsTable = json.loads(jsonString)
        except Exception as e:
            print(str(e))
            

    def save(self):

        print("SAVING DNS RECORDS")
        
        jsonString = json.dumps(DnsResolver.dnsTable, indent = 4)

        with open("dnsRecords.json", "w") as f:
            f.write(jsonString)
        
        

    def processStdout(self, string):

        getHost = False
        hosts = []        
        
        parts = string.replace(", ", " ").replace(". ", " ").replace(" A ", "___A___").split(" ")
        
        for part in parts:
            if "___A___" in part:
                match = part.split("___A___")
                hostname = DnsResolver.dnsTable.get(match[1], [])

                hosts.append(match[0])
                hosts.sort(key=len)

                hostname.extend(hosts)

                #remove duplicates
                res = []
                [res.append(x) for x in hostname if x not in res]
                
                DnsResolver.dnsTable[match[1]] = res
                getHost = False
                
            elif "CNAME" in part:
                getHost = True

            elif getHost:
                hosts.append(part)

    def cleanup(self):
        for key in DnsResolver.dnsTable:
            hosts = DnsResolver.dnsTable[key]
            
            res = []
            [res.append(x) for x in hosts if x not in res]

            DnsResolver.dnsTable[key] = res

        self.save()


    def get_size(self, start_path = '.'):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        return total_size

        
    def apply(self):

        #matching ip addresses
        pat = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        folders = os.listdir("output/")
        for folder in folders:
            if pat.match(folder):
                #this folder is an IP address, lets see if we find a dns record

                hostnames = DnsResolver.dnsTable.get(folder, [])
                if len(hostnames) > 0:
                    #found hostname
                    success = True
                    
                    for folder_ in folders:
                        if folder_ in hostnames[0]:
                            #directory already exists
                            success = False
                            srcSize = self.get_size("output/" + folder)
                            destSize = self.get_size("output/" + hostnames[0])
                            print("MERGING folder '" + folder + "' into existing '" + hostnames[0] + "'")
                            break

                    if success:
                        print("COPYING folder '" + folder + "' into existing '" + hostnames[0] + "'")

                    #copy the directory
                    shiftP = subprocess.Popen("cp -rl output/" + folder + " output/" + hostnames[0] , shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                    shiftP.wait()
                    if not success:
                        outputSize = self.get_size("output/" + hostnames[0])

                        if outputSize == srcSize + destSize:
                            success = True

                    if success:
                        print("SUCCESS")

                        deleteP = subprocess.Popen("rm -rf output/" + folder, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                        deleteP.wait()
                        
                    else:
                        print("FAILURE: Foldersizes not matching! Not removing Source Folder")
                    
        
    def execute(self):        
                
        self.process = subprocess.Popen("tcpdump -n -s 1500 udp and port 53 -v -i " + self.interface, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE,  stdin=subprocess.PIPE)                
        self.pipeProcessor = PipeProcessor(self.processStdout, self.process.stdout)

        self.saveTimer = multitimer.MultiTimer(15, self.save)
        self.saveTimer.start()

        

if __name__ ==  "__main__":
    inst = DnsResolver()
    inst.execute()

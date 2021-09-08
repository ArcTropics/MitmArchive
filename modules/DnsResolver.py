import os
import re
import json
import time

import multitimer
import subprocess

import pathlib
filepath = pathlib.Path(__file__).parent.resolve()

import sys
sys.path.append(filepath)

from modules.PipeProcessor import PipeProcessor


class DnsResolver:

    dnsTable = {}
    dnsTableInverse = {}
    dnsIpTable = {}
    
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
                
            with open(".dnsIpRecords.json", "r") as f:
                jsonString = f.read()
                DnsResolver.dnsIpTable = json.loads(jsonString)
                
            with open(".dnsInverseRecords.json", "r") as f:
                jsonString = f.read()
                DnsResolver.dnsTableInverse = json.loads(jsonString)

                
        except Exception as e:
            print(str(e))
            

    def save(self):

        print("SAVING DNS RECORDS")
        
        jsonString = json.dumps(DnsResolver.dnsTable, indent = 4)
        with open("dnsRecords.json", "w") as f:
            f.write(jsonString)


        jsonString = json.dumps(DnsResolver.dnsIpTable, indent = 4)
        with open(".dnsIpRecords.json", "w") as f:
            f.write(jsonString)

        jsonString = json.dumps(DnsResolver.dnsTableInverse, indent = 4)
        with open(".dnsInverseRecords.json", "w") as f:
            f.write(jsonString)

            

    def processStdout(self, string):

        getHost = False
        hosts = []        
        
        parts = string.replace(", ", " ").replace(". ", " ").replace(" A ", "___A___").split(" ")
        
        for part in parts:
            if "___A___" in part:
                match = part.split("___A___")

                hosts.append(match[0])
                hosts.sort(key=len)

                ip = ""
                for host in hosts:
                    ip = DnsResolver.dnsTableInverse.get(host, "")
                    if len(ip) > 0:
                        break

                if not len(ip) > 0:
                    ip = match[1]
                    

                #create a reference in the ip table
                DnsResolver.dnsIpTable[match[1]] = ip
    
                #create entries in the inverse table
                for host in hosts:
                    DnsResolver.dnsTableInverse[host] = ip


                hostnames = DnsResolver.dnsTable.get(ip, [])
                hostnames.extend(hosts)
                
                #remove duplicates
                res = []
                [res.append(x) for x in hostnames if x not in res]

                DnsResolver.dnsTable[ip] = res
                getHost = False
                
            elif "CNAME" in part:
                getHost = True

            elif getHost:
                hosts.append(part)

    @staticmethod
    def resolveIp(ip):
        
        refIp = DnsResolver.dnsIpTable.get(ip, "")
        if len(refIp) > 0:
            hostnames = DnsResolver.dnsTable.get(str(refIp), "")
            if len(hostnames) > 0:
                return hostnames[0]

        return None

                
    def cleanup(self):
        for key in DnsResolver.dnsTable:
            hosts = DnsResolver.dnsTable[key]
            
            res = []
            [res.append(x) for x in hosts if x not in res]
            
            for host in res:
                for key_ in DnsResolver.dnsTable:
                    if key_ != key:
                        for host_ in DnsResolver.dnsTable[key]:
                            if host_ == host:
                                #redirect to other ip
                                res = [key_]
                                print("redirecting ip " + str(key) + " to " + str(key_))

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


    def moveFolder(self, src, dest, isIp = False):
        folders = os.listdir("output/")
        success = True

        
        for folder_ in folders:
            if folder_ in dest:
                #directory already exists
                success = False
                srcSize = self.get_size("output/" + src)
                destSize = self.get_size("output/" + dest)                
                print("MERGING folder '" + src + "' into existing '" + dest + "'")
                break

        if success:
            print("COPYING folder '" + src + "' to '" + dest + "'")

        #copy the directory
        try:
            os.mkdir("output/" + dest)
        except:
            pass
        
        shiftP = subprocess.Popen("cp -rl output/" + src + "/* output/" + dest , shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        print("cp -rl output/" + src + "/* output/" + dest)
        shiftP.wait()
        if not success:
            outputSize = self.get_size("output/" + dest)
        
            if outputSize <= srcSize + destSize:
                success = True

        if success:
            print("SUCCESS")

            deleteP = subprocess.Popen("rm -rf output/" + src, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            deleteP.wait()
                
        else:
            print("FAILURE: Foldersizes not matching! Not removing Source Folder")
            print("src : " + str(srcSize) + " dst: " + str(destSize) + " sum: " + str(srcSize + destSize) + "  output: " + str(outputSize))
        
    
    def apply(self):

        #matching ip addresses
        pat = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        folders = os.listdir("output/")
        for folder in folders:
            if pat.match(folder):
                #this folder is an IP address, lets see if we find a dns record

                hostname = DnsResolver.resolveIp(folder)
                if hostname:
                    #found hostname
                    self.moveFolder(folder, hostname, True)

            else:
                ip = DnsResolver.dnsTableInverse.get(folder, "")
                if len(ip) > 0:

                    host_ = DnsResolver.resolveIp(ip)
                    if host_ and host_ != folder:
                        self.moveFolder(folder, host_)
                        
                
        
    def execute(self):        
                
        self.process = subprocess.Popen("tcpdump -n -s 1500 udp and port 53 -v -i " + self.interface, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE,  stdin=subprocess.PIPE)                
        self.pipeProcessor = PipeProcessor(self.processStdout, self.process.stdout)

        self.saveTimer = multitimer.MultiTimer(15, self.save)
        self.saveTimer.start()

        

if __name__ ==  "__main__":
    inst = DnsResolver()
    inst.execute()


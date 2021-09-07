import os
import sys
import json

from inspect import getmembers
import mitmproxy.http
from mitmproxy import ctx
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor


import pathlib
filepath = pathlib.Path(__file__).parent.resolve()

import sys
sys.path.append(filepath)

from modules.RexpMatcher import RexpMatcher
from modules.Archiver import Archiver
from modules.DnsResolver import DnsResolver

class mitmRoot:

    NUM_THREADS = 10
    
    def __init__(self):
        print(os.getcwd())
        try:
            os.mkdir("output")
        except:
            pass

        try:
            with open(".archive_conf.json", "r") as f:
                config = f.read()
                configDict = json.loads(config)

                self.dnsResolver = None
                interface = configDict["dns-recording"]
                if interface != "None":
                    print("INTERFACE")
                    self.dnsResolver = DnsResolver(interface)
                    self.dnsResolver.execute()
                    
        except Exception as e:
            print(str(e))
            pass


        
        self.inscope = RexpMatcher(".scope")
        print("inscope file found: " + str(self.inscope.fileFound))
        
        self.conts = RexpMatcher(".contents")
        print("contents file found: " + str(self.conts.fileFound))

        self.executor = ThreadPoolExecutor(self.NUM_THREADS)
        self.archiver = Archiver()

        

    def response(self, flow: mitmproxy.http.HTTPFlow):


        contentType = flow.response.headers.get("content-type", "")        
        if len(contentType) > 1:
            print(contentType)
            if self.conts.match(contentType):

                
                #for later
                self.executor.submit(self.archiver.archive,(flow))
                print("MATCH")
        
                #self.archiver.archive(flow)
        
    def archivingThread(self, flow):
        print("hello from archiver")

                
    def request(self, flow: mitmproxy.http.HTTPFlow):
        pass
        
addons = [
    mitmRoot()
]

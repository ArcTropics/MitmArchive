import os
import json
import copy

import pathlib
import mitmproxy

from urllib.parse import urlparse
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

import pathlib
filepath = pathlib.Path(__file__).parent.resolve()

import sys
sys.path.append(filepath)

from modules.DnsResolver import DnsResolver


class Archiver:        

    def createFolder(self, DICT):

        url = DICT["url"]
        outputPath = DICT["outputPath"]
        
        urlPath =  url.netloc + url.path
        path = outputPath / urlPath
        name = ""
        print(str(url.path)[-1])
        if str(url.path)[-1] != "/":
            name = path.name
            path = path.parent

        print(url)
        print("creating path: " + str(path))
        print("filename: " + str(name))

        DICT["path"] = path
        DICT["name"] = name
        

    def storeMeta(self, flow, DICT):
        url = DICT["url"]
        print(url)

        metaDict = {}
        metaDict["scheme"] = url.scheme
        metaDict["host"] = url.netloc
        metaDict["path"] = url.path
        metaDict["params"] = url.params
        metaDict["query"] = url.query
        metaDict["fragment"] = url.fragment
                
        metaDict["response-code"] = flow.response.status_code
        metaDict["method"] = flow.request.method
        print(flow.request.method)
        metaDict["port"] = flow.request.port
        metaDict["http_version"] = flow.request.http_version
        
        
        js = json.dumps(metaDict, indent = 4)
        with open(str(DICT["path_prefix"] / "meta.json"),"w") as f:
            f.write(js)
        
        
        
    def storeContent(self, flow, DICT):

        if len(flow.request.text) > 0:
            with open(str(DICT["path_prefix"] / "request_body.txt"),"w") as f:
                f.write(flow.request.text)

        
        with open(str(DICT["path_prefix"] / "response_body.txt"),"w") as f:
            f.write(flow.response.text)
        

    def storeHeaders(self, flow, DICT):
        
        with open(str(DICT["path_prefix"] / "request_headers.txt"),"w") as f:
            for header in flow.request.headers:
                f.write(header + ": " + flow.request.headers[header] + "\n")
        
        with open(str(DICT["path_prefix"] / "response_headers.txt"),"w") as f:
            for header in flow.response.headers:
                f.write(header + ": " + flow.response.headers[header])


    def archiveFlow(self, flow: mitmproxy.http.HTTPFlow):
        
        DICT = {}
        
        DICT["outputPath"] = (pathlib.Path(os.getcwd()) / "output")
        url = urlparse(flow.request.url)

        try:
            if DnsResolver.dnsTable.get(url.netloc, "None") is not "None":
                print("REPLACING URL NETLOC:")
                print(url.netloc)
                url = urlparse(flow.request.url.replace(url.netloc, DnsResolver.dnsTable[url.netloc][0]))
                print(url.netloc)

        except Exception as e:
            print(str(e))
        
        DICT["url"] = url
        
        self.createFolder(DICT)

        print("creating folder: " + str(DICT["path"]))
        
        now = datetime.now() # current date and time
        
        date_time = now.strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]
        print("date and time:",date_time)	
        
        DICT["ts"] = date_time
        DICT["prefix"] = "ENDPOINT_" + DICT["name"] + "/" + DICT["ts"]
        DICT["path_prefix"] = DICT["path"] / DICT["prefix"]

        DICT["path_prefix"].mkdir(parents=True, exist_ok=True)

        
        self.storeMeta(flow, DICT)
        self.storeContent(flow, DICT)
        self.storeHeaders(flow, DICT)

        
    def archive(self, flow: mitmproxy.http.HTTPFlow):
        try:
            self.archiveFlow(flow)
        except Exception as e:
            print("Exception while writing flow: " + str(e))

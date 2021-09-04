import os
import json
import copy

import pathlib
import mitmproxy

from urllib.parse import urlparse
from datetime import datetime


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
        path.mkdir(parents=True, exist_ok=True)

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

        js = json.dumps(metaDict, indent = 4)
        with open(str(DICT["path_prefix"]) + "_meta.json","w") as f:
            f.write(js)
        
        
        
    def storeContent(self, flow, DICT):

        with open(str(DICT["path_prefix"]) + "_request_body.txt","w") as f:
            f.write(flow.request.text)

        
        with open(str(DICT["path_prefix"]) + "_response_body.txt","w") as f:
            f.write(flow.response.text)
        

    def storeHeaders(self, flow, DICT):
        
        with open(str(DICT["path_prefix"]) + "_request_headers.txt","w") as f:
            for header in flow.request.headers:
                f.write(header + ": " + flow.request.headers[header])
        
        with open(str(DICT["path_prefix"]) + "_response_headers.txt","w") as f:
            for header in flow.response.headers:
                f.write(header + ": " + flow.response.headers[header])

        
    def archive(self, flow: mitmproxy.http.HTTPFlow):

        DICT = {}
        
        DICT["outputPath"] = (pathlib.Path(os.getcwd()) / "output")
        DICT["url"] = urlparse(flow.request.url)

        self.createFolder(DICT)

        print("creating folder: " + str(DICT["path"]))
        
        now = datetime.now() # current date and time
        
        date_time = now.strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]
        print("date and time:",date_time)	
        
        DICT["ts"] = date_time
        DICT["prefix"] = DICT["name"] + "-_-" + DICT["ts"] + "_"
        DICT["path_prefix"] = DICT["path"] / DICT["prefix"]

        
        self.storeMeta(flow, DICT)
        self.storeContent(flow, DICT)
        self.storeHeaders(flow, DICT)

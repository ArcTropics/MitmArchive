#Inspired by Tomnomnom's inscope implementation ;)

import re
import os
import pathlib

class RexpMatcher:


    def __init__(self, filename):
        self.filename = filename
        self.patterns=[]
        self.antipatterns=[]

        self.fileFound = self.openMatcherFile()

    def match(self, string):

        if not self.fileFound:
            return True
        
        for ap in self.antipatterns:
            if ap.match(string):
                return False

        for p in self.patterns:
            if p.match(string):
                return True

        return False


    def createMatcher(self, fd):
        for line in fd.readlines():

            isAntiPattern = False
            if line[0] == '!':
                line = line[1:]
                isAntiPattern = True

            pattern = re.compile(line[:-1])

            if isAntiPattern:
                self.antipatterns.append(pattern)
            else:
                self.patterns.append(pattern)


    def openMatcherFile(self):
        currentPath = pathlib.Path(os.getcwd()).resolve()
        homeDir = pathlib.Path(os.path.expanduser('~')).resolve()

        foundFile = False
        
        while len(str(currentPath)) >= len(str(homeDir)):

            try:
                path = str(currentPath / self.filename)
                with open(path) as f:
                    self.createMatcher(f)
                    foundFile = True
                    break
            except:
                currentPath = currentPath.parent

        return foundFile

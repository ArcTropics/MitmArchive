from subprocess import PIPE
from threading import Thread

class PipeProcessor:
    

    def __init__(self, callback, pipe):

        if callback and pipe:
        
            self.pipe = pipe
            self.callback = callback

            Thread(target=self.reader, daemon=True).start()

        
    def reader(self):

        line = ""
        buf = b' '
        while buf:
            
            buf = self.pipe.readline()

            try:
                line = buf[:-1].decode("utf-8")            
                self.callback(line)
            except:
                pass
            
    

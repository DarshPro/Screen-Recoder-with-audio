import subprocess
from threading import Thread

startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startupinfo.wShowWindow = subprocess.SW_HIDE

def listCam():
    global startupinfo
    process1 = subprocess.run(["ffmpeg.exe","-list_devices","true","-f","dshow","-i","dummy"], stdout = subprocess.PIPE, stderr = subprocess.STDOUT, startupinfo=startupinfo)
    result = str(process1.stdout).replace("\\r\\n","\n").replace("\\\\","\\")
    result = result[result.find("[dshow @"):result.find("DirectShow audio")].splitlines()
    result2 = []
    for i in result:
        if i[i.find("]")+1:].strip(" ").startswith("\""):
            result2.append(i[i.find("]")+1:].strip(" \""))
    return result2

def listMic():
    global startupinfo
    process1 = subprocess.run(["ffmpeg.exe","-list_devices","true","-f","dshow","-i","dummy"], stdout = subprocess.PIPE, stderr = subprocess.STDOUT, startupinfo=startupinfo)
    result = str(process1.stdout).replace("\\r\\n","\n").replace("\\\\","\\")
    result = result[result.find("DirectShow audio"):].splitlines()
    result2 = []
    for i in result:
        if i[i.find("]")+1:].strip(" ").startswith("\""):
            result2.append(i[i.find("]")+1:].strip(" \""))
    return result2
class capturer:
    def __init__(self, devicename):
        self.devicename = devicename
        self.captureprocess = None
    def startCapture(self,location):
        global startupinfo
        #print(self.devicename)
        self.captureprocess = subprocess.Popen(args=["ffmpeg.exe","-f","dshow","-i","video="+self.devicename+"","-y",'-c:v','mpeg4','-qscale:v','7',location],startupinfo=startupinfo)
    def stopCapture(self):
        self.captureprocess.terminate()
    def setDevice(self,devicename):
        self.devicename = devicename
if __name__ == "__main__":
    print("here be results...")
    print(listCam())
    print(listMic())
    cap = capturer(listCam()[0])
    try: 
        cap.startCapture("none.mpg")
    except KeyboardInterrupt:
        cap.stopCapture()

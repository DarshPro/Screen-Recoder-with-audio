import subprocess
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Button,Entry,Radiobutton,Checkbutton
from time import sleep
import os
import recordFile, Webcam
import webbrowser
from cmdGen import cmdGen
from sr_settings import settingsWin

class App(Tk): #the main class for the main window
    def __init__(self):
        Tk.__init__(self)

        # window properties
        self.title(string = "Screen Recorder by Darsh Sharma")
        self.iconbitmap("icon.ico")
        self.resizable(width = False, height = False)

        ffmpegAvailable = False
        for item in os.listdir():
            if item == "ffmpeg.exe":
                ffmpegAvailable = True
                break
        if not ffmpegAvailable:
            self.withdraw()
            if messagebox.askyesno("FFmpeg Not Found","ffmpeg.exe could not be found in screen recorder's directory. Do you want to be redirected to the ffmpeg download website? to pehele mera channel subscribe karo"):
                webbrowser.open_new_tab("https://www.youtube.com/channel/UCznpesyijPSg4fK082eDEow/videos")
            exit()
        self.cmdGen = cmdGen()  # create a command generator object to store settings 

        # file name
        label1 = Label(self, text="File Name:")
        label1.grid(row = 0, column = 0, sticky = "")
        self.entry1 = Entry(self)
        self.entry1.grid(row = 0, column = 1,sticky="ew")

        # ensure the existance of the "ScreenCaptures" directory
        try:
            os.mkdir("ScreenCaptures by Darsh Sharma")
        except FileExistsError:
            pass
        os.chdir("ScreenCaptures by Darsh Sharma")

        # find a default file name that is currently available.
        defaultFile = "DarshPro.mp4"
        available = False
        fileNum = 0
        while available == False:
            hasMatch = False
            for item in os.listdir():
                if item == defaultFile:
                    hasMatch = True
                    break
            if not hasMatch:
                available = True
            else:
                fileNum += 1
                defaultFile = "DarshPro"+str(fileNum)+".mp4"
        os.chdir("..")
        self.entry1.insert(END,defaultFile)

        # radio buttons determine what to record
        self.what = StringVar()
        self.what.set("desktop")
        self.radio2 = Radiobutton(self, text="record the window with the title of: ", variable=self.what, value = "title", command = self.enDis1)
        self.radio1 = Radiobutton(self, text="record the entire desktop", variable=self.what, value = "desktop", command = self.enDis)
        self.radio1.grid(row = 1, column = 0, sticky="w")
        self.radio2.grid(row = 2, column = 0, sticky = "w")
        self.entry2 = Entry(self, state=DISABLED)
        self.entry2.grid(row = 2, column = 1,sticky="ew")

        # initialize webcam
        self.webcamdevices = Webcam.listCam()
        self.webcamrecorder = Webcam.capturer("")
        
        # "record from webcam" checkbox
        self.rcchecked = IntVar()
        self.recordcam = Checkbutton(self, text="Record from webcam", command = self.checkboxChanged,variable=self.rcchecked)
        self.recordcam.grid(row = 3, column = 0)

        # a drop-down allowing you to select the webcam device from the available directshow capture devices
        self.devicename = StringVar(self)
        if self.webcamdevices:
            self.devicename.set(self.webcamdevices[0])
            self.deviceselector = OptionMenu(self, self.devicename, *self.webcamdevices)
            self.deviceselector.config(state=DISABLED)
            self.deviceselector.grid(row = 3, column = 1)
        else:
            self.devicename.set("NO DEVICES AVAILABLE")
            self.recordcam.config(state=DISABLED)
            self.deviceselector = OptionMenu(self, self.devicename, "NO DEVICES AVAILABLE")
            self.deviceselector.config(state=DISABLED)
            self.deviceselector.grid(row = 3, column = 1)
        
        self.opButton = Button(self, text="⚙ Additional Options...",command = self.openSettings)
        self.opButton.grid(row = 4, column=1, sticky='e')

        # the "start recording" button
        self.startButton = Button(self, text="⏺ Start Recording", command = self.startRecord)
        self.startButton.grid(row = 5, column = 0, columnspan = 2)


        # some variables
        self.recording = False      # are we recording?
        self.proc = None            # the popen object for ffmpeg (during screenrecord)
        self.recorder = recordFile.recorder()   # the "recorder" object for audio (see recordFile.py)
        self.mergeProcess = None    # the popen object for ffmpeg (while merging video and audio files)

        # start the ffmpeg monitoring callback
        self.pollClosed()

    def openSettings(self):
        self.settings = settingsWin(self,self.cmdGen,self.recorder)

    def pollClosed(self):
        """callback that repeats itself every 100ms. Automatically determines if ffmpeg is still running."""
        if self.recording:
            if self.proc.poll() != None:
                self.startRecord()
                messagebox.showerror("ffmpeg error","ffmpeg has stopped working. ERROR: \n"+str(self.proc.stderr.read()).replace('\\r\\n','\n'))
            if self.recorder.error:
                self.startRecord()
        if self.mergeProcess and self.recording == False:
            if self.mergeProcess.poll() != None:
                self.startButton.config(text="⏺ Start Recording", state = NORMAL)
                self.title(string = "Screen Recorder by Darsh Sharma")
        self.after(100, self.pollClosed)

    def enDis(self):
        """Called when the "desktop" radio button is pressed"""
        self.entry2.config(state=DISABLED)
        # self.what.set("desktop")

    def enDis1(self):
        """Called when the "window title" radio button is pressed"""
        self.entry2.config(state = NORMAL)
        # self.what.set("title")

    def checkboxChanged(self):
        """Called when the "record webcam" checkbox is checked or unchecked."""
        #self.rcchecked = not self.rcchecked
        if self.rcchecked.get():
            self.deviceselector.config(state = NORMAL)
        else:
            self.deviceselector.config(state = DISABLED)

    def startRecord(self):
        """toggles recording. Will start conversion subprocess on recording completion"""
        if self.recording == False:
            # change the window
            self.title(string = "Screen Recorder by Darsh Sharma (Recording...)")
            self.startButton.config(text="⏹️ Stop Recording")
            self.filename = self.entry1.get()

            # disable interface
            self.entry1.config(state = DISABLED)
            self.radio1.config(state = DISABLED)
            self.radio2.config(state = DISABLED)
            self.deviceselector.config(state = DISABLED)
            self.opButton.config(state = DISABLED)
            if self.what.get() == "title":
                self.entry2.config(state = DISABLED)

            # ensure the existence of the "tmp" directory
            try:
                os.mkdir("tmp")
            except FileExistsError:
                pass

            # start screen recording process
            self.recording = True
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # self.cmdGen.setFps(60)
            # self.cmdGen.setEncode('nvenc_h264') # CPU: mpeg4 // NVIDIA: h264_nvenc // AMD: no.
            self.cmdGen.setSource(self.what.get()=="title",self.entry2.get())
            command = self.cmdGen.getCmd("tmp/tmp.mkv")
            self.proc = subprocess.Popen(args=command, startupinfo=startupinfo)#,stderr=subprocess.PIPE)

            # start audio recording
            self.recorder.record("tmp/tmp.wav")

            # start webcam recording, if checked
            self.recordcam.config(state = DISABLED)
            if self.rcchecked.get() and self.webcamdevices:
                self.webcamrecorder.setDevice(str(self.devicename.get()))
                self.webcamrecorder.startCapture("tmp/webcamtmp.mkv")
            
            # minimize the window to get it out of the way of the recording
            self.iconify()
        elif self.recording == True:
            self.deiconify()
            defaultFile = self.filename

            # re-enable interface
            self.entry1.config(state = NORMAL)
            self.radio1.config(state = NORMAL)
            self.radio2.config(state = NORMAL)
            self.opButton.config(state = NORMAL)
            if self.webcamdevices:
                self.recordcam.config(state = NORMAL)
                if self.rcchecked.get():
                    self.deviceselector.config(state = NORMAL)
            if self.what.get() == "title":
                self.entry2.config(state = NORMAL)
            
            available = False
            fileNum = 0

            # stop all recording processes
            self.recording = False
            self.proc.terminate()
            if self.rcchecked.get() and self.webcamdevices:
                self.webcamrecorder.stopCapture()
            try:
                os.mkdir("ScreenCaptures by Darsh Sharma")
            except FileExistsError:
                pass

            # change the window title and button text to reflect the current process
            self.title(string = "Screen Recorder by Darsh Sharma (converting...)")
            self.startButton.config(text="converting your previous recording, please wait...", state = DISABLED)
            
            # start the video conversion process
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            self.cmdGen.config(audList=self.recorder.devices)
            command = self.cmdGen.getCvtCmd("ScreenCaptures by Darsh Sharma/"+self.filename)
            if not self.recorder.error:
                self.mergeProcess = subprocess.Popen(args=command)#,startupinfo=startupinfo)

            # if self.rcchecked.get():
            #     self.mergeProcess = subprocess.Popen(args= ["ffmpeg","-i",'tmp/tmp.mkv','-i','tmp/tmp.wav','-i','tmp/webcamtmp.mkv','-filter_complex','[2:v] scale=640:-1 [inner]; [0:0][inner] overlay=0:0 [out]',"-shortest",'-map','[out]','-y',"ScreenCaptures/"+self.filename])
            # else:
            #     self.mergeProcess = subprocess.Popen(args= ["ffmpeg","-i",'tmp/tmp.mkv','-i','tmp/tmp.wav',"-shortest",'-y',"ScreenCaptures/"+self.filename], startupinfo=startupinfo)

            # change the screen capture name to something that is not taken
            os.chdir("ScreenCaptures by Darsh Sharma")
            while True:
                matches = 0
                for item in os.listdir():
                    if item == defaultFile:
                        matches += 1
                if matches == 0:
                    self.entry1.delete(0,END)
                    self.entry1.insert(END,defaultFile)
                    break
                else:
                    fileNum += 1
                    file = self.filename.split(".")
                    defaultFile = file[0].rstrip("1234567890")+str(fileNum)+"."+file[1]

            os.chdir("../")

app = App()
app.mainloop()
print("DONE!")
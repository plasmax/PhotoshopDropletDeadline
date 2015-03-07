import os
import struct

from System import *
from System.Collections.Specialized import *
from System.Diagnostics import *
from System.IO import *
from System.Text.RegularExpressions import *

from FranticX.Net import *
from FranticX.Processes import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return PhotoshopDropletPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the CommandLine plugin.
######################################################################
class PhotoshopDropletPlugin( DeadlinePlugin ):

    # Photoshop Droplet Process (Pdp)
    Pdp = None
    processName = None
    CopyOnLocal = None
    isCheckFileSize = None
    CloseOnEndRender = None
    
    def __init__( self ):
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.StartJobCallback += self.StartJob
        self.RenderTasksCallback += self.RenderTasks
        self.EndJobCallback += self.EndJob
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.StartupDirectoryCallback
        del self.EndJobCallback
    
    def InitializeProcess(self):
        # Set the plugin specific settings.
        self.SingleFramesOnly = True
        self.PluginType = PluginType.Advanced
    
    def StartJob( self ):
        self.Pdp = PhotoshopDropletProcess( self )
        self.processName = Path.GetFileNameWithoutExtension( self.Pdp.executable )

        # Killing Photoshop if is already running
        if ProcessUtils.IsProcessRunning( "Photoshop.exe" ):
                self.returnError(False, "Photoshop is running on the slave - killing the process to allow renders.")
                os.system("taskkill /t /im \"Photoshop*\" /f")
                
        # Plugin options
        self.isCheckFileSize = self.GetBooleanPluginInfoEntryWithDefault( "CheckFileSize", True )
        self.CopyOnLocal = self.GetBooleanPluginInfoEntryWithDefault( "CopyOnLocal", False )
        self.CloseOnEndRender = self.GetBooleanPluginInfoEntryWithDefault( "CloseOnEndRender", True )
    
    def returnError( self, state, message ):
        if state:
            self.AbortRender("Task Failed ! " + message, ManagedProcess.AbortLevel.Fatal)
        else:
            self.LogStdout( message )
    
    ## Called by Deadline when a task is to be rendered.
    def RenderTasks( self ):
        self.LogInfo( "Render Tasks called" )
        # Check if the render frame exist
        renderFramePath = self.Pdp.RenderArgument()
        self.LogInfo(renderFramePath)
        
        if os.path.isfile(renderFramePath):
            if self.getImageWidth( renderFramePath ) < 2000:
                self.returnError(False, "Starting the process %s" % self.processName)
                            
                # Starting the process
                self.StartMonitoredManagedProcess( self.processName, self.Pdp )
                while( self.MonitoredManagedProcessIsRunning( self.processName ) ):
                    self.isBlockingPopup()
                    if self.IsCanceled():
                        self.timeout()
                
                if self.isReadyToExit(self.GetMonitoredManagedProcessExitCode(self.processName)):
                    self.LogStdout("Checking the render file size with the original file...")
                    if self.isCheckFileSize:
                        renderFileInfo = os.stat(renderFramePath)
                        self.Pdp.renderFileSize = renderFileInfo.st_size
                
                        self.checkFileSize( self.Pdp.origineFileSize, self.Pdp.renderFileSize )

                    if self.CloseOnEndRender:
                        if ProcessUtils.IsProcessRunning( "Photoshop.exe" ):
                            self.ShutdownMonitoredManagedProcess( self.processName )
                            # os.system("taskkill /t /im \"Photoshop*\" /f")
                        else:
                            self.returnError(False, "RenderTasks Photoshop droplet exited before finishing, \
                            it may have been terminated by your Droplet script")
            else:
                self.returnError(False, "The frame is larger than 2000px ! This is already a calculated cavity.")
                self.ExitWithSuccess()
        else:
            self.returnError(True, "The frame %s doesn't exist. The render is aborted !" % renderFramePath)
        
    def EndJob( self ):
        self.LogInfo("End Job called !")
        
    def isBlockingPopup ( self ):
        Popup = self.CheckForMonitoredManagedProcessPopups( self.processName )
        if ( Popup != "" ):
            self.returnError(True, "This popup was detected (%s). The render is aborted !" % Popup)
            self.ShutdownMonitoredManagedProcess( self.processName )
            self.LogStdout(str(self.MonitoredManagedProcessIsRunning( self.processName )))
                
    def isReadyToExit( self , exitCode ):
        self.LogInfo("Checking the exit code...")
        if exitCode == 0 or exitCode == 1 :
            self.LogStdout("Good, the exit code is 1!")
            return True
        else:
            self.FailRender("Error, check the exit code (%s)!" % str(exitCode))
            return False
    
    def checkFileSize( self, origineFileSize, renderFileSize ):
        if renderFileSize == origineFileSize:
            self.returnError(True,"The render file size (%(renderSize)s) and the original file size (%(originalSize)s) are the same"
            % {"renderSize": renderFileSize, "originalSize": origineFileSize})
        else:
            self.returnError(False,"The render file size (%(renderSize)s) is different of original file size (%(originalSize)s)" 
            % {"renderSize": renderFileSize, "originalSize": origineFileSize}) 
            return True
    
    def getImageWidth( self, imageFile ):
        with open(imageFile, 'rb') as f:
            data = f.read()
            w, h = struct.unpack('>LL', data[16:24])
            return int(w)
    
    def timeout(self):
        self.returnError(True, "Timeout ! Task failed. Killing process.")
        if ProcessUtils.IsProcessRunning( "Photoshop.exe" ):
            self.returnError(False, "Photoshop is running on the slave - killing the process to allow renders.")
            os.system("taskkill /t /im \"Photoshop*\" /f")
        
######################################################################
## This is the ManagedProcess class that is launched above.
######################################################################
class PhotoshopDropletProcess (ManagedProcess):

    Plugin = None
    executable = None
    origineFileSize = None
    renderFileSize = None
    startupDir = None
    
    ## Hook up the callbacks in the constructor.
    def __init__( self, plugin ):
        self.Plugin = plugin
        self.exitSuccess = False
        
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.StartupDirectoryCallback += self.StartupDirectory
        
        self.executable = self.RenderExecutable()
        self.startupDir = self.StartupDirectory()
    
    ## Clean up the managed process.
    def Cleanup():
        # Clean up stdout handler callbacks.
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.StartupDirectoryCallback

    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the ManagedProcess specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.StdoutHandling = True
        self.PopupHandling = True
        
        
        # Get the original file size before render
        origineStatInfo = os.stat(self.RenderArgument())
        self.origineFileSize = origineStatInfo.st_size
        
    def RenderExecutable( self ):
        return RepositoryUtils.CheckPathMapping(self.Plugin.GetPluginInfoEntry( "Executable" ).strip())
    
    def RenderArgument( self ):
        arguments = RepositoryUtils.CheckPathMapping(self.Plugin.GetPluginInfoEntry( "Arguments" ).strip())
        arguments = arguments.replace( "<STARTFRAME>", str(self.Plugin.GetStartFrame()) )
        arguments = arguments.replace( "<ENDFRAME>", str(self.Plugin.GetEndFrame()) )
        arguments = self.ReplacePaddedFrame( arguments, "<STARTFRAME%([0-9]+)>", self.Plugin.GetStartFrame() )
        arguments = self.ReplacePaddedFrame( arguments, "<ENDFRAME%([0-9]+)>", self.Plugin.GetEndFrame() )
        arguments = arguments.replace( "<QUOTE>", "\"" )
        return arguments
    
    def ReplacePaddedFrame( self, arguments, pattern, frame ):
        frameRegex = Regex( pattern )
        while True:
            frameMatch = frameRegex.Match( arguments )
            if frameMatch.Success:
                paddingSize = int( frameMatch.Groups[ 1 ].Value )
                if paddingSize > 0:
                    padding = StringUtils.ToZeroPaddedString( frame, paddingSize, False )
                else:
                    padding = str(frame)
                arguments = arguments.replace( frameMatch.Groups[ 0 ].Value, padding )
            else:
                break
        return arguments
    
    def StartupDirectory( self ):
        return self.Plugin.GetPluginInfoEntryWithDefault( "StartupDirectory", "" ).strip()

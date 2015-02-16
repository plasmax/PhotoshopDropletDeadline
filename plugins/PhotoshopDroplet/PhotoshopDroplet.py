import os

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
class PhotoshopDropletPlugin(DeadlinePlugin):

    # Photoshop Droplet Process (Pdp)
    Pdp = None
    processName = None 
    
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
        # processName = Path.GetFileNameWithoutExtension( Pdp.executable )
        # ProcessUtils.IsProcessRunning( processName )
        # self.Plugin.LogWarning( "Found existing %s process" % processName )
                # process = Process.GetProcessesByName( processName )[ 0 ]
        self.processName = "test"
    
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
            self.returnError(False, "Starting the process %s" % self.processName)
            
            # Starting the process
            self.RunManagedProcess(self.Pdp)
            isProcessRunning = self.MonitoredManagedProcessIsRunning(self.processName)
            if isProcessRunning:
                self.LogStdout("The process %s is running" % self.processName)
            else:
                self.returnError(True, "The process %s is not running. The render is aborted !" % self.processName)
        else:
            self.returnError(True, "The frame %s doesn't exist. The render is aborted !" % renderFramePath)
        # self.Pdp.LaunchExecutable(self.Pdp.executable, self.Pdp.arguments, self.Pdp.startupDir)
        
    def EndJob( self ):
        self.LogInfo("End Job called !")
        # theExitCode = GetMonitoredManagedProcessExitCode(self.processName)
        # ShutdownMonitoredManagedProcess( processName )
        
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
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.StartupDirectoryCallback += self.StartupDirectory
        self.TimeoutTasksCallback += self.Timeout
        self.CheckExitCodeCallback += self.CheckExitCode
        
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
        del self.TimeoutTasksCallback
        del self.CheckExitCodeCallback

    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the ManagedProcess specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.StdoutHandling = True
        self.PopupHandling = True
        self.SetUpdateTimeout( 2 )
        
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
    
    def Timeout( self ):
        self.Plugin.LogStdout("Time out ! Checking if process %s is still running" % self.Plugin.processName)
        isProcessRunning = self.Plugin.MonitoredManagedProcessIsRunning( self.Plugin.processName )
        if isProcessRunning:
            self.Plugin.returnError(True,"Task timeout ! The process %s is still running, I will kill it !" % self.Plugin.processName)
            self.ShutdownMonitoredManagedProcess( self.Plugin.processName )
        else:
            self.Plugin.returnError(True,"Task timeout ! The process %s isn't running... Call Sherlock Holmes for investigations !" % self.Plugin.processName)
        
    
    def CheckExitCode( self , exitCode ):
        self.Plugin.LogInfo("Checking the exit code")
        if exitCode == 0:
            self.Plugin.ExitWithSuccess()
        elif exitCode == 1:
            self.Plugin.LogStdout("The error code is 1. Checking the new file size")
            renderFileInfo = os.stat(self.RenderArgument())
            self.renderFileSize = renderFileInfo.st_size
            
            if self.renderFileSize == self.origineFileSize:
                self.Plugin.returnError(True,"The render file size (%(renderSize)s) and the original file size (%(originalSize)s) are the same" % {"renderSize": self.renderFileSize, "originalSize": self.origineFileSize})
            else:
                self.Plugin.returnError(False,"The render file size (%(renderSize)s) is different of original file size (%(originalSize)s)" % {"renderSize": self.renderFileSize, "originalSize": self.origineFileSize})
                self.Plugin.ExitWithSuccess()
        else:
            self.Plugin.FailRender("Error, check the exit code : ")
########################################################################
# Modeled after the Python Submitter (blame Edwin)
########################################################################

from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

from System.IO import File, StreamWriter
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global defaultLocation
    
    
    dialogWidth = 620
    dialogHeight = 500
    labelWidth = 120
    controlWidth = 152
    tabWidth = dialogWidth - 16
    defaultLocation = ""
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Photoshop Droplet Viewer Job To Deadline" )
    scriptDialog.SetIcon( Path.Combine( RepositoryUtils.GetRootDirectory(), "plugins/PhotoshopDroplet/PhotoshopDroplet.ico" ) )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "JobOptionsSeparator", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 3, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 5, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 6, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 6, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 7, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 8, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 9, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 9, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 9, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Photoshop Droplet Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "ExecutableLabel", "LabelControl", "Photoshop Droplet Executable", 4, 0, "The Photoshop Droplet Executable to use for rendering.", False )
    scriptDialog.AddSelectionControlToGrid( "ExecBox", "FileBrowserControl", "", "Executables (*.exe)", 4, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "StartupLabel", "LabelControl", "Start Up Folder (optional)", 5, 0, "The directory that the command line will start up in.", False )
    scriptDialog.AddSelectionControlToGrid( "StartupBox", "FolderBrowserControl", "","", 5, 1, colSpan=3, browserLocation=defaultLocation)
    
    scriptDialog.AddControlToGrid( "ArgsLabel", "LabelControl", "Arguments", 6, 0, "The command line arguments to be submitted." )
    scriptDialog.AddControlToGrid( "ArgsBox", "TextControl", "", 6, 1, colSpan=3 )  

    scriptDialog.AddControlToGrid("SpacerLabel","LabelControl", "Argument Tags", 7, 0, "Use these buttons to add tags to the arguments.", False )
    startFButton = scriptDialog.AddControlToGrid("StartFButton","ButtonControl", "Start Frame Tag", 7, 1, 'Adds a Start Frame tag to the arguments.' )
    endFButton = scriptDialog.AddControlToGrid("EndFButton","ButtonControl", "End Frame Tag", 7, 2, 'Adds an End Frame tag to the arguments.' )
    quoteButton = scriptDialog.AddControlToGrid("QuoteButton","ButtonControl", "Quote Tag", 7, 3, 'Adds a Quote tag to the arguments.' )

    scriptDialog.AddControlToGrid("FramePaddingLabel","LabelControl", "Frame Tag Padding", 8, 0, "Controls the amount of frame padding for the Start Frame and End Frame tags.", False )
    scriptDialog.AddRangeControlToGrid( "FramePaddingBox", "RangeControl", 0, 0, 10, 0, 1, 8, 1 )
    
    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 9, 0, "The list of frames for the normal job.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 9, 1 )
    
    getFramesButton = scriptDialog.AddControlToGrid( "getFramesButton", "ButtonControl", "Get Frame List from arguments", 9, 2, colSpan=2 )
    
    scriptDialog.EndGrid() 

    startFButton.ValueModified.connect(startFPressed)
    endFButton.ValueModified.connect(endFPressed)
    quoteButton.ValueModified.connect(quotePressed)    
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","IsBlacklistBox","MachineListBox",
    "LimitGroupBox","ExecBox","StartupBox","FramesBox","ArgsBox","VersionBox","SubmitSceneBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    scriptDialog.ShowDialog( False )
 
def startFPressed( *args ):
    global scriptDialog
    
    currentText = scriptDialog.GetValue( "ArgsBox" )
    
    frameTag = "<STARTFRAME"
    
    padding = scriptDialog.GetValue( "FramePaddingBox" )
    if padding > 0:
        frameTag += "%" + str(padding)
        
    frameTag += ">"
    
    currentText += frameTag
    scriptDialog.SetValue( "ArgsBox", currentText ) 
    
def endFPressed( *args ):
    global scriptDialog
    
    currentText = scriptDialog.GetValue( "ArgsBox" )
    
    frameTag = "<ENDFRAME"
    
    padding = scriptDialog.GetValue( "FramePaddingBox" )
    if padding > 0:
        frameTag += "%" + str(padding)
        
    frameTag += ">"
    
    currentText += frameTag
    scriptDialog.SetValue( "ArgsBox", currentText )
    
def quotePressed( *args ):
    global scriptDialog
    
    currentText = scriptDialog.GetValue( "ArgsBox" ) 
    currentText += "<QUOTE>"
    scriptDialog.SetValue( "ArgsBox", currentText ) 
 
def GetSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "PhotoshopDropletSettings.ini" )
    
def SubmitButtonPressed(*args):
    global scriptDialog
    
    # Check if executable file exists.
    execFile = scriptDialog.GetValue( "ExecBox" )
    if( not File.Exists( execFile ) ):
        scriptDialog.ShowMessageBox( "The executable {0} does not exist".format(execFile), "Error" )
        return
    elif (PathUtils.IsPathLocal(execFile)):
        result = scriptDialog.ShowMessageBox( "The executable file {0} is local. Are you sure you want to continue?".format(execFile), "Warning", ("Yes","No") )
        if(result=="No"):
            return
    
    # Create job info file.
    jobInfoFilename = Path.Combine( GetDeadlineTempPath(), "photoshopdroplet_job_info.job" )
    #scriptDialog.ShowMessageBox(str(jobInfoFilename), "")
    try:
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode ) #<- this is the line messing up
    except Exception, e:
        scriptDialog.ShowMessageBox("error: " + str(e) , "")
    
    writer.WriteLine( "Plugin=PhotoshopDroplet" )
    writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
    writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
    writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
    writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
    writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
    writer.WriteLine( "Frames=%s" % scriptDialog.GetValue( "FramesBox" ) )
    writer.WriteLine( "ChunkSize=1" )
    
    if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
        writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    else:
        writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )
    writer.Close()
    
    # Create plugin info file. Empty for now.
    pluginInfoFilename = Path.Combine( GetDeadlineTempPath(), "photoshopdroplet_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
  
    writer.WriteLine( "Arguments=%s" % scriptDialog.GetValue( "ArgsBox" ) )
    writer.WriteLine( "Executable=%s" % scriptDialog.GetValue( "ExecBox" ) )
    writer.WriteLine( "StartupDirectory=%s" % scriptDialog.GetValue( "StartupBox" ) )

    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    arguments.Add( execFile )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )

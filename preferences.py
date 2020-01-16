import bpy
import platform

from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

nodeUpdateItems = {
    ("EACH", "on each message", "Node Tree is executed on each message (ideal for low frequency messages)", "NONE", 0),
    ("MESSAGE", "on specific message", "Node Tree is executed on a specific message (ideal for high frequency messages)", "NONE", 1) }

class NodeOSCEnvVarSettings(bpy.types.PropertyGroup):
    udp_in: bpy.props.StringProperty(default="127.0.0.1", description='The IP of the interface of your Blender machine to listen on, set to 0.0.0.0 for all of them')
    udp_out: bpy.props.StringProperty(default="127.0.0.1", description='The IP of the destination machine to send messages to')
    port_in: bpy.props.IntProperty(default=9001, min=0, max=65535, description='The input network port (0-65535)')
    port_out: bpy.props.IntProperty(default=9002, min=0, max= 65535, description='The output network port (0-65535)')
    input_rate: bpy.props.IntProperty(default=0 ,description="The refresh rate of checking for input messages (millisecond)", min=0)
    output_rate: bpy.props.IntProperty(default=40 ,description="The refresh rate of sending output messages (millisecond)", min=1)
    isServerRunning: bpy.props.BoolProperty(default=False, description='Show if the engine is running or not')
    message_monitor: bpy.props.BoolProperty(description="Display the current value of your keys, the last message received and some infos in console")
    autorun: bpy.props.BoolProperty(description="Start the OSC engine automatically after loading a project. IMPORTANT: This only works if the project is saved while the server is NOT running!")
    lastaddr: bpy.props.StringProperty(description="Display the last OSC address received")
    lastpayload: bpy.props.StringProperty(description="Display the last OSC message content")
    node_update: bpy.props.EnumProperty(name = "node update", default = "EACH", items = nodeUpdateItems)
    node_frameMessage: bpy.props.StringProperty(default="/frame/end",description="OSC message that triggers a node tree execution")
    error: bpy.props.StringProperty(default="",description="Last error message")

class NodeOSCPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    usePyLiblo: BoolProperty(
            name="Use PyLiblo library. Currently only supported on OSX and Windows",
            default=False,
            )

    def draw(self, context):
        prefs = context.preferences
        view = prefs.view

        layout = self.layout
        if platform.system() != "Linux":
            layout.prop(self, "usePyLiblo")
            
        layout.label(text="Helpfull to get full data paths is to enable python tool tips:")
        layout.prop(view, "show_tooltips_python")
        layout.label(text="Use Ctrl-Alt-Shift-C to copy the full datapath to the clipboard")

def register():
    bpy.utils.register_class(NodeOSCEnvVarSettings)
    bpy.utils.register_class(NodeOSCPreferences)
    bpy.types.Scene.nodeosc_envars = bpy.props.PointerProperty(type=NodeOSCEnvVarSettings)

def unregister():
    del bpy.types.Scene.nodeosc_envars
    bpy.utils.unregister_class(NodeOSCPreferences)
    bpy.utils.unregister_class(NodeOSCEnvVarSettings)

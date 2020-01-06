
import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

class NodeOSCEnvVarSettings(bpy.types.PropertyGroup):
    nodeosc_udp_in: bpy.props.StringProperty(default="127.0.0.1", description='The IP of the interface of your Blender machine to listen on, set to 0.0.0.0 for all of them')
    nodeosc_udp_out: bpy.props.StringProperty(default="127.0.0.1", description='The IP of the destination machine to send messages to')
    nodeosc_port_in: bpy.props.IntProperty(default=9001, min=0, max=65535, description='The input network port (0-65535)')
    nodeosc_port_out: bpy.props.IntProperty(default=9002, min=0, max= 65535, description='The output network port (0-65535)')
    nodeosc_rate: bpy.props.IntProperty(default=10 ,description="The refresh rate of the engine (millisecond)", min=1)
    status: bpy.props.StringProperty(default="Stopped", description='Show if the engine is running or not')
    nodeosc_monitor: bpy.props.BoolProperty(description="Display the current value of your keys, the last message received and some infos in console")
    nodeosc_autorun: bpy.props.BoolProperty(description="Start the OSC engine automatically after loading a project")
    nodeosc_lastaddr: bpy.props.StringProperty(description="Display the last OSC address received")
    nodeosc_lastpayload: bpy.props.StringProperty(description="Display the last OSC message content")

class NodeOSCPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    usePyLiblo: BoolProperty(
            name="Use PyLiblo library",
            default=False,
            )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Preferences for NodeOSC")
        layout.prop(self, "usePyLiblo")

def register():
    print("done that")
    bpy.utils.register_class(NodeOSCEnvVarSettings)
    bpy.utils.register_class(NodeOSCPreferences)
    bpy.types.Scene.NodeOSC_envVars = bpy.props.PointerProperty(type=NodeOSCEnvVarSettings)

def unregister():
    del bpy.types.Scene.NodeOSC_envVars
    bpy.utils.unregister_class(NodeOSCPreferences)
    bpy.utils.unregister_class(NodeOSCEnvVarSettings)

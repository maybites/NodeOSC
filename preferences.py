
import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

class NodeOSCEnvVarSettings(bpy.types.PropertyGroup):
        #key_path = bpy.props.StringProperty(name="Key", default="Unknown")
        address: bpy.props.StringProperty(name="Address", default="")
        data_path: bpy.props.StringProperty(name="Data path", default="")
        id: bpy.props.StringProperty(name="ID", default="")
        osc_type: bpy.props.StringProperty(name="Type", default="Unknown")
        osc_index: bpy.props.StringProperty(name="Type", default="Unknown")
        value: bpy.props.StringProperty(name="Value", default="Unknown")
        idx: bpy.props.IntProperty(name="Index", min=0, default=0)

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


def unregister():
    bpy.utils.unregister_class(NodeOSCPreferences)
    bpy.utils.unregister_class(NodeOSCEnvVarSettings)

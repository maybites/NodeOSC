import bpy

from ..utils.utils import *

class NodeOSCMsgValues(bpy.types.PropertyGroup):
        #key_path = bpy.props.StringProperty(name="Key", default="Unknown")
        osc_address: bpy.props.StringProperty(name="address", default="/custom")
        osc_type: bpy.props.StringProperty(name="Type", default="f")
        osc_index: bpy.props.StringProperty(name="Argument indices. Indicate in which order the arriving arguments will be handled inside blender. Have to be in the format \'(0 [, 1, 2])\' with at least one integer, separated by a comma, and inside two parantheses(). There should be no more indices than arriving arguments, otherwise the message will be ignored", default="(0))")
        osc_direction: bpy.props.EnumProperty(name = "RX/TX", default = "INPUT", items = dataDirectionItems)
        data_path: bpy.props.StringProperty(name="Datapath. Use Ctrl-Alt-Shift-C to copy the full datapath from your property you desire to controll to the clipboard, remove the property name (after the last dot) and set it inside Property", default="")
        id: bpy.props.StringProperty(name="Property", default="")
        value: bpy.props.StringProperty(name="value", default="Unknown")
        idx: bpy.props.IntProperty(name="Index", min=0, default=0)
        enabled: bpy.props.BoolProperty(name="Enabled", default=True)
        ui_expanded: bpy.props.BoolProperty(name="Expanded", default=False)  

key_classes = (
    NodeOSCMsgValues,
)

def register():
    for cls in key_classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.OSC_keys = bpy.props.CollectionProperty(type=NodeOSCMsgValues)
    bpy.types.Scene.OSC_keys_tmp = bpy.props.CollectionProperty(type=NodeOSCMsgValues)
    bpy.types.Scene.OSC_nodes = bpy.props.CollectionProperty(type=NodeOSCMsgValues)


def unregister():
    del bpy.types.Scene.OSC_keys
    del bpy.types.Scene.OSC_nodes
    del bpy.types.Scene.OSC_keys_tmp
    for cls in reversed(key_classes):
        bpy.utils.unregister_class(cls)



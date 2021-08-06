import bpy

from .utils import *

class NodeOSCMsgValues(bpy.types.PropertyGroup):
        #key_path = bpy.props.StringProperty(name="Key", default="Unknown")
        osc_address: bpy.props.StringProperty(name="OSC Address", default="/custom")
        osc_type: bpy.props.StringProperty(name="Type", default="f")
        osc_index: bpy.props.StringProperty(name="Argument indices.", description = "Indicate in which order the arriving arguments will be applied. Have to be in the format \'() or (0 [, 1, 2])\' with 0...n integers, separated by a comma, and inside two parantheses \'()\'. There should be no more indices than arriving arguments, otherwise the message will be ignored", default="())")
        osc_direction: bpy.props.EnumProperty(name = "RX/TX", default = "INPUT", items = dataDirectionItems)
        filter_repetition: bpy.props.BoolProperty(name = "Filter argument repetition", default = False, description = "Avoid sending messages with repeating arguments")
        dp_format_enable: bpy.props.BoolProperty(name = "Format", default = False, description = "enable realtime evaluation of datapath with python string-format functionality")
        dp_format: bpy.props.StringProperty(name="Format", default="args", description = "enter the format values separated by commas. available keywords: array 'args' for all arguments, 'length' for args length, 'index' if loop is enabled" )
        loop_enable: bpy.props.BoolProperty(name = "Loop", default = False, description = "enable looping through the arguments")
        loop_range: bpy.props.StringProperty(name="Range", default="0, length, 1", description = "enter the range values for the loop. Maximal 3 values, separated by commas. Default: first value = start index, second value = end index, third value = step. Available keywords: 'args' for all arguments, 'length' for args length")
        filter_enable: bpy.props.BoolProperty(name = "Filter arguments", default = False, description = "enable filtering of incomming messages based on the incomming arguments")
        filter_eval: bpy.props.StringProperty(name="Argument evaluation", default="args[0] == 'string' or args[1] == 0", description = "the filter condition to be evaluated. The result of the evaluated condition must be a 'true' or 'false'. Available keywords: array 'args' for all incomming arguments. BE AWARE: 'Filter repetition' should be disabled to guarrantee work properly")
        data_path: bpy.props.StringProperty(name="Datapath", description = "Use Ctrl-Alt-Shift-C to copy-paste the full datapath from your property you desire to controll", default="bpy.data.objects['Cube']")
        props: bpy.props.StringProperty(name="Property", default="", description = "NOT USED ANYMORE")
        value: bpy.props.StringProperty(name="value", default="Unknown")
        idx: bpy.props.IntProperty(name="Index", min=0, default=0)
        enabled: bpy.props.BoolProperty(name="Enabled", default=True)
        ui_expanded: bpy.props.BoolProperty(name="Expanded", default=True)
        node_data_type: bpy.props.EnumProperty(name = "Node data type", default = "LIST", items = nodeDataTypeItems)
        node_type: bpy.props.IntProperty(name = "Node type", default = 0)

key_classes = (
    NodeOSCMsgValues,
)

def register():
    for cls in key_classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.NodeOSC_keys = bpy.props.CollectionProperty(type=NodeOSCMsgValues, description='collection of custom osc handler')
    bpy.types.Scene.NodeOSC_keys_tmp = bpy.props.CollectionProperty(type=NodeOSCMsgValues)
    bpy.types.Scene.NodeOSC_nodes = bpy.props.CollectionProperty(type=NodeOSCMsgValues, description='collection of all osc handler that are created by nodes')
    bpy.types.Scene.NodeOSC_outputs = bpy.props.CollectionProperty(type=NodeOSCMsgValues, description='collection of all osc handler that send messages to output')


def unregister():
    del bpy.types.Scene.NodeOSC_outputs
    del bpy.types.Scene.NodeOSC_keys
    del bpy.types.Scene.NodeOSC_nodes
    del bpy.types.Scene.NodeOSC_keys_tmp
    for cls in reversed(key_classes):
        bpy.utils.unregister_class(cls)



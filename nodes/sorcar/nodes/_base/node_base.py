import bpy

import platform

if platform.system() == "Windows":
    from sorcar.nodes._base.node_base import ScNode
else:
    from Sorcar.nodes._base.node_base import ScNode
    
from .....utils.utils import *

def sorcarTreeUpdate(self, context):
    bpy.context.scene.nodeosc_SORCAR_needsUpdate = True

class ScOSCNode(ScNode):

    osc_address: bpy.props.StringProperty(name="Osc address", 
        default="/sorcar/number")
    osc_type: bpy.props.StringProperty(
        name="Type", 
        default="fff")
    osc_index: bpy.props.StringProperty(
        name="Argument indices. Indicate in which order the arguments will be handled inside blender. Have to be in the format \'() or (0 [, 1, 2])\' with 0...n integers, separated by a comma, and inside two parantheses \'()\'. There should be no more indices than arriving arguments, otherwise the message will be ignored", 
        default="()")
    osc_direction: bpy.props.EnumProperty(
        name = "RX/TX", 
        default = "INPUT", 
        items = dataNodeDirectionItems)
    data_path: bpy.props.StringProperty(
        name="data path", 
        default="")
    id: bpy.props.StringProperty(
        name="id", 
        default="setValue")
    node_data_type: bpy.props.EnumProperty(
        name="NodeDataType", 
        default="SINGLE", 
        items = nodeDataTypeItems)
    node_type: bpy.props.IntProperty(
        name="NodeType", 
        default=2)
     
    def init(self, context):
        super().init(context)
        self.data_path = 'bpy.data.node_groups[\'' + self.id_data.name + '\'].nodes[\'' + self.name +'\']'
    
    def draw_buttons(self, context, layout):
        super().draw_buttons(context, layout)
        envars = bpy.context.scene.nodeosc_envars
        layout.enabled = not envars.isServerRunning

    def error_condition(self):
        return (
            super().error_condition()
        )
    
    def update_value(self, context):
        if context.space_data is not None:
            super().update_value(context)
        else:
            sorcarTreeUpdate(self, context)
        return None

    def post_execute(self):
        return super().post_execute()
    
    def setValue(self, value):
        self.post_execute()

    def getValue(self):
        pass

    @property
    def value(self):
        return self.getValue()

    @value.setter
    def value(self, value):
        self.setValue(value)

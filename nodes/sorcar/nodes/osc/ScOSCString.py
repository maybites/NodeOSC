import bpy

from bpy.props import StringProperty
from bpy.types import Node
from Sorcar.nodes._base.node_base import ScNode

from .....utils.utils import *

class ScOSCString(Node, ScNode):
    bl_idname = "ScOSCString"
    bl_label = "OSCString"

    prop_string: StringProperty(name="String", update=ScNode.update_value)

    osc_address: bpy.props.StringProperty(name="Osc address", 
        default="/sorcar/string")
    osc_type: bpy.props.StringProperty(
        name="Type", 
        default="fff")
    osc_index: bpy.props.StringProperty(
        name="Argument indices. Indicate in which order the arguments will be handled inside blender. Have to be in the format \'() or (0 [, 1, 2])\' with 0...n integers, separated by a comma, and inside two parantheses \'()\'. There should be no more indices than arriving arguments, otherwise the message will be ignored", 
        default="()")
    osc_direction: bpy.props.EnumProperty(
        name = "RX/TX", 
        default = "INPUT", 
        items = dataDirectionItems)
    data_path: bpy.props.StringProperty(
        name="data path", 
        default="")
    id: bpy.props.StringProperty(
        name="id", 
        default="")
    node_data_type: bpy.props.EnumProperty(
        name="NodeDataType", 
        default="FLOAT", 
        items = nodeDataTypeItems)
    node_type: bpy.props.IntProperty(
        name="NodeType", 
        default=2)
       
    def post_execute(self):
        return {"Value": self.prop_string}

     
    def init(self, context):
        super().init(context)
        #self.inputs.new("ScNodeSocketBool", "Random").init("in_random", True)
        #self.inputs.new("ScNodeSocketNumber", "Seed").init("in_seed")
        #self.outputs.new("ScNodeSocketNumber", "Value")
        
        self.data_path = 'bpy.data.node_groups[\'' + self.id_data.name + '\'].nodes[\'' + self.name +'\']'
        
        if self.osc_direction == "OUTPUT":
            self.id = "value"
        if self.osc_direction == "INPUT":
            self.id = "setValue"

        self.outputs.new("ScNodeSocketString", "Value")
    
    def draw_buttons(self, context, layout):
        super().draw_buttons(context, layout)
        layout.prop(self, "prop_string")
        layout.prop(self, "osc_address", text="")
        layout.prop(self, "osc_index", text="")
        #layout.prop(self, "osc_direction", text="")

    def error_condition(self):
        return (
            super().error_condition()
        )
    
    def post_execute(self):
        out = {}
        out["Value"] = self.prop_string
        return out
    
    def setValue(self, value):
        self.prop_string = value
        bpy.context.scene.nodeosc_SORCAR_needsUpdate = True
        self.post_execute()

    def getValue(self):
        return self.prop_string

    @property
    def value(self):
        return self.getValue()

    @value.setter
    def value(self, value):
        self.setValue(value)

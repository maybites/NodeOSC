import bpy
import numpy

from bpy.props import EnumProperty, FloatProperty, IntProperty, BoolProperty, StringProperty
from bpy.types import Node
from Sorcar.nodes._base.node_base import ScNode
from numpy import array, uint32

from .....utils.utils import *

class ScOSCNumber(Node, ScNode):
    bl_idname = "ScOSCNumber"
    bl_label = "OSCNumber"

    prop_type: EnumProperty(name="Type", items=[("FLOAT", "Float", ""), ("INT", "Integer", ""), ("ANGLE", "Angle", "")], default="FLOAT", update=ScNode.update_value)
    prop_float: FloatProperty(name="Float")
    prop_int: IntProperty(name="Integer")
    prop_angle: FloatProperty(name="Angle", unit="ROTATION")

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
     
    def init(self, context):
        super().init(context)
        #self.inputs.new("ScNodeSocketBool", "Random").init("in_random", True)
        #self.inputs.new("ScNodeSocketNumber", "Seed").init("in_seed")
        #self.outputs.new("ScNodeSocketNumber", "Value")
        
        self.data_path = 'bpy.data.node_groups[\'' + self.id_data.name + '\'].nodes[\'' + self.name +'\']'
        
        if self.osc_direction == "OUTPUT":
            self.id = "value"
            self.inputs.new("ScNodeSocketNumber", "Value")
        if self.osc_direction == "INPUT":
            self.id = "setValue"
            self.outputs.new("ScNodeSocketNumber", "Value")
    
    def draw_buttons(self, context, layout):
        super().draw_buttons(context, layout)
        #if (not self.inputs["Random"].default_value):
        layout.prop(self, "prop_type", expand=True)
        layout.prop(self, "osc_address", text="")
        layout.prop(self, "osc_index", text="")
        #layout.prop(self, "osc_direction", text="")

    def error_condition(self):
        return (
            super().error_condition()
        )
    
    def post_execute(self):
        out = {}
        if (self.prop_type == "FLOAT"):
            out["Value"] = self.prop_float
        elif (self.prop_type == "INT"):
            out["Value"] = self.prop_int
        elif (self.prop_type == "ANGLE"):
            out["Value"] = self.prop_angle
        return out
    
    def setValue(self, value):
        if (self.prop_type == "FLOAT"):
            self.prop_float = value
        elif (self.prop_type == "INT"):
            self.prop_int = value
        elif (self.prop_type == "ANGLE"):
            self.prop_angle = value
        self.post_execute()

    def getValue(self):
        if (self.prop_type == "FLOAT"):
            return self.prop_float
        elif (self.prop_type == "INT"):
            return self.prop_int
        elif (self.prop_type == "ANGLE"):
            return self.prop_angle

    @property
    def value(self):
        return self.getValue()

    @value.setter
    def value(self, value):
        self.setValue(value)

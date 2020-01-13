import bpy
import mathutils

from bpy.props import EnumProperty, FloatProperty
from bpy.types import Node
from mathutils import Vector
from Sorcar.nodes._base.node_base import ScNode

from .....utils.utils import *

def sorcarTreeUpdate(self, context):
    bpy.context.scene.nodeosc_SORCAR_needsUpdate = True

class ScOSCVector(Node, ScNode):
    bl_idname = "ScOSCVector"
    bl_label = "OSCVector"

    in_uniform: EnumProperty(items=[("NONE", "None", "-"), ("XY", "XY", "-"), ("YZ", "YZ", "-"), ("XZ", "XZ", "-"), ("XYZ", "XYZ", "-")], default="NONE", update=sorcarTreeUpdate)
    in_x: FloatProperty(update=sorcarTreeUpdate)
    in_y: FloatProperty(update=sorcarTreeUpdate)
    in_z: FloatProperty(update=sorcarTreeUpdate)

    osc_address: bpy.props.StringProperty(name="Osc address", 
        default="/sorcar/vector")
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
        default="TUPLE", 
        items = nodeDataTypeItems)
    node_type: bpy.props.IntProperty(
        name="NodeType", 
        default=2)
    
    def init(self, context):
        super().init(context)
        self.inputs.new("ScNodeSocketString", "Uniform").init("in_uniform")
        self.inputs.new("ScNodeSocketNumber", "X").init("in_x", True)
        self.inputs.new("ScNodeSocketNumber", "Y").init("in_y", True)
        self.inputs.new("ScNodeSocketNumber", "Z").init("in_z", True)
        
        self.data_path = 'bpy.data.node_groups[\'' + self.id_data.name + '\'].nodes[\'' + self.name +'\']'
        
        if self.osc_direction == "OUTPUT":
            self.id = "value"
        if self.osc_direction == "INPUT":
            self.id = "setValue"

        self.outputs.new("ScNodeSocketVector", "Value")
    
    def error_condition(self):
        return (
            not self.inputs["Uniform"].default_value in ["NONE", "XY", "YZ", "XZ", "XYZ"]
        )
    
    def post_execute(self):
        out = {}
        if (self.inputs["Uniform"].default_value == "NONE"):
            out["Value"] = Vector((self.inputs["X"].default_value, self.inputs["Y"].default_value, self.inputs["Z"].default_value))
        elif (self.inputs["Uniform"].default_value == "XY"):
            out["Value"] = Vector((self.inputs["X"].default_value, self.inputs["X"].default_value, self.inputs["Z"].default_value))
        elif (self.inputs["Uniform"].default_value == "YZ"):
            out["Value"] = Vector((self.inputs["X"].default_value, self.inputs["Y"].default_value, self.inputs["Y"].default_value))
        elif (self.inputs["Uniform"].default_value == "XZ"):
            out["Value"] = Vector((self.inputs["X"].default_value, self.inputs["Y"].default_value, self.inputs["X"].default_value))
        elif (self.inputs["Uniform"].default_value == "XYZ"):
            out["Value"] = Vector((self.inputs["X"].default_value, self.inputs["X"].default_value, self.inputs["X"].default_value))
        return out
    
    def draw_buttons(self, context, layout):
        super().draw_buttons(context, layout)
        #if (not self.inputs["Random"].default_value):
        layout.prop(self, "osc_address", text="")
        layout.prop(self, "osc_index", text="")
        #layout.prop(self, "osc_direction", text="")

    def error_condition(self):
        return (
            super().error_condition()
        )
    
    def setValue(self, value):
        if len(value) > 0:
            self.in_x = value[0]
        if len(value) > 1:
            self.in_y = value[1]
        if len(value) > 2:
            self.in_z = value[2]
        self.post_execute()

    def getValue(self):
        return post_execute()["Value"]

    @property
    def value(self):
        return self.getValue()

    @value.setter
    def value(self, value):
        self.setValue(value)
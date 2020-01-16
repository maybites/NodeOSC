import bpy
import mathutils

from bpy.props import EnumProperty, FloatProperty
from bpy.types import Node
from mathutils import Vector
from .._base.node_base import *

from .....utils.utils import *

class ScOSCVector(Node, ScOSCNode):
    bl_idname = "ScOSCVector"
    bl_label = "OSCVector"

    in_uniform: EnumProperty(items=[("NONE", "None", "-"), ("XY", "XY", "-"), ("YZ", "YZ", "-"), ("XZ", "XZ", "-"), ("XYZ", "XYZ", "-")], default="NONE", update=ScOSCNode.update_value)
    in_x: FloatProperty(update=ScOSCNode.update_value)
    in_y: FloatProperty(update=ScOSCNode.update_value)
    in_z: FloatProperty(update=ScOSCNode.update_value)
   
    def init(self, context):
        super().init(context)
        self.inputs.new("ScNodeSocketString", "Uniform").init("in_uniform")
        self.inputs.new("ScNodeSocketNumber", "X").init("in_x", True)
        self.inputs.new("ScNodeSocketNumber", "Y").init("in_y", True)
        self.inputs.new("ScNodeSocketNumber", "Z").init("in_z", True)
        
        self.osc_address = "/sorcar/vector"
        self.node_data_type = "LIST"
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
        layout.prop(self, "osc_address", text="")
        layout.prop(self, "osc_index", text="")

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

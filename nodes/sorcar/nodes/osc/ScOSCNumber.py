import bpy
import numpy

from bpy.props import EnumProperty, FloatProperty, IntProperty, BoolProperty, StringProperty
from bpy.types import Node
from .._base.node_base import *
from numpy import array, uint32

from .....utils.utils import *

class ScOSCNumber(Node, ScOSCNode):
    bl_idname = "ScOSCNumber"
    bl_label = "OSCNumber"

    prop_type: EnumProperty(name="Type", items=[("FLOAT", "Float", ""), ("INT", "Integer", ""), ("ANGLE", "Angle", "")], default="FLOAT", update=ScOSCNode.update_value)
    prop_float: FloatProperty(name="Float", update=ScOSCNode.update_value)
    prop_int: IntProperty(name="Integer", update=ScOSCNode.update_value)
    prop_angle: FloatProperty(name="Angle", unit="ROTATION", update=ScOSCNode.update_value)
  
    def init(self, context):
        super().init(context)
        self.outputs.new("ScNodeSocketNumber", "Value")
    
    def draw_buttons(self, context, layout):
        super().draw_buttons(context, layout)
        #if (not self.inputs["Random"].default_value):
        layout.prop(self, "prop_type", expand=True)
        if (self.prop_type == "FLOAT"):
            layout.prop(self, "prop_float")
        elif (self.prop_type == "INT"):
            layout.prop(self, "prop_int")
        elif (self.prop_type == "ANGLE"):
            layout.prop(self, "prop_angle")
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

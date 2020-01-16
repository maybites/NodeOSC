import bpy

from bpy.props import StringProperty
from bpy.types import Node
from .._base.node_base import *

from .....utils.utils import *

class ScOSCString(Node, ScOSCNode):
    bl_idname = "ScOSCString"
    bl_label = "OSCString"

    prop_string: StringProperty(name="String", update=ScOSCNode.update_value)
            
    def init(self, context):
        super().init(context)       
        self.osc_address = "/sorcar/string"
        self.node_data_type = "LIST"
        self.outputs.new("ScNodeSocketString", "Value")
    
    def draw_buttons(self, context, layout):
        super().draw_buttons(context, layout)
        layout.prop(self, "prop_string", text="")
        layout.prop(self, "osc_address", text="")
        layout.prop(self, "osc_index", text="")

    
    def post_execute(self):
        out = {}
        out["Value"] = self.prop_string
        return out
    
    def setValue(self, value):
        self.prop_string = value
        self.post_execute()

    def getValue(self):
        return self.prop_string

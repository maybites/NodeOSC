import bpy

from bpy.props import StringProperty
from bpy.types import Node
from Sorcar.nodes._base.node_base import ScNode

class ScOSCString(Node, ScNode):
    bl_idname = "ScOSCString"
    bl_label = "OSCString"

    prop_string: StringProperty(name="String", update=ScNode.update_value)

    def init(self, context):
        super().init(context)
        self.outputs.new("ScNodeSocketString", "Value")
    
    def draw_buttons(self, context, layout):
        super().draw_buttons(context, layout)
        layout.prop(self, "prop_string")
    
    def post_execute(self):
        return {"Value": self.prop_string}
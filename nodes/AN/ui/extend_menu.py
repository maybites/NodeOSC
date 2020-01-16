import bpy
from bpy.props import *
from animation_nodes.utils.operators import makeOperator
from animation_nodes.sockets.info import getBaseDataTypes
from animation_nodes.tree_info import getSubprogramNetworks
from animation_nodes.utils.nodes import getAnimationNodeTrees

mainBaseDataTypes = ("Object", "Integer", "Float", "Vector", "Text")
numericalDataTypes = ("Matrix", "Vector", "Float", "Color", "Euler", "Quaternion")

def drawMenu(self, context):
    if context.space_data.tree_type != "an_AnimationNodeTree": return

    layout = self.layout
    layout.operator_context = "INVOKE_DEFAULT"
    layout.separator()
    layout.menu("AN_MT_OSC_menu", text = "OSC", icon = "LINENUMBERS_ON")
 
class OSCMenu(bpy.types.Menu):
    bl_idname = "AN_MT_OSC_menu"
    bl_label = "OSC Menu"

    def draw(self, context):
        layout = self.layout
        insertNode(layout, "an_OSCListNode", "List", {"assignedType" : repr("List")})
        insertNode(layout, "an_OSCNumberNode", "Number", {"assignedType" : repr("Number")})
        layout.separator()
 
def insertNode(layout, type, text, settings = {}, icon = "NONE"):
    operator = layout.operator("node.add_node", text = text, icon = icon)
    operator.type = type
    operator.use_transform = True
    for name, value in settings.items():
        item = operator.settings.add()
        item.name = name
        item.value = value
    return operator

def register():
    bpy.types.NODE_MT_add.append(drawMenu)

def unregister():
    bpy.types.NODE_MT_add.remove(drawMenu)

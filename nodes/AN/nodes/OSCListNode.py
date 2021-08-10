import bpy
import ast
from bpy.props import *
from collections import defaultdict
from animation_nodes.sockets.info import toIdName
from animation_nodes.base_types import AnimationNode
from animation_nodes.data_structures import DoubleList

from ....utils.utils import *

dataByIdentifier = defaultdict(None)

class OSCListNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_OSCListNode"
    bl_label = "OSCList"
    
    osc_address: bpy.props.StringProperty(name="Osc address", 
        default="/an/list", 
        update = AnimationNode.refresh)
    osc_type: bpy.props.StringProperty(
        name="Type", 
        default="fff")
    osc_index: bpy.props.StringProperty(
        name="Argument indices. Indicate in which order the arguments will be handled inside blender. Have to be in the format \'() or (0 [, 1, 2])\' with 0...n integers, separated by a comma, and inside two parantheses \'()\'. There should be no more indices than arriving arguments, otherwise the message will be ignored", 
        default="()",
        update = AnimationNode.refresh)
    osc_direction: bpy.props.EnumProperty(
        name = "RX/TX", 
        default = "INPUT", 
        items = dataNodeDirectionItems, 
        update = AnimationNode.refresh)
    data_path: bpy.props.StringProperty(
        name="data path", 
        default="")
    props: bpy.props.StringProperty(
        name="props", 
        default="")
    node_data_type: bpy.props.EnumProperty(
        name="NodeDataType", 
        default="LIST", 
        items = nodeDataTypeItems)
    node_type: bpy.props.IntProperty(
        name="NodeType", 
        default=1)

    createString: BoolProperty(name = "Make String", default = False,
        description = "Transform list to string",
        update = AnimationNode.refresh)

    default_list: bpy.props.StringProperty(
        name="defaultList", 
        default='[0, 0]',
        description = "make sure you follow this structure [ val1, val2, etc..]",
        update = AnimationNode.refresh)
               
    def create(self):        
        self.data_path = 'bpy.data.node_groups[\'' + self.nodeTree.name + '\'].nodes[\'' + self.name +'\']'
       
        self.setValue(ast.literal_eval(self.default_list)) 
       
        if self.osc_direction == "OUTPUT":
            self.props = "value"
            self.newInput("Generic", "Value", "value")
        if self.osc_direction == "INPUT":
            self.props = "setValue"
            self.newOutput("Generic", "Value", "value")

    #def delete(self):
        
    def draw(self, layout):
        envars = bpy.context.scene.nodeosc_envars
        layout.enabled = not envars.isServerRunning
        layout.prop(self, "default_list", text = "")
        layout.prop(self, "createString", text = "", icon = "FILE_TEXT")
        layout.prop(self, "osc_address", text = "")
        layout.prop(self, "osc_index", text = "")
        layout.prop(self, "osc_direction", text = "")

    def getExecutionCode(self, required):
        if self.osc_direction == "OUTPUT":
            return "self.setValue(value)"
        if self.osc_direction == "INPUT":
            return "value = self.getValue()"

    def setValue(self, value):
        if self.createString:
            if len(value) == 1:
                dataByIdentifier[self.identifier] = str(value[0])
            else:
                dataByIdentifier[self.identifier] = str(value)
        else:
            dataByIdentifier[self.identifier] = value
            

    def getValue(self):
        value = dataByIdentifier.get(self.identifier)
        if isinstance(value, DoubleList):
            value = tuple(value)
        if value is not None and self.createString:
            if len(value) == 1:
                value = str(value[0])
            else:
                value = str(value)
        return value


    @property
    def value(self):
        return self.getValue()

    @value.setter
    def value(self, value):
        self.setValue(value)

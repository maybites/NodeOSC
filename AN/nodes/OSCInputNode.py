import bpy
from bpy.props import *
from collections import defaultdict
from animation_nodes.sockets.info import toIdName
from animation_nodes.base_types import AnimationNode

dataByIdentifier = defaultdict(None)

dataDirectionItems = {
    ("IMPORT", "Import", "Receive the data from somewhere else", "IMPORT", 0),
    ("EXPORT", "Export", "Another script can read the data from this node", "EXPORT", 1) }

class OSCInputNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_OSCInputNode"
    bl_label = "OSC Interface"

    dataDirection: EnumProperty(name = "Data Direction", default = "IMPORT",
        items = dataDirectionItems, update = AnimationNode.refresh)

    osc_address: StringProperty(name = "osc.address", default = "",
        update = AnimationNode.refresh)

    osc_index: StringProperty(name = "osc.index", default = "",
        update = AnimationNode.refresh)

    oscHandlerID = -1
    oscHandler = None

    def create(self):
        if self.oscHandlerID == -1:
            bpy.context.scene.OSC_nodes.clear()
            self.oscHandlerID = len(bpy.context.scene.OSC_nodes)
            print("created node: ", self.oscHandlerID)
            self.oscHandler = bpy.context.scene.OSC_nodes.add()
            self.oscHandler.data_path = 'bpy.data.node_groups[\'' + self.nodeTree.name + '\'].nodes[\'' + self.name +'\']'
            #self.oscHandler.data_path = self.getValue.__module__
            #self.oscHandler.data_path = self.identifier
            self.oscHandler.osc_address = self.osc_address
            self.oscHandler.osc_index = self.osc_index
            self.oscHandler.id = "value"
        
        if self.dataDirection == "EXPORT":
            self.newInput("Generic", "Value", "value")
        if self.dataDirection == "IMPORT":
            self.newOutput("Generic", "Value", "value")

    def delete(self):
        bpy.context.scene.OSC_nodes.remove(self.oscHandlerID)
        print("removed node:", self.oscHandlerID)

    def draw(self, layout):
        layout.prop(self, "osc_address", text = "")
        layout.prop(self, "osc_index", text = "")
        layout.prop(self, "dataDirection", text = "")

    def getExecutionCode(self, required):
        if self.dataDirection == "EXPORT":
            return "self.setValue(value)"
        if self.dataDirection == "IMPORT":
            return "value = self.getValue()"

    def setValue(self, value):
        dataByIdentifier[self.identifier] = value

    def getValue(self):
        return dataByIdentifier.get(self.identifier)

    @property
    def value(self):
        return self.getValue()

    @value.setter
    def value(self, value):
        self.setValue(value)

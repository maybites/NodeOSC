import bpy

dataDirectionItems = {
    ("INPUT", "Input", "Receive the OSC message from somewhere else", "IMPORT", 0),
    ("OUTPUT", "Output", "Send the OSC message from this node", "EXPORT", 1),
    ("BOTH", "Both", "Send and Reveive this OSC message", "FILE_REFRESH", 2) }

dataNodeDirectionItems = {
    ("INPUT", "Input", "Receive the OSC message from somewhere else", "IMPORT", 0),
    ("OUTPUT", "Output", "Send the OSC message from this node", "EXPORT", 1) }

nodeDataTypeItems = {
    ("LIST", "List", "Expects List", "IMPORT", 0),
    ("SINGLE", "Single", "Expects single value", "IMPORT", 1) } 

nodeTypeItems = {
    ("NONE", 0),
    ("AN", 1),
    ("SORCAR", 2) } 

def sorcarTreeUpdate():
    bpy.context.scene.nodeosc_SORCAR_needsUpdate = True

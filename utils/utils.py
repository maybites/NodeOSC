import bpy

dataDirectionItems = {
    ("INPUT", "Input", "Receive the OSC message from somewhere else", "IMPORT", 0),
    ("OUTPUT", "Output", "Send the OSC message from this node", "EXPORT", 1) }

nodeDataTypeItems = {
    ("TUPLE", "Tuple", "Expects Tuple", "IMPORT", 0),
    ("FLOAT", "Float", "Expects Float", "IMPORT", 1) } 

nodeTypeItems = {
    ("NONE", 0),
    ("AN", 1),
    ("SORCAR", 2) } 

def sorcarTreeUpdate():
    bpy.context.scene.nodeosc_SORCAR_needsUpdate = True

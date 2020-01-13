import bpy

dataDirectionItems = {
    ("INPUT", "Input", "Receive the OSC message from somewhere else", "IMPORT", 0),
    ("OUTPUT", "Output", "Send the OSC message from this node", "EXPORT", 1) }

nodeDataTypeItems = {
    ("TUPLE", "Tuple", "Expects Tuple", "IMPORT", 0),
    ("FLOAT", "Float", "Expects Float", "IMPORT", 1) } 

nodeTypeItems = {
    ("NONE", "None", "is nota a message to/from a node", "INFO", 0),
    ("AN", "AnimationNode", "is a message to/from an animation node", "INFO", 1),
    ("SORCAR", "Sorcar", "is a message to/from a sorcar node", "IMPORT", 2) } 

__error_report = ""
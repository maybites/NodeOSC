import bpy
import queue

from ..nodes.nodes import *
from ..utils import utils

#######################################
#  OSC Receive Method                 #
#######################################

# the OSC-server should not directly modify blender data from its own thread.
# instead we need a queue to store the callbacks and execute them inside
# a blender timer thread

# define the queue to store the callbacks
OSC_callback_queue = queue.LifoQueue()

# the repeatfilter, together with lifo (last in - first out) will
# make sure only the last osc message received on a certain address
# will be applied. all older messages will be ignored.
queue_repeat_filter = {}

# define the method the timer thread is calling when it is appropriate
def execute_queued_OSC_callbacks():
    queue_repeat_filter.clear()
    
    hasOscMessages = False
    
    # while there are callbacks stored inside the queue
    while not OSC_callback_queue.empty():
        hasOscMessages = True
        items = OSC_callback_queue.get()
        address = items[1]
        # if the address has not been here before:
        if queue_repeat_filter.get(address, False) == False:
            func = items[0]
            args = items[1:]
            # execute them 
            func(*args)
            
        queue_repeat_filter[address] = True
        
    if hasOscMessages:
        if bpy.context.scene.nodeosc_envars.node_update != "MESSAGE":
            bpy.context.scene.nodeosc_AN_needsUpdate = True
            bpy.context.scene.nodeosc_SORCAR_needsUpdate = True

    #when all the messages are applied, execute the Animation node tree
    #  the SORCAR node tree needs to be executed from the server modal method..
    executeAnimationNodeTrees()
    
    return 0 if bpy.context.scene.nodeosc_envars.input_rate == 0 else bpy.context.scene.nodeosc_envars.input_rate / 1000

# called by the queue execution thread
def OSC_callback_unkown(address, args):
    bpy.context.scene.nodeosc_envars.lastaddr = address
    bpy.context.scene.nodeosc_envars.lastpayload = str(args)

# called by the queue execution thread
def OSC_callback_custom(address, obj, attr, attrIdx, oscArgs, oscIndex):
    try:
        if len(oscIndex) > 0:
            obj[attr] = oscArgs[oscIndex[0]]
        else:
            obj[attr] = oscArgs[0]
    except TypeError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Message attribute invalid: "+address + " " + str(oscArgs) + " " + str(err)      
    except:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Improper attributes received: "+address + " " + str(oscArgs)

# called by the queue execution thread
def OSC_callback_Property(address, obj, attr, attrIdx, oscArgs, oscIndex):
    try:
        val = oscArgs[0]
        if len(oscIndex) > 0:
            val = oscArgs[oscIndex[0]]
        setattr(obj,attr,val)
    except TypeError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Message attribute invalid: "+address + " " + str(oscArgs) + " " + str(err)      
    except:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Improper attributes received: "+address + " " + str(oscArgs)

# called by the queue execution thread
def OSC_callback_IndexedProperty(address, obj, attr, attrIdx, oscArgs, oscIndex):
    try:
        if len(oscIndex) > 0:
            getattr(obj,attr)[attrIdx] = oscArgs[oscIndex[0]]
        else:
            getattr(obj,attr)[attrIdx] = oscArgs[0]
    except TypeError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Message attribute invalid: "+address + " " + str(oscArgs) + " " + str(err)      
    except:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Improper attributes received: "+address + " " + str(oscArgs)

# called by the queue execution thread
def OSC_callback_properties(address, obj, attr, attrIdx, oscArgs, oscIndex):
    try:
        if len(oscIndex) > 0:
            getattr(obj, attr)[:] = (oscArgs[i] for i in oscIndex)
        else:
            getattr(obj, attr)[:] = oscArgs
            
    except TypeError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Message attribute invalid: "+address + " " + str(oscArgs) + " " + str(err)      
    except:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Improper attributes received: "+address + " " + str(oscArgs)

# called by the queue execution thread
def OSC_callback_nodeFLOAT(address, obj, attr, attrIdx, oscArgs, oscIndex):
    try:
        val = oscArgs[0]
        if len(oscIndex) > 0:
            val = oscArgs[oscIndex[0]]
        getattr(obj, attr)(val)
    except TypeError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Message attribute invalid: "+address + " " + str(oscArgs) + " " + str(err)      
    except:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Improper attributes received: "+address + " " + str(oscArgs)

# called by the queue execution thread
def OSC_callback_nodeLIST(address, obj, attr, attrIdx, oscArgs, oscIndex):
    try:
        val = list(oscArgs)
        if len(oscIndex) > 0:
            val = list(oscArgs[i] for i in oscIndex)
        getattr(obj, attr)(val)
    except TypeError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Message attribute invalid: "+address + " " + str(oscArgs) + " " + str(err)      
    except:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Improper attributes received: "+address + " " + str(oscArgs)

# method called by the pythonosc library in case of an unmapped message
def OSC_callback_pythonosc_undef(* args):
    if bpy.context.scene.nodeosc_envars.message_monitor == True:
        address = args[0]
        OSC_callback_queue.put((OSC_callback_unkown, address, args[1:]))

# method called by the pythonosc library in case of a mapped message
def OSC_callback_pythonosc(* args):
    # the args structure:
    #    args[0] = osc address
    #    args[1] = custom data pakage (tuplet with 5 values)
    #    args[>1] = osc arguments
    address = args[0]
    mytype = args[1][0][0]      # callback type 
    obj = args[1][0][1]          # blender object name (i.e. bpy.data.objects['Cube'])
    attr = args[1][0][2]        # blender object ID (i.e. location)
    attrIdx = args[1][0][3]         # ID-index (not used)
    oscIndex = args[1][0][4]    # osc argument index to use (should be a tuplet, like (1,2,3))
    nodeType = args[1][0][5]    # node type 

    # we have to make sure the oscIndex is a tuple. 
    # there is a cornercase '(0)' where make_tuple doesn't return tuple (how stupid is that)
    if isinstance(oscIndex, int): 
        oscIndex = (oscIndex,)

    oscArgs = args[2:]

    fillCallbackQue(address, obj, attr, attrIdx, oscArgs, oscIndex, mytype)
     
# method called by the pyliblo library in case of a mapped message
def OSC_callback_pyliblo(path, oscArgs, types, src, data):
    # the args structure:
    address = path
    mytype = data[0]        # callback type 
    obj = data[1]           # blender object name (i.e. bpy.data.objects['Cube'])
    attr = data[2]          # blender object ID (i.e. location)
    attrIdx = data[3]       # ID-index (not used)
    oscIndex = data[4]      # osc argument index to use (should be a tuplet, like (1,2,3))
    nodeType = data[5]      # node type 

    # we have to make sure the oscIndex is a tuple. 
    # there is a cornercase '(0)' where make_tuple doesn't return tuple (how stupid is that)
    if isinstance(oscIndex, int): 
        oscIndex = (oscIndex,)
        
    fillCallbackQue(address, obj, attr, attrIdx, oscArgs, oscIndex, mytype)


def fillCallbackQue(address, obj, attr, attrIdx, oscArgs, oscIndex, mytype):
    if mytype == -1:
        #special type reserved for message that triggers the execution of nodetrees
        if nodeType == 1:
            bpy.context.scene.nodeosc_AN_needsUpdate = True
        elif nodeType == 2:
            bpy.context.scene.nodeosc_SORCAR_needsUpdate = True
    elif mytype == 0:
        OSC_callback_queue.put((OSC_callback_unkown, address, oscArgs))
    elif mytype == 1:
        OSC_callback_queue.put((OSC_callback_custom, address, obj, attr, attrIdx, oscArgs, oscIndex))
    elif mytype == 2:
        OSC_callback_queue.put((OSC_callback_Property, address, obj, attr, attrIdx, oscArgs, oscIndex))
    elif mytype == 3:
        OSC_callback_queue.put((OSC_callback_IndexedProperty, address, obj, attr, attrIdx, oscArgs, oscIndex))
    elif mytype == 4:
        OSC_callback_queue.put((OSC_callback_properties, address, obj, attr, attrIdx, oscArgs, oscIndex))
    elif mytype == 5:
        OSC_callback_queue.put((OSC_callback_nodeFLOAT, address, obj, attr, attrIdx, oscArgs, oscIndex))
    elif mytype == 6:
        OSC_callback_queue.put((OSC_callback_nodeLIST, address, obj, attr, attrIdx, oscArgs, oscIndex))

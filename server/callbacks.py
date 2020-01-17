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
        address_uniq = items[1]
        # if the address has not been here before:
        if queue_repeat_filter.get(address_uniq, False) == False:
            func = items[0]
            args = items[2:]
            # execute them 
            func(*args)
            
        queue_repeat_filter[address_uniq] = True
        
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
def OSC_callback_Property(address, data_path, prop, attrIdx, oscArgs, oscIndex):
    try:
        val = oscArgs[0]
        if len(oscIndex) > 0:
            val = oscArgs[oscIndex[0]]
        setattr(data_path,prop,val)
    except TypeError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Message attribute invalid: "+address + " " + str(oscArgs) + " " + str(err)      
    except:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Improper attributes received: "+address + " " + str(oscArgs)

# called by the queue execution thread
def OSC_callback_IndexedProperty(address, data_path, prop, attrIdx, oscArgs, oscIndex):
    try:
        if len(oscIndex) > 0:
            getattr(data_path,prop)[attrIdx] = oscArgs[oscIndex[0]]
        else:
            getattr(data_path,prop)[attrIdx] = oscArgs[0]
    except TypeError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Message attribute invalid: "+address + " " + str(oscArgs) + " " + str(err)      
    except:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Improper attributes received: "+address + " " + str(oscArgs)

# called by the queue execution thread
def OSC_callback_properties(address, data_path, prop, attrIdx, oscArgs, oscIndex):
    try:
        if len(oscIndex) > 0:
            getattr(data_path, prop)[:] = (oscArgs[i] for i in oscIndex)
        else:
            getattr(data_path, prop)[:] = oscArgs
            
    except TypeError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Message attribute invalid: "+address + " " + str(oscArgs) + " " + str(err)      
    except:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Improper attributes received: "+address + " " + str(oscArgs)

# called by the queue execution thread
def OSC_callback_nodeFLOAT(address, data_path, prop, attrIdx, oscArgs, oscIndex):
    try:
        val = oscArgs[0]
        if len(oscIndex) > 0:
            val = oscArgs[oscIndex[0]]
        getattr(data_path, prop)(val)
    except TypeError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Message attribute invalid: "+address + " " + str(oscArgs) + " " + str(err)      
    except:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Improper attributes received: "+address + " " + str(oscArgs)

# called by the queue execution thread
def OSC_callback_nodeLIST(address, data_path, prop, attrIdx, oscArgs, oscIndex):
    try:
        val = list(oscArgs)
        if len(oscIndex) > 0:
            val = list(oscArgs[i] for i in oscIndex)
        getattr(data_path, prop)(val)
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
        OSC_callback_queue.put((OSC_callback_unkown, address, address, args[1:]))

# method called by the pythonosc library in case of a mapped message
def OSC_callback_pythonosc(* args):
    # the args structure:
    #    args[0] = osc address
    #    args[1][0] = custom data package list with (tuplet with 5 values)
    #    args[>1] = osc arguments
    address = args[0]
    data = args[1][0]
    oscArgs = args[2:]
    
    fillCallbackQue(address, oscArgs, data)
     
# method called by the pyliblo library in case of a mapped message
def OSC_callback_pyliblo(path, args, types, src, data):
    # the args structure:
    address = path
    oscArgs = args
    
    fillCallbackQue(address, oscArgs, data)


def fillCallbackQue(address, oscArgs, dataList):
    index = 0
    for data in dataList:
        mytype = data[0]        # callback type 
        datapath = data[1]      # blender datapath (i.e. bpy.data.objects['Cube'])
        prop = data[2]          # blender property ID (i.e. location)
        attrIdx = data[3]       # ID-index (not used)
        oscIndex = data[4]      # osc argument index to use (should be a tuplet, like (1,2,3))
        nodeType = data[5]      # node type 

        address_uniq = address + "_" + str(index)
        
        if mytype == -1:
            #special type reserved for message that triggers the execution of nodetrees
            if nodeType == 1:
                bpy.context.scene.nodeosc_AN_needsUpdate = True
            elif nodeType == 2:
                bpy.context.scene.nodeosc_SORCAR_needsUpdate = True
        elif mytype == 0:
            OSC_callback_queue.put((OSC_callback_unkown, address_uniq, address, oscArgs))
        elif mytype == 1:
            OSC_callback_queue.put((OSC_callback_custom, address_uniq, address, datapath, prop, attrIdx, oscArgs, oscIndex))
        elif mytype == 2:
            OSC_callback_queue.put((OSC_callback_Property, address_uniq, address, datapath, prop, attrIdx, oscArgs, oscIndex))
        elif mytype == 3:
            OSC_callback_queue.put((OSC_callback_IndexedProperty, address_uniq, address, datapath, prop, attrIdx, oscArgs, oscIndex))
        elif mytype == 4:
            OSC_callback_queue.put((OSC_callback_properties, address_uniq, address, datapath, prop, attrIdx, oscArgs, oscIndex))
        elif mytype == 5:
            OSC_callback_queue.put((OSC_callback_nodeFLOAT, address_uniq, address, datapath, prop, attrIdx, oscArgs, oscIndex))
        elif mytype == 6:
            OSC_callback_queue.put((OSC_callback_nodeLIST, address_uniq, address, datapath, prop, attrIdx, oscArgs, oscIndex))

        index += 1
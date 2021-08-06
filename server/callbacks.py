import bpy
import queue
import time
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

# contains all the OSC messages that are expected to be received
OSC_Callback_Handlers = {}

# called after startup of inputServer
def setOscHandlers(_oscHandlers):
    global OSC_Callback_Handlers
    OSC_Callback_Handlers = _oscHandlers

# define the method the timer thread is calling when it is appropriate
def execute_queued_OSC_callbacks():
    envars = bpy.context.scene.nodeosc_envars

    start = time.perf_counter()
    queue_repeat_filter.clear()
    
    hasOscMessages = False
    
    # while there are callbacks stored inside the queue
    while not OSC_callback_queue.empty():
        hasOscMessages = True
        items = OSC_callback_queue.get()
        address_uniq = items[1]
        # if the address has not been here before:
        if not envars.repeat_address_filter_IN or (envars.repeat_address_filter_IN and queue_repeat_filter.get(address_uniq, False) == False):
            func = items[0]
            args = items[2:]
            # execute them 
            func(*args)
        
        if envars.repeat_address_filter_IN:
            queue_repeat_filter[address_uniq] = True
        
    if hasOscMessages:
        if bpy.context.scene.nodeosc_envars.node_update != "MESSAGE":
            bpy.context.scene.nodeosc_AN_needsUpdate = True
            bpy.context.scene.nodeosc_SORCAR_needsUpdate = True

    #when all the messages are applied, execute the Animation node tree
    #  the SORCAR node tree needs to be executed from the server modal method..
    executeAnimationNodeTrees()
    
    # calculate the execution time
    end = time.perf_counter()
    bpy.context.scene.nodeosc_envars.executionTimeInput = end - start
    
    return 0 if bpy.context.scene.nodeosc_envars.input_rate == 0 else bpy.context.scene.nodeosc_envars.input_rate / 1000

# called by the queue execution thread
def OSC_callback_unkown(address, args):
    bpy.context.scene.nodeosc_envars.lastaddr = address
    bpy.context.scene.nodeosc_envars.lastpayload = str(args)

# called by the queue execution thread
def OSC_callback_function(address, data_path, prop, attrIdx, oscArgs, oscIndex):
    try:
        eval(data_path)
    except Exception as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  str(err) + " > address: "+address + " | function: " + data_path

# called by the queue execution thread
def OSC_callback_statement(address, data_path, prop, attrIdx, oscArgs, oscIndex):
    try:
        exec(data_path)
    except Exception as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  str(err) + " > address: "+address + " | statement: " + data_path

# called by the queue execution thread
def OSC_callback_custom(address, data_path, prop, attrIdx, oscArgs, oscIndex):
    try:
        if len(oscIndex) > 0:
            data_path[prop] = oscArgs[oscIndex[0]]
        else:
            data_path[prop] = oscArgs[0]
    except TypeError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Message attribute invalid: "+address + " " + str(oscArgs) + " " + str(err)      
    except IndexError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "provided args[idx] out of range > address: " + address + " | args: " + str(oscArgs)  + " | args[idx]: " + str(oscIndex)
    except Exception as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  str(err) + " > address: "+address + " | args: " + str(oscArgs) 

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
    except IndexError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "provided args[idx] out of range > address: " + address + " | args: " + str(oscArgs)  + " | args[idx]: " + str(oscIndex)
    except Exception as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  str(err) + " > address: "+address + " | args: " + str(oscArgs) 

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
    except IndexError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "provided args[idx] out of range > address: " + address + " | args: " + str(oscArgs)  + " | args[idx]: " + str(oscIndex)
    except Exception as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  str(err) + " > address: "+address + " | args: " + str(oscArgs) 

# called by the queue execution thread
def OSC_callback_properties(address, data_path, prop, attrIdx, oscArgs, oscIndex):
    try:
        if len(oscIndex) > 0:
            getattr(data_path, prop)[:] = (oscArgs[i] for i in oscIndex)
        else:
            getattr(data_path, prop)[:] = oscArgs
            
    except TypeError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  str(err) + "> address: "+address + " | args: " + str(oscArgs)     
    except IndexError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "provided args[idx] out of range > address: " + address + " | args: " + str(oscArgs)  + " | args[idx]: " + str(oscIndex)
    except Exception as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  str(err) + " > address: "+address + " | args: " + str(oscArgs) 

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
    except IndexError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "provided args[idx] out of range > address: " + address + " | args: " + str(oscArgs)  + " | args[idx]: " + str(oscIndex)
    except Exception as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  str(err) + "> address: "+address + " | args: " + str(oscArgs) 

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

# called by the queue execution thread
def OSC_callback_format(address, data_path, prop_ignore, attrIdx, oscArgs, oscIndex, sFormat, sRange):
    # prepare the available variables
    length = len(oscArgs)
    args = oscArgs
    if sRange == '':
        call_format(address, data_path, prop_ignore, attrIdx, oscArgs, oscIndex, sFormat, 0)
    else:
        for index in range (*eval(sRange)):
            call_format(address, data_path, prop_ignore, attrIdx, oscArgs, oscIndex, sFormat, index)

# called by the queue execution thread
def call_format(address, data_path, prop_ignore, attrIdx, oscArgs, oscIndex, sFormat, index):
    try:
        # format the data_path
        length = len(oscArgs)
        args = oscArgs
        myFormat = eval(sFormat)
        if type(myFormat) is tuple:     
            f_data_path = data_path.format(*myFormat)
        else:
            f_data_path = data_path.format(myFormat)
                
        f_OscIndex = eval(oscIndex)

        if bpy.context.scene.nodeosc_envars.debug_monitor == True:
            msg = "Recived: "+address + " " + str(oscArgs)  + " -> applied to evaluated data-path: '" + f_data_path + "' with format: '" + str(myFormat) + "' and args[idx]: '" + str(f_OscIndex) + "' "
            bpy.context.scene.nodeosc_envars.error += '\n' + msg

        #  ... and don't forget the corner case
        if isinstance(f_OscIndex, int): 
            f_OscIndex = (f_OscIndex,)
        # now we have to analyse the data_path to figure out how we have to apply the values
        if f_data_path.find('][') != -1 and (f_data_path[-2:] == '"]' or f_data_path[-2:] == '\']'):
            #For custom properties 
            #   like bpy.data.objects['Cube']['customProp']
            prop = f_data_path[f_data_path.rindex('['):]
            prop = prop[2:-2] # get rid of [' ']
            datapath = f_data_path[0:f_data_path.rindex('[')]
            OSC_callback_custom(address, eval(datapath), prop, attrIdx, oscArgs, f_OscIndex)
        elif f_data_path[-1] == ']':
            #For normal properties with index in brackets 
            #   like bpy.data.objects['Cube'].location[0]
            datapath = f_data_path[0:f_data_path.rindex('.')]
            prop =  f_data_path[f_data_path.rindex('.') + 1:f_data_path.rindex('[')]
            prop_index =  f_data_path[f_data_path.rindex('[') + 1:f_data_path.rindex(']')]
            OSC_callback_IndexedProperty(address, eval(datapath), prop, int(prop_index), oscArgs, f_OscIndex)
        elif f_data_path[-1] == ')' :
            # its a function call 
            prop = ''
            OSC_callback_function(address, f_data_path, prop, attrIdx, oscArgs, f_OscIndex)
        elif f_data_path.find('=') != -1:
            # its a statement call 
            prop = ''
            OSC_callback_statement(address, f_data_path, prop, attrIdx, oscArgs, f_OscIndex)
        else:
            #without index in brackets
            datapath = f_data_path[0:f_data_path.rindex('.')]
            prop =  f_data_path[f_data_path.rindex('.') + 1:]
            OSC_callback_properties(address, eval(datapath), prop, attrIdx, oscArgs, f_OscIndex)
 
    except TypeError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Message attribute invalid: "+address + " " + str(oscArgs) + " " + str(err)      
    except SyntaxError as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Evaluation error: " + str(err) +  " with >" + str(err.text) + "<"
    except Exception as err:
        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            bpy.context.scene.nodeosc_envars.error =  "Unknown error: " + str(err)

# method called by the pythonosc library in case of an unmapped message
def OSC_callback_pythonosc_undef(* args):
    if bpy.context.scene.nodeosc_envars.message_monitor == True:
        address = args[0]
        OSC_callback_queue.put((OSC_callback_unkown, address, address, args[1:]))

# method called by the oscpy library in case of a mapped message
def OSC_callback_oscpy(* args):
    # the args structure:
    #    args[0] = osc address
    #    args[>0] = osc arguments
    
    address = bytes.decode(args[0])
    oscArgs = args[1:]
    global OSC_Callback_Handlers
    data = OSC_Callback_Handlers.get(address)
    
    if data != None:
        fillCallbackQue(address, oscArgs, data)
    else:
        if bpy.context.scene.nodeosc_envars.message_monitor:
            OSC_callback_queue.put((OSC_callback_unkown, address, address, oscArgs))
        

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


def fillCallbackQue(address, args, dataList):
    index = 0
    for data in dataList:
        mytype = data[0]        # callback type 
        datapath = data[1]      # blender datapath (i.e. bpy.data.objects['Cube'])
        prop = data[2]          # blender property (i.e. location)
        attrIdx = data[3]       # blender property index (i.e. location[index])
        oscIndex = data[4]      # osc argument index to use (should be a tuplet, like (1,2,3))
        nodeType = data[5]      # node type 
        myFormat = data[6]      # datapath format string
        myRange = data[7]       # loop range string
        myFilter = data[8]      # filter condition

        address_uniq = address + "_" + str(index)
        
        if (myFilter == True or eval(myFilter)):        
            if mytype == -1:
                #special type reserved for message that triggers the execution of nodetrees
                if nodeType == 1:
                    bpy.context.scene.nodeosc_AN_needsUpdate = True
                elif nodeType == 2:
                    bpy.context.scene.nodeosc_SORCAR_needsUpdate = True
            elif mytype == 0:
                OSC_callback_queue.put((OSC_callback_unkown, address_uniq, address, args))
            elif mytype == 1:
                OSC_callback_queue.put((OSC_callback_custom, address_uniq, address, datapath, prop, attrIdx, args, oscIndex))
            elif mytype == 2:
                OSC_callback_queue.put((OSC_callback_Property, address_uniq, address, datapath, prop, attrIdx, args, oscIndex))
            elif mytype == 3:
                OSC_callback_queue.put((OSC_callback_IndexedProperty, address_uniq, address, datapath, prop, attrIdx, args, oscIndex))
            elif mytype == 4:
                OSC_callback_queue.put((OSC_callback_properties, address_uniq, address, datapath, prop, attrIdx, args, oscIndex))
            elif mytype == 5:
                OSC_callback_queue.put((OSC_callback_nodeFLOAT, address_uniq, address, datapath, prop, attrIdx, args, oscIndex))
            elif mytype == 6:
                OSC_callback_queue.put((OSC_callback_nodeLIST, address_uniq, address, datapath, prop, attrIdx, args, oscIndex))
            elif mytype == 7:
                OSC_callback_queue.put((OSC_callback_function, address_uniq, address, datapath, prop, attrIdx, args, oscIndex))
            elif mytype == 10:
                OSC_callback_queue.put((OSC_callback_format, address_uniq, address, datapath, prop, attrIdx, args, oscIndex, myFormat, myRange))

            index += 1
import bpy
import types
import sys
from select import select
import socket
import errno
import mathutils
import traceback
from math import radians
from bpy.props import *
from ast import literal_eval as make_tuple

from .callbacks import *
from ..nodes.nodes import *

def make_osc_messages(myOscKeys, myOscMsg):
    envars = bpy.context.scene.nodeosc_envars
    for item in myOscKeys:        
        if item.dp_format_enable == False:
            # we cannot deal with a datapath string that has format syntax
            #print( "sending  :{}".format(item) )
            prop = None
            if item.node_type == 1:
                prop = eval(item.data_path + ".getValue()")
            else:
                prop = eval(item.data_path)
            
            # now make the values to be sent a tuple (unless its a string or None)
            if isinstance(prop, (bool, int, float)):
                prop = (prop,)
            elif prop is None:
                prop = 'None'
            elif isinstance(prop, (mathutils.Vector, mathutils.Quaternion, mathutils.Euler, mathutils.Matrix)):
                prop = tuple(prop)
            
            stringProp = str(prop)
            
            if not (item.filter_repetition and envars.repeat_argument_filter_OUT) and stringProp != item.value:
                item.value = stringProp

                # make sure the osc indices are a tuple
                indices = make_tuple(item.osc_index)
                if isinstance(indices, int): 
                    indices = (indices,)
                    
                # sort the properties according to the osc_indices
                if prop is not None and not isinstance(prop, str) and len(indices) > 0:
                    prop = tuple(prop[i] for i in indices)
                myOscMsg[item.osc_address] = prop
    return myOscMsg

#######################################
#  PythonOSC Server  BASE CLASS       #
#######################################

class OSC_OT_OSCServer(bpy.types.Operator):

    _timer = None
    count = 0
    
    #####################################
    # CUSTOMIZEABLE FUNCTIONS:

    #inputServer = "" #for the receiving socket
    #outputServer = "" #for the sending socket
    #dispatcher = "" #dispatcher function
    
    def sendingOSC(self, context, event):
         pass
        
    # setup the sending server
    def setupInputServer(self, context, envars):
        pass

    # setup the receiving server
    def setupOutputServer(self, context, envars):
       pass
    
    # add method 
    def addMethod(self, address, data):
        pass

    # add default method 
    def addDefaultMethod():
        pass
    
    # start receiving 
    def startupInputServer(self, context, envars):
        pass

    # stop receiving
    def shutDownInputServer(self, context, envars):
        pass

    #
    #
    #####################################
 
    #######################################
    #  MODAL Function                     #
    #######################################

    def modal(self, context, event):
        envars = bpy.context.scene.nodeosc_envars
        if envars.isServerRunning == False:
            return self.cancel(context)
        if envars.message_monitor and envars.error != "":
            self.report({'WARNING'}, envars.error)
            print(envars.error)
            envars.error = ""

        if event.type == 'TIMER':
            #hack to refresh the GUI
            self.count = self.count + envars.output_rate
            if envars.message_monitor == True:
                if self.count >= 100:
                    self.count = 0
                    context.area.tag_redraw()

            # only available spot where updating the sorcar tree doesn't throw errors...
            executeSorcarNodeTrees(context)

            try:
                start = time.perf_counter()
                self.sendingOSC(context, event)
                # calculate the execution time
                end = time.perf_counter()
                bpy.context.scene.nodeosc_envars.executionTimeOutput = end - start
                
            except Exception as err:
                self.report({'WARNING'}, "Output error: {0}".format(err))
                return self.cancel(context)

        return {'PASS_THROUGH'}
    
    #######################################
    #  Setup OSC Receiver and Sender      #
    #######################################

    def execute(self, context):
        envars = bpy.context.scene.nodeosc_envars
        if envars.port_in == envars.port_out:
            self.report({'WARNING'}, "Ports must be different.")
            return{'FINISHED'}
        if envars.isServerRunning == False:
    
            #Setting up the dispatcher for receiving
            try:
                self.setupInputServer(context, envars)
                
                self.setupOutputServer(context, envars)
                
                #  all the osc messages handlers ready for registering to the server
                oscHandlerDict = {} 
                oscHandleList = []
                
                # register a message for executing 
                if envars.node_update == "MESSAGE" and hasAnimationNodes():
                    # oscHandleList content:
                        # callback type 
                        # blender datapath (i.e. bpy.data.objects['Cube'])
                        # blender property (i.e. location)
                        # blender property index (i.e. location[index])
                        # osc argument index to use (should be a tuplet, like (1,2,3))
                        # node type 
                        # datapath format string
                        # loop range string
                        # filter eval string

                    oscHandleList = (-1, None, None, None, None, 0, '', '', True)
                    self.addOscHandler(oscHandlerDict, envars.node_frameMessage, oscHandleList)
                
                for item in bpy.context.scene.NodeOSC_keys:
                    filter_eval = True
                    if item.filter_enable:
                        filter_eval = item.filter_eval
                    if item.osc_direction != "OUTPUT" and item.enabled:
                        if item.dp_format_enable == False:      
                            # make osc index into a tuple ..
                            oscIndex = make_tuple(item.osc_index)
                            #  ... and don't forget the corner case
                            if isinstance(oscIndex, int): 
                                oscIndex = (oscIndex,)
                            
                            try:
                                oscHandleList = None
                                if item.data_path.find('][') != -1 and (item.data_path[-2:] == '"]' or item.data_path[-2:] == '\']'):
                                    #For custom properties 
                                    #   like bpy.data.objects['Cube']['customProp']
                                    prop =  item.data_path[item.data_path.rindex('['):]
                                    prop = prop[2:-2] # get rid of [' ']
                                    datapath = item.data_path[0:item.data_path.rindex('[')]
                                    oscHandleList = [1, eval(datapath), prop, item.idx, oscIndex, item.node_type, '', '', filter_eval]
                                elif item.data_path[-1] == ']':
                                    #For normal properties with index in brackets 
                                    #   like bpy.data.objects['Cube'].location[0]
                                    datapath = item.data_path[0:item.data_path.rindex('.')]
                                    prop =  item.data_path[item.data_path.rindex('.') + 1:item.data_path.rindex('[')]
                                    prop_index =  item.data_path[item.data_path.rindex('[') + 1:item.data_path.rindex(']')]
                                    oscHandleList = [3, eval(datapath), prop, int(prop_index), oscIndex, item.node_type, '', '', filter_eval]
                                elif item.data_path[-1] == ')':
                                    # its a function call
                                    oscHandleList = [7, item.data_path, '', item.idx, oscIndex, item.node_type, '', '', filter_eval]
                                else:
                                    #without index in brackets
                                    datapath = item.data_path[0:item.data_path.rindex('.')]
                                    prop =  item.data_path[item.data_path.rindex('.') + 1:]
                                    if isinstance(getattr(eval(datapath), prop), (int, float, str)):
                                        # property is single value
                                        oscHandleList = [2, eval(datapath), prop, item.idx, oscIndex, item.node_type, '', '', filter_eval]
                                    else:
                                        # property is array
                                        oscHandleList = [4, eval(datapath), prop, item.idx, oscIndex, item.node_type, '', '', filter_eval]
                                        
                                if oscHandleList != None:
                                    self.addOscHandler(oscHandlerDict, item.osc_address.strip(), oscHandleList)
                                else:
                                    self.report({'WARNING'}, "Unable to create listener for: object '"+item.data_path+"' with id '"+item.props+"' : {0}".format(err))
                                    
                            except Exception as err:
                                self.report({'WARNING'}, "Register custom handle: object '"+item.data_path+"' with id '"+item.props+"' : {0}".format(err))

                        else:
                            oscIndex = item.osc_index
                            try:
                                oscHandleList = None
                                
                                if item.loop_enable:
                                    oscHandleList = [10, item.data_path, '', 0, item.osc_index, item.node_type, item.dp_format, item.loop_range, filter_eval]
                                else:
                                    oscHandleList = [10, item.data_path, '', 0, item.osc_index, item.node_type, item.dp_format, '', filter_eval]
                                
                                if oscHandleList != None:
                                    self.addOscHandler(oscHandlerDict, item.osc_address.strip(), oscHandleList)
                                else:
                                    self.report({'WARNING'}, "Unable to create listener for: object '"+item.data_path+"' with id '"+item.props+"' : {0}".format(err))
                            except Exception as err:
                                self.report({'WARNING'}, "Register custom handle: object '"+item.data_path+"' with id '"+item.props+"' : {0}".format(err))
                            

                # lets go and find all nodes in all nodetrees that are relevant for us
                nodes_createCollections()
                
                for item in bpy.context.scene.NodeOSC_nodes:
                    filter_eval = True
                    if item.osc_direction != "OUTPUT":
                        # make osc index into a tuple ..
                        oscIndex = make_tuple(item.osc_index)
                        #  ... and don't forget the corner case
                        if isinstance(oscIndex, int): 
                            oscIndex = (oscIndex,)
                            
                        try:
                            if item.node_data_type == "SINGLE":
                                oscHandleList = [5, eval(item.data_path), item.props, item.idx, oscIndex, item.node_type, '', '', filter_eval]
                            elif item.node_data_type == "LIST":
                                oscHandleList = [6, eval(item.data_path), item.props, item.idx, oscIndex, item.node_type, '', '', filter_eval]

                            self.addOscHandler(oscHandlerDict, item.osc_address.strip(), oscHandleList)
                        except Exception as err:
                            self.report({'WARNING'}, "Register node handle: object '"+item.data_path+"' with id '"+item.props+"' : {0}".format(err))

                # register all oscHandles on the server
                for address, oscHandles in oscHandlerDict.items():
                    self.addMethod(address, oscHandles)

                # this provides the callback functions with the oscHandles
                setOscHandlers(oscHandlerDict)
                
                # register the default method for unregistered addresses
                self.addDefaultMethod()

                # startup the receiving server
                self.startupInputServer(context, envars)
                                
                # register the execute queue method
                bpy.app.timers.register(execute_queued_OSC_callbacks)

                #inititate the modal timer thread
                context.window_manager.modal_handler_add(self)
                self._timer = context.window_manager.event_timer_add(envars.output_rate/1000, window = context.window)
            
            except Exception as err:
                self.report({'WARNING'}, "Server startup: {0}".format(err))
                return {'CANCELLED'}

            envars.isServerRunning = True
            
            self.report({'INFO'}, "Server successfully started!")

            return {'RUNNING_MODAL'}
        else:
            self.report({'INFO'}, "Server stopped!")
            envars.isServerRunning = False    
                
        return{'FINISHED'}


    def cancel(self, context):
        envars = bpy.context.scene.nodeosc_envars
        self.shutDownInputServer(context, envars)
        context.window_manager.event_timer_remove(self._timer)

        # hack to check who is calling the cancel method. 
        # see https://blender.stackexchange.com/questions/23126/is-there-a-way-to-execute-code-before-blender-is-closing
        traceback_elements = traceback.format_stack()
        # if the stack has 2 elements, it is because the server stop has been pushed.
        #  otherwise it might be loading a new project which would cause an exception
        #  and stop the proper shutdown of the server..
        if traceback_elements.__len__ == 2:        
            bpy.app.timers.unregister(execute_queued_OSC_callbacks)  
                  
        return {'CANCELLED'}

    # will take an address and a oscHandle data packet. 
    # if the address has already been used, the package will be added to the packagelist
    def addOscHandler(self, handleDict, address, oscHandlePackage):
        oldpackage = handleDict.get(address)
        if oldpackage == None:
            oldpackage = [oscHandlePackage]
        else:
            oldpackage += [oscHandlePackage]
        handleDict[address] = oldpackage
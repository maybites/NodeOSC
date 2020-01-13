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
            if self.count >= 500:
                self.count = 0
                if envars.message_monitor == True:
                    for window in bpy.context.window_manager.windows:
                        screen = window.screen
                        for area in screen.areas:
                            if area.type == 'VIEW_3D':
                                area.tag_redraw()

            for node_group in bpy.data.node_groups:
                if node_group.bl_idname == 'ScNodeTree':
                    node_group.execute_node()

            try:
                self.sendingOSC(context, event)
                    
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

                dataTuple = []
                
                # register a message for executing 
                if envars.node_update == "MESSAGE" and hasAnimationNodes():
                    dataTuple = (-1, None, None, None, None)
                
                self.addMethod(envars.node_frameMessage, dataTuple)
                
                for item in bpy.context.scene.OSC_keys:
                    if item.osc_direction == "INPUT" and item.enabled:
                        try:
                            #For ID custom properties (with brackets)
                            if item.id[0:2] == '["' and item.id[-2:] == '"]':
                                dataTuple = (1, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                            #For normal properties
                            #with index in brackets -: i_num
                            elif item.id[-1] == ']':
                                d_p = item.id[:-3]
                                i_num = int(item.id[-2])
                                dataTuple = (3, eval(item.data_path), d_p, i_num, make_tuple(item.osc_index))
                            #without index in brackets
                            else:
                                if isinstance(getattr(eval(item.data_path), item.id), (int, float, str)):
                                    dataTuple = (2, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                elif isinstance(getattr(eval(item.data_path), item.id), (list, tuple)):
                                    dataTuple = (4, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                elif isinstance(getattr(eval(item.data_path), item.id), mathutils.Vector):
                                    dataTuple = (4, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                elif isinstance(getattr(eval(item.data_path), item.id), mathutils.Quaternion):
                                    dataTuple = (4, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))

                            self.addMethod(item.osc_address, dataTuple)

                        except Exception as err:
                            self.report({'WARNING'}, "Register custom handle: object '"+item.data_path+"' with id '"+item.id+"' : {0}".format(err))
                    
                # lets go and find all nodes in all nodetrees that are relevant for us
                nodes_createHandleCollection()
                
                for item in bpy.context.scene.OSC_nodes:
                    if item.osc_direction == "INPUT":
                        try:
                            if item.node_data_type == "FLOAT":
                                dataTuple = (5, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                            elif item.node_data_type == "TUPLE":
                                dataTuple = (6, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))

                            self.addMethod(item.osc_address, dataTuple)
                        except Exception as err:
                            self.report({'WARNING'}, "Register node handle: object '"+item.data_path+"' with id '"+item.id+"' : {0}".format(err))

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
        context.window_manager.event_timer_remove(self._timer)
        bpy.app.timers.unregister(execute_queued_OSC_callbacks)
        
        self.shutDownInputServer(context, envars)
        return {'CANCELLED'}

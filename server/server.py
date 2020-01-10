import bpy
import types
import sys
from select import select
import socket
import errno
import mathutils
from math import radians
from bpy.props import *
from ast import literal_eval as make_tuple

import os
import platform
script_file = os.path.realpath(__file__)
directory = os.path.dirname(script_file)
if directory not in sys.path:
    sys.path.append(directory)
    sys.path.append(os.path.join(directory,'pyliblo',platform.system()))

import liblo

from pythonosc import osc_message_builder
from pythonosc import udp_client
from pythonosc import osc_bundle
from pythonosc import osc_message
from pythonosc import osc_packet
from pythonosc import dispatcher
from pythonosc import osc_server
import threading
import socketserver

from .callbacks import *
from ..nodes.nodes import *

_report= ["",""] #This for reporting OS network error

def make_osc_messages(myOscKeys, myOscMsg):
    for item in myOscKeys:
        if item.osc_direction == "OUTPUT" and item.enabled:
            #print( "sending  :{}".format(item) )
            if item.id[0:2] == '["' and item.id[-2:] == '"]':
                prop = eval(item.data_path+item.id)
            else:
                prop = eval(item.data_path+'.'+item.id)
            if isinstance(prop, mathutils.Vector):
                prop = tuple(prop);
            if isinstance(prop, mathutils.Quaternion):
                prop = tuple(prop);
            if isinstance(prop, mathutils.Euler):
                prop = tuple(prop);
            if isinstance(prop, mathutils.Matrix):
                prop = tuple(prop);
            if prop is None:
                prop = 'None'
            if str(prop) != item.value:
                item.value = str(prop)
                # sort the properties according to the osc_indices
                indices = make_tuple(item.osc_index)
                if prop is not None and not isinstance(prop, str) and len(indices) > 0:
                    prop = tuple(prop[i] for i in indices)
                myOscMsg[item.osc_address] = prop
    return myOscMsg

#######################################
#  Setup PythonOSC Server             #
#######################################

class OSC_OT_PythonOSCServer(bpy.types.Operator):
    bl_idname = "nodeosc.pythonosc_operator"
    bl_label = "OSCMainThread"

    _timer = None
    client = "" #for the sending socket
    count = 0

    #######################################
    #  Sending OSC                        #
    #######################################

    def modal(self, context, event):
        envars = bpy.context.scene.nodeosc_envars
        if envars.status == "Stopped":
            return self.cancel(context)

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
            
            oscMessage = {}
            
            # gather all the ouput bound osc messages
            make_osc_messages(bpy.context.scene.OSC_keys, oscMessage)
            make_osc_messages(bpy.context.scene.OSC_nodes, oscMessage)
            
            # and send them 
            for key, args in oscMessage.items():
                msg = osc_message_builder.OscMessageBuilder(address=key)
                if isinstance(args, tuple):
                    for argum in args:
                        msg.add_arg(argum)
                else:
                    msg.add_arg(args)
                msg = msg.build()
                self.client.send(msg)

        return {'PASS_THROUGH'}

    #######################################
    #  Setup OSC Receiver and Sender      #
    #######################################

    def execute(self, context):
        envars = bpy.context.scene.nodeosc_envars
        global _report

        #For sending
        try:
            self.client = udp_client.UDPClient(envars.udp_out, envars.port_out)
            msg = osc_message_builder.OscMessageBuilder(address="/NodeOSC")
            msg.add_arg("python server started up")
            msg = msg.build()
            self.client.send(msg)
        except OSError as err:
            _report[1] = err
            return {'CANCELLED'}
 
        #Setting up the dispatcher for receiving
        try:
            self.dispatcher = dispatcher.Dispatcher()  
            
            # register a message for executing 
            if envars.node_update == "MESSAGE" and hasAnimationNodes():
                dataTuple = (-1, None, None, None, None)
                self.dispatcher.map(envars.node_frameMessage, OSC_callback_pythonosc, dataTuple)
            
            for item in bpy.context.scene.OSC_keys:
                if item.osc_direction == "INPUT" and item.enabled:
                    #For ID custom properties (with brackets)
                    if item.id[0:2] == '["' and item.id[-2:] == '"]':
                        dataTuple = (1, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                        self.dispatcher.map(item.osc_address, OSC_callback_pythonosc, dataTuple)
                    #For normal properties
                    #with index in brackets -: i_num
                    elif item.id[-1] == ']':
                        d_p = item.id[:-3]
                        i_num = int(item.id[-2])
                        dataTuple = (3, eval(item.data_path), d_p, i_num, make_tuple(item.osc_index))
                        self.dispatcher.map(item.osc_address, OSC_callback_pythonosc, dataTuple)
                    #without index in brackets
                    else:
                        try:
                            if isinstance(getattr(eval(item.data_path), item.id), (int, float, str)):
                                dataTuple = (2, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                self.dispatcher.map(item.osc_address, OSC_callback_pythonosc, dataTuple)
                            elif isinstance(getattr(eval(item.data_path), item.id), (list, tuple)):
                                dataTuple = (4, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                self.dispatcher.map(item.osc_address, OSC_callback_pythonosc, dataTuple)
                            elif isinstance(getattr(eval(item.data_path), item.id), mathutils.Vector):
                                dataTuple = (4, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                self.dispatcher.map(item.osc_address, OSC_callback_pythonosc, dataTuple)
                            elif isinstance(getattr(eval(item.data_path), item.id), mathutils.Quaternion):
                                dataTuple = (4, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                self.dispatcher.map(item.osc_address, OSC_callback_pythonosc, dataTuple)
                        except:
                            print ("Improper setup received: object '"+item.data_path+"' with id'"+item.id+"' is no recognized dataformat")

            # lets go and find all nodes in all nodetrees that are relevant for us
            nodes_createHandleCollection()
            
            for item in bpy.context.scene.OSC_nodes:
                if item.osc_direction == "INPUT":
                    try:
                        if isinstance(getattr(eval(item.data_path), item.id), types.MethodType):
                            dataTuple = (5, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                            self.dispatcher.map(item.osc_address, OSC_callback_pythonosc, dataTuple)
                    except:
                        print ("Improper setup received: object '"+item.data_path+"' with id '"+item.id+"' is no recognized dataformat")

            self.dispatcher.set_default_handler(OSC_callback_pythonosc_undef)
 
            print("Create Server Thread on Port", envars.port_in)
            # creating a blocking UDP Server
            #   Each message will be handled sequentially on the same thread.
            #   the alternative: 
            #       ThreadingOSCUDPServer creates loads of threads 
            #       that are not cleaned up properly
            self.server = osc_server.BlockingOSCUDPServer((envars.udp_in, envars.port_in), self.dispatcher)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.start()
            # register the execute queue method
            bpy.app.timers.register(execute_queued_OSC_callbacks)

        except OSError as err:
            _report[0] = err
            return {'CANCELLED'}

        #inititate the modal timer thread
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(envars.output_rate/1000, window = context.window)
        envars.status = "Running"

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        envars = bpy.context.scene.nodeosc_envars
        context.window_manager.event_timer_remove(self._timer)
        print("OSC server.shutdown()")
        self.server.shutdown()
        envars.status = "Stopped"
        bpy.app.timers.unregister(execute_queued_OSC_callbacks)
        return {'CANCELLED'}


#######################################
#  Setup PyLiblo Server               #
#######################################

class OSC_OT_PyLibloServer(bpy.types.Operator):
    bl_idname = "nodeosc.pyliblo_operator"
    bl_label = "OSCMainThread"

    _timer = None
    client = "" #for the sending socket
    count = 0
    address = None

    #modes_enum = [('Replace','Replace','Replace'),('Update','Update','Update')]
    #bpy.types.WindowManager.addosc_mode = bpy.props.EnumProperty(name = "import mode", items = modes_enum)

    #######################################
    #  Sending OSC                        #
    #######################################

    def modal(self, context, event):
        envars = bpy.context.scene.nodeosc_envars
        if bpy.context.scene.nodeosc_envars.status == "Stopped":
            return self.cancel(context)

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
            #Sending
            
            oscMessage = {}
            
            make_osc_messages(bpy.context.scene.OSC_keys, oscMessage)
            make_osc_messages(bpy.context.scene.OSC_nodes, oscMessage)
            
            for key, args in oscMessage.items():
                msg = liblo.Message(key)
                if isinstance(args, tuple):
                    for argum in args:
                        msg.add(argum)
                else:
                    msg.add(args)
                self.st.send(self.address, msg)
                
        return {'PASS_THROUGH'}

    #######################################
    #  Setup OSC Receiver and Sender      #
    #######################################

    def execute(self, context):
        envars = bpy.context.scene.nodeosc_envars
        global _report

        #Setting up the dispatcher for receiving
        try:
            self.st = liblo.ServerThread(envars.port_in)
            print("Created Server Thread on Port", self.st.port)
            
             # register a message for executing 
            if envars.node_update == "MESSAGE" and hasAnimationNodes():
                dataTuple = (-1, None, None, None, None)
                self.st.add_method(envars.node_frameMessage, None, OSC_callback_pyliblo, dataTuple)

            for item in bpy.context.scene.OSC_keys:
                if item.osc_direction == "INPUT" and item.enabled:
                    #For ID custom properties (with brackets)
                    if item.id[0:2] == '["' and item.id[-2:] == '"]':
                        dataTuple = (1, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                        self.st.add_method(item.address, None, OSC_callback_pyliblo, dataTuple)
                    #For normal properties
                    #with index in brackets -: i_num
                    elif item.id[-1] == ']':
                        d_p = item.id[:-3]
                        i_num = int(item.id[-2])
                        dataTuple = (3, eval(item.data_path), d_p, i_num, make_tuple(item.osc_index))
                        self.st.add_method(item.address, None, OSC_callback_pyliblo, dataTuple)
                    #without index in brackets
                    else:
                        try:
                            if isinstance(getattr(eval(item.data_path), item.id), (int, float, str)):
                                dataTuple = (2, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                self.st.add_method(item.osc_address, None, OSC_callback_pyliblo, dataTuple)
                            elif isinstance(getattr(eval(item.data_path), item.id), (list, tuple)):
                                dataTuple = (4, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                self.st.add_method(item.osc_address, None, OSC_callback_pyliblo, dataTuple)
                            if isinstance(getattr(eval(item.data_path), item.id), mathutils.Vector):
                                dataTuple = (4, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                self.st.add_method(item.osc_address, None, OSC_callback_pyliblo, dataTuple)
                            elif isinstance(getattr(eval(item.data_path), item.id), mathutils.Quaternion):
                                dataTuple = (4, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                self.st.add_method(item.osc_address, None, OSC_callback_pyliblo, dataTuple)
                        except:
                            print ("Improper setup received: object '"+item.data_path+"' with id'"+item.id+"' is no recognized dataformat")

            # lets go and find all nodes in all nodetrees that are relevant for us
            nodes_createHandleCollection()

            for item in bpy.context.scene.OSC_nodes:
                if item.osc_direction == "INPUT":
                    try:
                        if isinstance(getattr(eval(item.data_path), item.id), types.MethodType):
                            dataTuple = (5, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                            self.st.add_method(item.osc_address, None, OSC_callback_pyliblo, dataTuple)
                    except:
                        print ("Improper setup received: object '"+item.data_path+"' with id '"+item.id+"' is no recognized dataformat")

    
            #self.st.add_method(None, None, OSC_callback_unkown)
            self.st.start()
            print("PyLiblo Server started")
            # register the execute queue method
            bpy.app.timers.register(execute_queued_OSC_callbacks)


            #self.server = osc_server.ThreadingOSCUDPServer((envars.addosc_udp_in, envars.addosc_port_in), self.dispatcher)
            #self.server_thread = threading.Thread(target=self.server.serve_forever)
            #self.server_thread.start()
        except OSError as err:
            _report[0] = err
            return {'CANCELLED'}

        #For sending
        try:
            self.address = liblo.Address(envars.udp_out, envars.port_out)
            msg = liblo.Message("/NodeOSC")
            msg.add("pyliblo server started up")
            self.st.send(self.address, msg)
        except OSError as err:
            _report[1] = err
            return {'CANCELLED'}

        #inititate the modal timer thread
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(envars.output_rate/1000, window = context.window)
        envars.status = "Running"

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        envars = bpy.context.scene.nodeosc_envars
        context.window_manager.event_timer_remove(self._timer)
        print("stopping PyLiblo Server..")
        self.st.stop()
        self.st.free()
        #self.server.shutdown()
        # unregister the execute queue method
        bpy.app.timers.unregister(execute_queued_OSC_callbacks)
        envars.status = "Stopped"
        return {'CANCELLED'}

panel_classes = (
    OSC_OT_PythonOSCServer,
    OSC_OT_PyLibloServer,
)

def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(panel_classes):
        bpy.utils.unregister_class(cls)

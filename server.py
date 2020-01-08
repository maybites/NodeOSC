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

from callbacks import *

_report= ["",""] #This for reporting OS network errors

class StartUDP(bpy.types.Operator):
    bl_idname = "nodeosc.startudp"
    bl_label = "Start UDP Connection"
    bl_description ="Start/Stop the OSC engine"

    def execute(self, context):
        global _report
        if bpy.context.scene.nodeosc_envars.port_in == bpy.context.scene.nodeosc_envars.port_out:
            self.report({'INFO'}, "Ports must be different.")
            return{'FINISHED'}
        if bpy.context.scene.nodeosc_envars.status != "Running" :
            preferences = context.preferences
            addon_prefs = preferences.addons[__package__].preferences           
            if addon_prefs.usePyLiblo == False:
                bpy.ops.nodeosc.pythonosc_operator()
            else:
                bpy.ops.nodeosc.pyliblo_operator()
            if _report[0] != '':
                self.report({'INFO'}, "Input error: {0}".format(_report[0]))
                _report[0] = ''
            elif _report[1] != '':
                self.report({'INFO'}, "Output error: {0}".format(_report[1]))
                _report[1] = ''
        else:
            self.report({'INFO'}, "Disconnected !")
            bpy.context.scene.nodeosc_envars.status = "Stopped"
        return{'FINISHED'}

class PickOSCaddress(bpy.types.Operator):
    bl_idname = "nodeosc.pick"
    bl_label = "Pick the last event OSC address"
    bl_options = {'UNDO'}
    bl_description ="Pick the address of the last OSC message received"

    i_addr: bpy.props.StringProperty()

    def execute(self, context):
        last_event = bpy.context.scene.nodeosc_envars.lastaddr
        if len(last_event) > 1 and last_event[0] == "/":
            for item in bpy.context.scene.OSC_keys:
                if item.osc_address == self.i_addr :
                    item.osc_address = last_event
        return{'FINISHED'}

# fill up the OSC_handles with all the current OSC_keys and OSC_nodes
def createServerHandles():
    item = bpy.context.scene.OSC_handles.clear()
    for tmp_item in bpy.context.scene.OSC_keys:
        item = bpy.context.scene.OSC_handles.add()
        item.id = tmp_item.id
        item.data_path = tmp_item.data_path
        item.osc_address = tmp_item.osc_address
        item.osc_type = tmp_item.osc_type
        item.osc_index = tmp_item.osc_index
        item.idx = tmp_item.idx
    for tmp_item in bpy.context.scene.OSC_nodes:
        item = bpy.context.scene.OSC_handles.add()
        item.id = tmp_item.id
        item.data_path = tmp_item.data_path
        item.osc_address = tmp_item.osc_address
        item.osc_type = tmp_item.osc_type
        item.osc_index = tmp_item.osc_index
        item.idx = tmp_item.idx
 
#######################################
#  Setup PythonOSC Server             #
#######################################

class OSC_OT_PythonOSCServer(bpy.types.Operator):
    bl_idname = "nodeosc.pythonosc_operator"
    bl_label = "OSCMainThread"

    _timer = None
    client = "" #for the sending socket
    count = 0

    #modes_enum = [('Replace','Replace','Replace'),('Update','Update','Update')]
    #bpy.types.WindowManager.nodeosc_mode = bpy.props.EnumProperty(name = "import mode", items = modes_enum)

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
            #Sending
            for item in bpy.context.scene.OSC_keys:
                if item.osc_direction == "OUTPUT":
                    #print( "sending  :{}".format(item) )
                    if item.id[0:2] == '["' and item.id[-2:] == '"]':
                        prop = eval(item.data_path+item.id)
                    else:
                        prop = eval(item.data_path+'.'+item.id)

                    if isinstance(prop, mathutils.Vector):
                        prop = list(prop)

                    if isinstance(prop, mathutils.Quaternion):
                        prop = list(prop)

                    if str(prop) != item.value:
                        item.value = str(prop)

                        if item.idx == 0:
                            msg = osc_message_builder.OscMessageBuilder(address=item.osc_address)
                            #print( "sending prop :{}".format(prop) )
                            if isinstance(prop, list):
                                for argmnts in prop:
                                    msg.add_arg(argmnts)
                            else:
                                msg.add_arg(prop)
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
            msg = osc_message_builder.OscMessageBuilder(address="/blender")
            msg.add_arg("Hello from Blender, simple test.")
            msg = msg.build()
            self.client.send(msg)
        except OSError as err:
            _report[1] = err
            return {'CANCELLED'}
 
        #Setting up the dispatcher for receiving
        try:
            self.dispatcher = dispatcher.Dispatcher()  
            for item in bpy.context.scene.OSC_keys:
                if item.osc_direction == "INPUT":
                    #For ID custom properties (with brackets)
                    if item.id[0:2] == '["' and item.id[-2:] == '"]':
                        dataTuple = (1, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                        self.dispatcher.map(item.osc_address, OSC_callback_pythonosc, dataTuple)
                    #For normal properties
                    #with index in brackets -: i_num
                    elif item.id[-1] == ']':
                        d_p = item.id[:-3]
                        i_num = int(item.id[-2])
                        dataTuple = (2, eval(item.data_path), d_p, i_num, make_tuple(item.osc_index))
                        self.dispatcher.map(item.osc_address, OSC_callback_pythonosc, dataTuple)
                    #without index in brackets
                    else:
                        try:
                            if isinstance(getattr(eval(item.data_path), item.id), mathutils.Vector):
                                dataTuple = (3, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                self.dispatcher.map(item.osc_address, OSC_callback_pythonosc, dataTuple)
                            elif isinstance(getattr(eval(item.data_path), item.id), mathutils.Quaternion):
                                dataTuple = (3, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                self.dispatcher.map(item.osc_address, OSC_callback_pythonosc, dataTuple)
                            elif isinstance(getattr(eval(item.data_path), item.id), tuple):
                                dataTuple = (3, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                self.dispatcher.map(item.osc_address, OSC_callback_pythonosc, dataTuple)
                        except:
                            print ("Improper setup received: object '"+item.data_path+"' with id'"+item.id+"' is no recognized dataformat")

            for item in bpy.context.scene.OSC_nodes:
                if item.osc_direction == "INPUT":
                    try:
                        if isinstance(getattr(eval(item.data_path), item.id), types.MethodType):
                            dataTuple = (4, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
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
            """
            #Sending
            for item in bpy.context.scene.OSC_keys:
                #print( "sending  :{}".format(item) )
                if item.id[0:2] == '["' and item.id[-2:] == '"]':
                    prop = eval(item.data_path+item.id)
                else:
                    prop = eval(item.data_path+'.'+item.id)
                if isinstance(prop, mathutils.Vector):
                    prop = list(prop);
                if isinstance(prop, mathutils.Quaternion):
                    prop = list(prop);
                if str(prop) != item.value:
                    item.value = str(prop)
                    if item.idx == 0:
                        msg = osc_message_builder.OscMessageBuilder(address=item.address)
                        #print( "sending prop :{}".format(prop) )
                        if isinstance(prop, list):
                            for argum in prop:
                                msg.add_arg(argum)
                        else:
                            msg.add_arg(prop)
                        msg = msg.build()
                        self.client.send(msg)
            """
        return {'PASS_THROUGH'}

    #######################################
    #  Setup OSC Receiver and Sender      #
    #######################################

    def execute(self, context):
        envars = bpy.context.scene.nodeosc_envars
        global _report

        #For sending
        """
        try:
            self.client = udp_client.UDPClient(envars.udp_out, envars.port_out)
            msg = osc_message_builder.OscMessageBuilder(address="/blender")
            msg.add_arg("Hello from Blender, simple test.")
            msg = msg.build()
            self.client.send(msg)
        except OSError as err:
            _report[1] = err
            return {'CANCELLED'}
        """

        #Setting up the dispatcher for receiving
        try:
            self.st = liblo.ServerThread(envars.port_in)
            print("Created Server Thread on Port", self.st.port)
            for item in bpy.context.scene.OSC_handles:
                if item.osc_direction == "INPUT":
                    #For ID custom properties (with brackets)
                    if item.id[0:2] == '["' and item.id[-2:] == '"]':
                        dataTuple = (1, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                        self.st.add_method(item.address, None, OSC_callback_pyliblo, dataTuple)
                    #For normal properties
                    #with index in brackets -: i_num
                    elif item.id[-1] == ']':
                        d_p = item.id[:-3]
                        i_num = int(item.id[-2])
                        dataTuple = (2, eval(item.data_path), d_p, i_num, make_tuple(item.osc_index))
                        self.st.add_method(item.address, None, OSC_callback_pyliblo, dataTuple)
                    #without index in brackets
                    else:
                        try:
                            if isinstance(getattr(eval(item.data_path), item.id), mathutils.Vector):
                                dataTuple = (3, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                self.st.add_method(item.osc_address, None, OSC_callback_pyliblo, dataTuple)
                            elif isinstance(getattr(eval(item.data_path), item.id), mathutils.Quaternion):
                                dataTuple = (3, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                                self.st.add_method(item.osc_address, None, OSC_callback_pyliblo, dataTuple)
                        except:
                            print ("Improper setup received: object '"+item.data_path+"' with id'"+item.id+"' is no recognized dataformat")

            for item in bpy.context.scene.OSC_nodes:
                if item.osc_direction == "INPUT":
                    try:
                        if isinstance(getattr(eval(item.data_path), item.id), types.MethodType):
                            dataTuple = (4, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                            self.st.add_method(item.osc_address, None, OSC_callback_pythonosc, dataTuple)
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


        #inititate the modal timer thread
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(envars.output_rate/1000, window = context.window)
        envars.status = "Running"

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        envars = bpy.context.scene.nodeosc_envars
        context.window_manager.event_timer_remove(self._timer)
        print("self.st.free():")
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
    StartUDP,
    PickOSCaddress,
)

def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(panel_classes):
        bpy.utils.unregister_class(cls)

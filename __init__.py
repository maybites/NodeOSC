#    This Addon for Blender implements realtime OSC controls in the viewport
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#    Copyright (C) 2018  maybites <https://github.com/maybites/>
#
#    Copyright (C) 2017  AG6GR <https://github.com/AG6GR/>
#
#    Copyright (C) 2015  JPfeP <http://www.jpfep.net/>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****

# TODO:
#
# attach the timer to the context window or not ?
# pbm not set to None du modal timer when opening a new blend file
# Bool are not part of OSC 1.0 (only later as extension)
# Deal with tupple (x,y,z) or (r,g,b) usr "type(key).__name__" for Vector, Euler, etc...
# Monitoring in console report error "Improper..." due to Monitoring refresh hack overhead


bl_info = {
    "name": "NodeOSC",
    "author": "maybites",
    "version": (0, 19),
    "blender": (2, 80, 0),
    "location": "View3D > Tools > NodeOSC",
    "description": "Realtime control of Blender using OSC protocol",
    "warning": "Please read the disclaimer about network security on the download site.",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"}

import bpy
import sys
from select import select
import socket
import errno
import mathutils
from math import radians
from bpy.props import *
from ast import literal_eval as make_tuple

import os
script_file = os.path.realpath(__file__)
directory = os.path.dirname(script_file)
if directory not in sys.path:
   sys.path.append(directory)

from pythonosc import osc_message_builder
from pythonosc import udp_client
from pythonosc import osc_bundle
from pythonosc import osc_message
from pythonosc import osc_packet
from pythonosc import dispatcher
from pythonosc import osc_server
import threading
import socketserver
from bpy.app.handlers import persistent

_report= ["",""] #This for reporting OS network errors

#######################################
#  Setup OSC                          #
#######################################

class OSC_Reading_Sending(bpy.types.Operator):
    bl_idname = "nodeosc.modal_timer_operator"
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
        if bpy.context.scene.NodeOSC_envVars.status == "Stopped":
            return self.cancel(context)

        if event.type == 'TIMER':
            #hack to refresh the GUI
            bcw = bpy.context.scene.NodeOSC_envVars
            self.count = self.count + bcw.nodeosc_rate
            if self.count >= 500:
                self.count = 0
                if bpy.context.scene.NodeOSC_envVars.nodeosc_monitor == True:
                    for window in bpy.context.window_manager.windows:
                        screen = window.screen
                        for area in screen.areas:
                            if area.type == 'VIEW_3D':
                                area.tag_redraw()
            #Sending
            for item in bpy.context.scene.OSC_keys:
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
        global _report
        bcw = bpy.context.scene.NodeOSC_envVars

        #For sending
        try:
            self.client = udp_client.UDPClient(bcw.nodeosc_udp_out, bcw.nodeosc_port_out)
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
                    except:
                        print ("Improper setup received: object '"+item.data_path+"' with id'"+item.id+"' is no recognized dataformat")
 
            self.dispatcher.set_default_handler(OSC_callback_pythonosc_undef)
 
            print("Create Server Thread on Port", bcw.nodeosc_port_in)
            # creating a blocking UDP Server
            #   Each message will be handled sequentially on the same thread.
            #   the alternative: 
            #       ThreadingOSCUDPServer creates loads of threads 
            #       that are not cleaned up properly
            self.server = osc_server.BlockingOSCUDPServer((bcw.nodeosc_udp_in, bcw.nodeosc_port_in), self.dispatcher)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.start()
            # register the execute queue method
            bpy.app.timers.register(execute_queued_OSC_callbacks)

        except OSError as err:
            _report[0] = err
            return {'CANCELLED'}


        #inititate the modal timer thread
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(bcw.nodeosc_rate/1000, window = context.window)
        bpy.context.scene.NodeOSC_envVars.status = "Running"

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        print("OSC server.shutdown()")
        self.server.shutdown()
        bpy.context.scene.NodeOSC_envVars.status = "Stopped"
        bpy.app.timers.unregister(execute_queued_OSC_callbacks)
        return {'CANCELLED'}
                 

class StartUDP(bpy.types.Operator):
    bl_idname = "nodeosc.startudp"
    bl_label = "Start UDP Connection"
    bl_description ="Start the OSC engine"

    def execute(self, context):
        global _report
        if bpy.context.scene.NodeOSC_envVars.nodeosc_port_in == bpy.context.scene.NodeOSC_envVars.nodeosc_port_out:
            self.report({'INFO'}, "Ports must be different.")
            return{'FINISHED'}
        if bpy.context.scene.NodeOSC_envVars.status != "Running" :
            bpy.ops.nodeosc.modal_timer_operator()
            if _report[0] != '':
                self.report({'INFO'}, "Input error: {0}".format(_report[0]))
                _report[0] = ''
            elif _report[1] != '':
                self.report({'INFO'}, "Output error: {0}".format(_report[1]))
                _report[1] = ''
        else:
            self.report({'INFO'}, "Already connected !")
        return{'FINISHED'}

class StopUDP(bpy.types.Operator):
    bl_idname = "nodeosc.stopudp"
    bl_label = "Stop UDP Connection"
    bl_description ="Stop the OSC engine"

    def execute(self, context):
        self.report({'INFO'}, "Disconnected !")
        bpy.context.scene.NodeOSC_envVars.status = "Stopped"
        return{'FINISHED'}

class PickOSCaddress(bpy.types.Operator):
    bl_idname = "nodeosc.pick"
    bl_label = "Pick the last event OSC address"
    bl_options = {'UNDO'}
    bl_description ="Pick the address of the last OSC message received"

    i_addr: bpy.props.StringProperty()

    def execute(self, context):
        last_event = bpy.context.scene.NodeOSC_envVars.nodeosc_lastaddr
        if len(last_event) > 1 and last_event[0] == "/":
            for item in bpy.context.scene.OSC_keys:
                if item.osc_address == self.i_addr :
                    item.osc_address = last_event
        return{'FINISHED'}



#Restore saved settings
@persistent
def nodeosc_handler(scene):
    if bpy.context.scene.NodeOSC_envVars.nodeosc_autorun == True:
        bpy.ops.nodeosc.startudp()


classes = (
    OSC_Reading_Sending,
    StartUDP,
    StopUDP,
    PickOSCaddress,
)

from . import preferences
from . import keys
from .AN import auto_load
auto_load.init()

from callbacks import *
from . import panels

def register():
    preferences.register()
    keys.register()
    panels.register()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_post.append(nodeosc_handler)
    auto_load.register()

def unregister():
    auto_load.unregister()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    panels.unregister()
    keys.unregister()
    preferences.unregister()

if __name__ == "__main__":
    register()

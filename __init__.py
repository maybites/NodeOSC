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
import json
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

#For saving/restoring settings in the blendfile
def upd_settings_sub(n):
    text_settings = None
    for text in bpy.data.texts:
        if text.name == '.nodeosc_settings':
            text_settings = text
    if text_settings == None:
        bpy.ops.text.new()
        text_settings = bpy.data.texts[-1]
        text_settings.name = '.nodeosc_settings'
        text_settings.write("\n\n\n\n\n\n")
    if n==0:
        text_settings.lines[0].body = str(int(bpy.context.window_manager.nodeosc_monitor))
    elif n==1:
        text_settings.lines[1].body = str(bpy.context.window_manager.nodeosc_port_in)
    elif n==2:
        text_settings.lines[2].body = str(bpy.context.window_manager.nodeosc_port_out)
    elif n==3:
        text_settings.lines[3].body = str(bpy.context.window_manager.nodeosc_rate)
    elif n==4:
        text_settings.lines[4].body = bpy.context.window_manager.nodeosc_udp_in
    elif n==5:
        text_settings.lines[5].body = bpy.context.window_manager.nodeosc_udp_out
    elif n==6:
        text_settings.lines[6].body = str(int(bpy.context.window_manager.nodeosc_autorun))

def upd_setting_0():
    upd_settings_sub(0)

def upd_setting_1():
    upd_settings_sub(1)

def upd_setting_2():
    upd_settings_sub(2)

def upd_setting_3():
    upd_settings_sub(3)

def upd_setting_4():
    upd_settings_sub(4)

def upd_setting_5():
    upd_settings_sub(5)

def upd_setting_6():
    upd_settings_sub(6)

#######################################
#  Setup OSC                          #
#######################################

class OSC_Reading_Sending(bpy.types.Operator):
    bl_idname = "nodeosc.modal_timer_operator"
    bl_label = "OSCMainThread"

    _timer = None
    client = "" #for the sending socket
    count = 0

    def upd_trick_nodeosc_monitor(self,context):
        upd_setting_0()

    def upd_trick_portin(self,context):
        upd_setting_1()

    def upd_trick_portout(self,context):
        upd_setting_2()

    def upd_trick_rate(self,context):
        upd_setting_3()

    def upd_trick_nodeosc_udp_in(self,context):
        upd_setting_4()

    def upd_trick_nodeosc_udp_out(self,context):
        upd_setting_5()

    def upd_trick_nodeosc_autorun(self,context):
        upd_setting_6()

    bpy.types.WindowManager.nodeosc_udp_in  = bpy.props.StringProperty(default="127.0.0.1", update=upd_trick_nodeosc_udp_in, description='The IP of the interface of your Blender machine to listen on, set to 0.0.0.0 for all of them')
    bpy.types.WindowManager.nodeosc_udp_out = bpy.props.StringProperty(default="127.0.0.1", update=upd_trick_nodeosc_udp_out, description='The IP of the destination machine to send messages to')
    bpy.types.WindowManager.nodeosc_port_in = bpy.props.IntProperty(default=9001, min=0, max=65535, update=upd_trick_portin, description='The input network port (0-65535)')
    bpy.types.WindowManager.nodeosc_port_out = bpy.props.IntProperty(default=9002, min=0, max= 65535, update=upd_trick_portout, description='The output network port (0-65535)')
    bpy.types.WindowManager.nodeosc_rate = bpy.props.IntProperty(default=10 ,description="The refresh rate of the engine (millisecond)", min=1, update=upd_trick_rate)
    bpy.types.WindowManager.status = bpy.props.StringProperty(default="Stopped", description='Show if the engine is running or not')
    bpy.types.WindowManager.nodeosc_monitor = bpy.props.BoolProperty(description="Display the current value of your keys, the last message received and some infos in console", update=upd_trick_nodeosc_monitor)
    bpy.types.WindowManager.nodeosc_autorun = bpy.props.BoolProperty(description="Start the OSC engine automatically after loading a project", update=upd_trick_nodeosc_autorun)
    bpy.types.WindowManager.nodeosc_lastaddr = bpy.props.StringProperty(description="Display the last OSC address received")
    bpy.types.WindowManager.nodeosc_lastpayload = bpy.props.StringProperty(description="Display the last OSC message content")

    #modes_enum = [('Replace','Replace','Replace'),('Update','Update','Update')]
    #bpy.types.WindowManager.nodeosc_mode = bpy.props.EnumProperty(name = "import mode", items = modes_enum)

    #######################################
    #  Sending OSC                        #
    #######################################

    def modal(self, context, event):
        if context.window_manager.status == "Stopped":
            return self.cancel(context)

        if event.type == 'TIMER':
            #hack to refresh the GUI
            bcw = bpy.context.window_manager
            self.count = self.count + bcw.nodeosc_rate
            if self.count >= 500:
                self.count = 0
                if bpy.context.window_manager.nodeosc_monitor == True:
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
                        msg = osc_message_builder.OscMessageBuilder(address=item.address)
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
        bcw = bpy.context.window_manager

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
                    self.dispatcher.map(item.address, OSC_callback_pythonosc, dataTuple)
                #For normal properties
                #with index in brackets -: i_num
                elif item.id[-1] == ']':
                    d_p = item.id[:-3]
                    i_num = int(item.id[-2])
                    dataTuple = (2, eval(item.data_path), d_p, i_num, make_tuple(item.osc_index))
                    self.dispatcher.map(item.address, OSC_callback_pythonosc, dataTuple)
                #without index in brackets
                else:
                    try:
                        if isinstance(getattr(eval(item.data_path), item.id), mathutils.Vector):
                            dataTuple = (3, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                            self.dispatcher.map(item.address, OSC_callback_pythonosc, dataTuple)
                        elif isinstance(getattr(eval(item.data_path), item.id), mathutils.Quaternion):
                            dataTuple = (3, eval(item.data_path), item.id, item.idx, make_tuple(item.osc_index))
                            self.dispatcher.map(item.address, OSC_callback_pythonosc, dataTuple)
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
        context.window_manager.status = "Running"

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        print("OSC server.shutdown()")
        self.server.shutdown()
        context.window_manager.status = "Stopped"
        bpy.app.timers.unregister(execute_queued_OSC_callbacks)
        return {'CANCELLED'}
                 

class StartUDP(bpy.types.Operator):
    bl_idname = "nodeosc.startudp"
    bl_label = "Start UDP Connection"
    bl_description ="Start the OSC engine"

    def execute(self, context):
        global _report
        if context.window_manager.nodeosc_port_in == context.window_manager.nodeosc_port_out:
            self.report({'INFO'}, "Ports must be different.")
            return{'FINISHED'}
        if bpy.context.window_manager.status != "Running" :
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
        bpy.context.window_manager.status = "Stopped"
        return{'FINISHED'}

class PickOSCaddress(bpy.types.Operator):
    bl_idname = "nodeosc.pick"
    bl_label = "Pick the last event OSC address"
    bl_options = {'UNDO'}
    bl_description ="Pick the address of the last OSC message received"

    i_addr: bpy.props.StringProperty()

    def execute(self, context):
        last_event = bpy.context.window_manager.nodeosc_lastaddr
        if len(last_event) > 1 and last_event[0] == "/":
            for item in bpy.context.scene.OSC_keys:
                if item.address == self.i_addr :
                    item.address = last_event
        return{'FINISHED'}



#Restore saved settings
@persistent
def nodeosc_handler(scene):
    for text in bpy.data.texts:
        if text.name == '.nodeosc_settings':
            try:
                bpy.context.window_manager.nodeosc_monitor = int(text.lines[0].body)
            except:
                pass
            try:
                bpy.context.window_manager.nodeosc_port_in  = int(text.lines[1].body)
            except:
                pass
            try:
                bpy.context.window_manager.nodeosc_port_out = int(text.lines[2].body)
            except:
                pass
            try:
                bpy.context.window_manager.nodeosc_rate = int(text.lines[3].body)
            except:
                bpy.context.window_manager.nodeosc_rate = 10
            if text.lines[4].body != '':
                bpy.context.window_manager.nodeosc_udp_in = text.lines[4].body
            if text.lines[5].body != '':
                bpy.context.window_manager.nodeosc_udp_out = text.lines[5].body
            try:
                bpy.context.window_manager.nodeosc_autorun = int(text.lines[6].body)
            except:
                pass

            #if error_device == True:
            #    bpy.context.window_manager.nodeosc_autorun = False

            if bpy.context.window_manager.nodeosc_autorun == True:
                bpy.ops.nodeosc.startudp()


classes = (
    OSC_Reading_Sending,
    StartUDP,
    StopUDP,
    PickOSCaddress,
)

from . import preferences
from . import keys
from . import panels
from callbacks import *
from .AN import auto_load
auto_load.init()

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

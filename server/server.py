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

import os
import platform
script_file = os.path.realpath(__file__)
directory = os.path.dirname(script_file)
if directory not in sys.path:
    sys.path.append(directory)

from oscpy.client import OSCClient
from oscpy.server import OSCThreadServer

from pythonosc import osc_message_builder
from pythonosc import udp_client
from pythonosc import osc_bundle
from pythonosc import osc_message
from pythonosc import osc_packet
from pythonosc import dispatcher
from pythonosc import osc_server

import threading
import socketserver

from ._base import *

from .callbacks import *
from ..nodes.nodes import *

#######################################
#  Setup OSCPy Server                 #
#######################################

class OSC_OT_OSCPyServer(OSC_OT_OSCServer):
    bl_idname = "nodeosc.oscpy_operator"
    bl_label = "OSCMainThread"

    _timer = None
    count = 0

    #####################################
    # CUSTOMIZEABLE FUNCTIONS:

    inputServer = "" #for the receiving socket
    outputServer = "" #for the sending socket
            
    # setup the sending server
    def setupInputServer(self, context, envars):
        self.dispatcher = dispatcher.Dispatcher()   
 
    # setup the receiving server
    def setupOutputServer(self, context, envars):
        #For sending
        self.outputServer = OSCClient(envars.udp_out, envars.port_out)
        self.outputServer.send_message(b'/NodeOSC', [b'Python server started up'])     
        print("OSCPy Server sended test message to " + envars.udp_out + " on port " + str(envars.port_out))

    def sendingOSC(self, context, event):

        oscMessage = {}
        
        # gather all the ouput bound osc messages
        make_osc_messages(bpy.context.scene.NodeOSC_outputs, oscMessage)
         
        # and send them 
        for key, args in oscMessage.items():
            values = []
            if isinstance(args, (tuple, list)):
                for argum in args:
                    if type(argum) == str:
                        argum = bytes(argum, encoding='utf-8')
                    values.append(argum)
            else:
                if type(args) == str:
                    args = bytes(args, encoding='utf-8')
                values.append(args)
            self.outputServer.send_message(bytes(key, encoding='utf-8'), values)
  
    # add method 
    def addMethod(self, address, data):
        pass #already set during creation of inputserver
 
    # add default method 
    def addDefaultMethod(self):
        pass #already set during creation of inputserver
    
    # start receiving 
    def startupInputServer(self, context, envars):
        print("Create OscPy Thread...")
        # creating a blocking UDP Server
        #   Each message will be handled sequentially on the same thread.
        self.inputServer = OSCThreadServer(encoding='utf8', default_handler=OSC_callback_oscpy)
        sock = self.inputServer.listen(address=envars.udp_in, port=envars.port_in, default=True)
        print("... server started on ", envars.port_in)

    # stop receiving
    def shutDownInputServer(self, context, envars):
        print("OSCPy Server is shutting down...")
        self.inputServer.stop()                 # Stop default socket
        print("  stopping all sockets...")
        self.inputServer.stop_all()             # Stop all sockets
        print("  terminating server...")
        self.inputServer.terminate_server()     # Request the handler thread to stop looping
        self.inputServer.join_server()          # Wait for the handler thread to finish pending tasks and exit
        print("... OSCPy Server is shutdown")
 
 
#######################################
#  Setup PythonOSC Server             #
#######################################

class OSC_OT_PythonOSCServer(OSC_OT_OSCServer):
    bl_idname = "nodeosc.pythonosc_operator"
    bl_label = "OSCMainThread"

    _timer = None
    count = 0

    #####################################
    # CUSTOMIZEABLE FUNCTIONS:

    inputServer = "" #for the receiving socket
    outputServer = "" #for the sending socket
    dispatcher = "" #dispatcher function
            
    # setup the sending server
    def setupInputServer(self, context, envars):
        self.dispatcher = dispatcher.Dispatcher()   
 
    # setup the receiving server
    def setupOutputServer(self, context, envars):
        #For sending
        self.outputServer = udp_client.UDPClient(envars.udp_out, envars.port_out)
        msg = osc_message_builder.OscMessageBuilder(address="/NodeOSC")
        msg.add_arg("Python server started up")
        msg = msg.build()
        self.outputServer.send(msg)     
        print("Python Server sended test message to " + envars.udp_out + " on port " + str(envars.port_out))

    def sendingOSC(self, context, event):

        oscMessage = {}
        
        # gather all the ouput bound osc messages
        make_osc_messages(bpy.context.scene.NodeOSC_outputs, oscMessage)
         
        # and send them 
        for key, args in oscMessage.items():
            msg = osc_message_builder.OscMessageBuilder(address=key)
            if isinstance(args, (tuple, list)):
                for argum in args:
                    msg.add_arg(argum)
            else:
                msg.add_arg(args)
            msg = msg.build()
            self.outputServer.send(msg)
  
    # add method 
    def addMethod(self, address, data):
        self.dispatcher.map(address, OSC_callback_pythonosc, data)
 
    # add default method 
    def addDefaultMethod(self):
        self.dispatcher.set_default_handler(OSC_callback_pythonosc_undef)
    
    # start receiving 
    def startupInputServer(self, context, envars):
        print("Create Python Server Thread...")
        # creating a blocking UDP Server
        #   Each message will be handled sequentially on the same thread.
        #   the alternative: 
        #       ThreadingOSCUDPServer creates loads of threads 
        #       that are not cleaned up properly
        self.inputServer = osc_server.BlockingOSCUDPServer((envars.udp_in, envars.port_in), self.dispatcher)
        self.server_thread = threading.Thread(target=self.inputServer.serve_forever)
        self.server_thread.start()
        print("... server started on ", envars.port_in)

    # stop receiving
    def shutDownInputServer(self, context, envars):
        self.inputServer.shutdown()
        print("Python Server is shutdown")
 
 
panel_classes = (
    OSC_OT_OSCPyServer,
    OSC_OT_PythonOSCServer,
)

def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(panel_classes):
        bpy.utils.unregister_class(cls)

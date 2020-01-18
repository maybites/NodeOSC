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

from ._base import *

from .callbacks import *
from ..nodes.nodes import *

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
 
 

#######################################
#  Setup PyLiblo Server               #
#######################################

class OSC_OT_PyLibloServer(OSC_OT_OSCServer):
    bl_idname = "nodeosc.pyliblo_operator"
    bl_label = "OSCMainThread"

    _timer = None
    count = 0

    #####################################
    # CUSTOMIZEABLE FUNCTIONS:

    st = "" #for the input and output server
    address = None
            
    # setup the sending server
    def setupInputServer(self, context, envars):
        self.st = liblo.ServerThread(envars.port_in)
        print("Created Server Thread on Port", self.st.port)
 
    # setup the receiving server
    def setupOutputServer(self, context, envars):
        #For sending
        self.address = liblo.Address(envars.udp_out, envars.port_out)
        msg = liblo.Message("/NodeOSC")
        msg.add("pyliblo server started up")
        self.st.send(self.address, msg)
        print("PyLiblo Server sended test message to " + envars.udp_out + " on port " + str(envars.port_out))

    def sendingOSC(self, context, event):
        oscMessage = {}
        
        # gather all the ouput bound osc messages
        make_osc_messages(bpy.context.scene.NodeOSC_outputs, oscMessage)
        
        # and send them 
        for key, args in oscMessage.items():
            msg = liblo.Message(key)
            if isinstance(args, (tuple, list)):
                for argum in args:
                    msg.add(argum)
            else:
                msg.add(args)
            self.st.send(self.address, msg)
           
    # add method 
    def addMethod(self, address, data):
        self.st.add_method(address, None, OSC_callback_pyliblo, data)
 
    # add default method 
    def addDefaultMethod(self):
        pass
    
    # start receiving 
    def startupInputServer(self, context, envars):
        print("PyLiblo Server starting up....")
        self.st.start()
        print("... server started", envars.port_in)

    # stop receiving
    def shutDownInputServer(self, context, envars):
        self.st.stop()
        self.st.free()
        print("PyLiblo Server is shutdown.")


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

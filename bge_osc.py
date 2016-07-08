#    This module for the Blender Game Engine implements OSC support 
#
# ***** BEGIN GPL LICENSE BLOCK *****
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
#
# Version: 0.3
#
# TODO

# faire un try si erreur sur la reception type mismatch
# et si blenderplayer ?
# tester si le callback ne loupe pas des valeur si reception entre 2 frames
# pbm de coherence, si on ne lit pas le dict osc_in avec la fonction idoine les valeur restent en memoire-> vider le dictionnaire a chaque frame ?

import bge
from bge import logic
from pythonosc import osc_message_builder
from pythonosc import udp_client
from pythonosc import osc_bundle
from pythonosc import osc_message
from pythonosc import osc_packet
from pythonosc import dispatcher
from pythonosc import osc_server
import threading
import socketserver


# The default settings for internet 
UDP_OUT_IP = '127.0.0.1'  
UDP_IN_IP = '127.0.0.1'  
UDP_IN_PORT = 9003
UDP_OUT_PORT = 9004

# This will add a common address before the game properties object 
PREFIX = ''

# This is for adding the name object to the address
ADD_NAME = False

# To print in the console OSC messages
DEBUG_IN = False
DEBUG_OUT = False
    
    
IO="BOTH"    
    
# Will parse the settings 
def settings(controller):
    global UDP_OUT_IP,UDP_IN_IP,UDP_IN_PORT,UDP_OUT_PORT,PREFIX,ADD_NAME,DEBUG_IN,DEBUG_OUT,IO
    obj = controller.owner
    for prop in obj.getPropertyNames():
        if prop == 'UDP_OUT_IP':
            UDP_OUT_IP = obj[prop] 
        elif prop == 'UDP_IN_IP':
            UDP_IN_IP = obj[prop]
        elif prop == 'UDP_IN_PORT':
            UDP_IN_PORT = int(obj[prop])
        elif prop == 'UDP_OUT_PORT':    
            UDP_OUT_PORT = int(obj[prop])
        elif prop == 'DEBUG_IN':
            DEBUG_IN = obj[prop]
        elif prop == 'DEBUG_OUT':
            DEBUG_OUT = obj[prop]           
        elif prop == 'PREFIX':
            if len(obj[prop]) > 0:
                if obj[prop][0] == "/":
                    PREFIX = obj[prop]
                else:
                    PREFIX = "/"+obj[prop]
        elif prop == 'ADD_NAME':
            ADD_NAME = obj[prop]
        elif prop == 'IO':
            IO = obj[prop]

controller = logic.getCurrentController()            
settings(controller) 

# These 2 dictionnaries are for the script mode 
bge.logic.osc_out = {}
bge.logic.osc_in = {}

# For setting the engine
def io(cont):
    global IO
    scene = bge.logic.getCurrentScene()
    sens  = cont.sensors[0]
    obj = controller.owner
    for prop in obj.getPropertyNames():
        if prop == 'IO':
            IO= obj[prop] 
    
    if IO == "OUT" or IO == "BOTH":
        client_out(cont)
    else:
        pass

        

# For receiving OSC messages (server side)
def BGE_OSC_callback(*args):
    global PREFIX,ADD_NAME,DEBUG_IN
    scene = bge.logic.getCurrentScene()
    
    if DEBUG_IN:
        print (args)
          
    if len(args) <= 2 :  
        # for the simple game properties
        for obj in scene.objects:
            if ADD_NAME == True:
                pre_addr = PREFIX+"/"+obj.name
            else:
                pre_addr = PREFIX
            for prop in obj.getPropertyNames():
                if pre_addr+prop == args[0]: 
                    obj[prop]=args[1]    
    else:
        # for the script mode
        try:
            bge.logic.osc_in[args[0]]=args[1:]
        except:
            pass
# The server for receiving OSC messages 
class Main:   
    def __init__(self):
        if IO == 'IN' or IO == 'BOTH':
            self.dispatcher = dispatcher.Dispatcher()
            self.dispatcher.set_default_handler(BGE_OSC_callback)
            self.server = osc_server.ThreadingOSCUDPServer((UDP_IN_IP, UDP_IN_PORT), self.dispatcher)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server.allow_reuse_address
            self.server_thread.start()
            print('OSC INPUT ENABLED, UDP_IN_IP: '+UDP_IN_IP+', UDP_IN_PORT: '+str(UDP_IN_PORT))
        if IO == 'OUT' or IO == 'BOTH':
            print('OSC OUTPUT ENABLED, UDP_OUT_IP: '+UDP_OUT_IP+', UDP_OUT_PORT: '+str(UDP_OUT_PORT))
        if PREFIX !='':
            print('PREFIX: '+PREFIX)
        if ADD_NAME == True:
            print('ADD_NAME: '+str(ADD_NAME))
    
    def stop(self):
        if IO == 'IN' or IO == 'BOTH':
            self.server.shutdown()
        
    def __del__(self):
        self.stop()

logic.main = Main()


#These 2 functions are for accessing the "script" dictionnaries
def receive(key):
    if key in bge.logic.osc_in:
        if ADD_NAME == True:
            cont = bge.logic.getCurrentController()
            obj = cont.owner
            pre_addr = PREFIX+"/"+obj.name
        else:
            pre_addr = PREFIX
        val = bge.logic.osc_in[pre_addr+key]
        del bge.logic.osc_in[pre_addr+key]
    else:
        val = None
    return val

def send(key,values):
    if ADD_NAME == True:
        cont = bge.logic.getCurrentController()
        obj = cont.owner
        pre_addr = PREFIX+"/"+obj.name
    else:
        pre_addr = PREFIX
    bge.logic.osc_out[pre_addr+key]=values
    


# For sending data   
def client_out(cont):
    bge_client = udp_client.UDPClient(UDP_OUT_IP, UDP_OUT_PORT) 
    scene = bge.logic.getCurrentScene()
    sens  = cont.sensors[0]
         
    # for the simple bge properties    
    for obj in scene.objects:
        if ADD_NAME == True:
            pre_addr = PREFIX+"/"+obj.name
        else:
            pre_addr = PREFIX
        for prop in obj.getPropertyNames():
            if prop[0] == '/': 
                msg = osc_message_builder.OscMessageBuilder(address=pre_addr+prop)
                msg.add_arg(obj[prop])
                msg = msg.build()
                bge_client.send(msg)    
                if DEBUG_OUT:
                    print(pre_addr+prop,obj[prop])
                
    # for the script mode
    for keys in list(bge.logic.osc_out):
        values = bge.logic.osc_out[keys]
        if DEBUG_OUT:
            print (keys,values)
            
        msg = osc_message_builder.OscMessageBuilder(address=keys)
        for item in values:
            msg.add_arg(item)
        msg = msg.build()
        bge_client.send(msg) 
        
        #This to clear the sent value from the dictionnary
        del bge.logic.osc_out[keys]
                
                
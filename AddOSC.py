#    This Addon for Blender implements realtime OSC controls in the viewport
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

#TODO:


#-implémenter la conversion pour les autres types que Vector,Euler,Quaternion à l'import ou convertir à la volée les virgules en "|"
#-Implémenter la possibilité d'ajouter des clés à distance (pareil BGE) ?
#----ADDOSC

#-inventer un system "par objet" que l'on puisse se servir de sa surface de controle sur chaque objet selectionné sans avoir à tout refaire pour chaque object
#-pas prendre des props de scene pour le serveur ou la liste des props !
#-actuellement le bloc qui separe les x y z est "commented out"
#-intercepter les erreurs quand les adress OSC sont vides
#-grosse merde actuellement avec les adress reseau "already in use"
#-pbm avec l'adresse au niveau de l'envoi, meme quand on la met sur 127.0.0.2 ca envoit encore sur 127.0.0.1
# monitoring of the values
#-type(key).__name__

bl_info = {
    "name": "AddOSC",
    "author": "JPfeP",
    "version": (0, 6),
    "blender": (2, 6, 6),
    "location": "",
    "description": "Realtime control of Blender using OSC protocol",
    "warning": "beta quality",
    "wiki_url": "http://www.jpfep.net/en-us/pages/addosc/",
    "tracker_url": "",
    "category": "System"}

import bpy
import sys
#from sys import exit
from select import select
from bpy.utils import register_module, unregister_module
import socket
import errno
from math import radians
from bpy.props import *

from pythonosc import osc_message_builder
from pythonosc import udp_client
from pythonosc import osc_bundle
from pythonosc import osc_message
from pythonosc import osc_packet
from pythonosc import dispatcher
from pythonosc import osc_server
import threading
import socketserver


#Quelques variables globales
thread_run= 0



def mycallback(arg1,arg2):
    id = int(arg1.split("/")[-1:][0])
    bcs = bpy.context.scene
    strtoexec = "bpy.data." + bcs.OSC_keys[id].name + "=" + str(arg2)
    try:
        exec(strtoexec)
    except:
        print ("Improper message received")

class OSC_Readind_Sending(bpy.types.Operator):
    bl_idname = "addosc.modal_timer_operator"
    bl_label = "OSCMainThread"
    
    _timer = None 
    client = "" #for the sending socket
    
    bpy.types.Scene.udp_addr = bpy.props.StringProperty(default="127.0.0.1")
    bpy.types.Scene.port_in = bpy.props.IntProperty(default=9001, min=0)
    bpy.types.Scene.port_out = bpy.props.IntProperty(default=9002, min=0)
    bpy.types.Scene.osc_rate = bpy.props.IntProperty(default=100 ,description="refresh rate (ms)", min=0)
    bpy.types.Scene.status = bpy.props.StringProperty(default="Stopped")
    bpy.types.WindowManager.monitor = bpy.props.BoolProperty(description="Display the current value of your keys")
    
    def modal(self, context, event):
        global thread_run 
       
        if thread_run == 0 :
            print("exit")
            return self.cancel(context)	  
       
        if event.type == 'TIMER':
            #Reception is no more done in the timer modal operator, see the handler 

            #Sending
            for item in bpy.context.scene.OSC_keys:
                prop = str(eval("bpy.data."+item.name))
                if prop != item.value:
                    msg = osc_message_builder.OscMessageBuilder(address=item.address+"/"+str(item.ID))
                    msg.add_arg(eval("bpy.data." + item.name))
                    msg = msg.build()
                    self.client.send(msg)
                    item.value = prop    
   
        return {'PASS_THROUGH'}      
      
    def execute(self, context):
        #Setting up the dispatcher for receiving
        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.set_default_handler(mycallback)
        bcs = bpy.context.scene
        self.server = osc_server.ThreadingOSCUDPServer((bcs.udp_addr, bcs.port_in), self.dispatcher)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.start()
        
        #And for sending
        self.client = udp_client.UDPClient(bcs.udp_addr, bcs.port_out) 
        
        
        #Warn if no keys ?
 
        #inititate the modal timer thread
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(bcs.osc_rate/1000, context.window)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        self.server.shutdown()
        return {'CANCELLED'}

class OSC_UI_Panel(bpy.types.Panel):
    bl_label = "OSC Link"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "AddOSC"
 
    def draw(self, context):
        layout = self.layout
        layout.prop(bpy.context.scene, 'udp_addr', text="Input address")
        layout.prop(bpy.context.scene, 'port_in', text="Input port")
        layout.prop(bpy.context.scene, 'port_out', text="Outport port")
        layout.prop(bpy.context.scene, 'osc_rate', text="Update rate(ms)")    
        layout.prop(bpy.context.scene, 'status', text="Running Status")
        layout.prop(bpy.context.window_manager, 'monitor')
        layout.operator("addosc.startudp", text='Start')
        layout.operator("addosc.stopudp", text='Stop')
        layout.separator()
        layout.prop(bpy.context.scene, 'defaultaddr', text="Default Out Address") 
        layout.operator("addosc.importks", text='Import Keying Set')
        for item in bpy.context.scene.OSC_keys:
            row = layout.row()
            box = row.box()
            box.prop(item, 'name')
            box.prop(item, 'address')
            box.prop(item, 'ID')
            box.prop(item, 'osc_type')
            if bpy.context.window_manager.monitor == True:
                box.prop(item, 'value')
            
class MY_OT_StartUDP(bpy.types.Operator):
    bl_idname = "addosc.startudp"
    bl_label = "Start UDP Connection"
 
    def execute(self, context):
        global RATE
        global thread_run
        RATE = bpy.data.scenes[0].osc_rate
        if thread_run == 0 :
            try:
                bpy.ops.addosc.modal_timer_operator()
            except:
                self.report({'INFO'}, "Error !")
                return{'FINISHED'} 
            thread_run = 1	  
            self.report({'INFO'}, "Connecting...")
            bpy.context.scene.status = "Started"
            
        else:
            self.report({'INFO'}, "Already connected !")	  
        return{'FINISHED'}


class MY_OT_StopUDP(bpy.types.Operator):
    bl_idname = "addosc.stopudp"
    bl_label = "Stop UDP Connection"
 
    def execute(self, context):
        global thread_run
        thread_run = 0
        self.report({'INFO'}, "Disconnected !")
        bpy.context.scene.status = "Stopped"
        return{'FINISHED'}

          
class MY_OT_ImportKS(bpy.types.Operator):
    bl_idname = "addosc.importks"  
    bl_label = "Import a Keying Set"
    
    class SceneSettingItem(bpy.types.PropertyGroup):
        name = bpy.props.StringProperty(name="Key", default="Unknown")
        address = bpy.props.StringProperty(name="OSC address", default="Unknown")
        ID = bpy.props.IntProperty(name="ID", default=0, min=0)
        osc_type = bpy.props.StringProperty(name="Type", default="Unknown")
        value = bpy.props.StringProperty(name="Value", default="Unknown")
    bpy.utils.register_class(SceneSettingItem)    
                     
    bpy.types.Scene.OSC_keys = bpy.props.CollectionProperty(type=SceneSettingItem)
    
    bpy.types.Scene.defaultaddr = bpy.props.StringProperty(default="/blender")

    def execute(self, context):
        ks = bpy.context.scene.keying_sets.active
        my_item = bpy.context.scene.OSC_keys.clear()
        tvar2 = ""
        id_n = 0
        if str(ks) != "None":
            for items in ks.paths:               
                if str(items.id) != "None":     #workaround to avoid bad ID Block (Nodes)

                    #This is for customs properties that have brackets
                    if items.data_path[0:2] == '["' and items.data_path[-2:] == '"]':
                        tvar = repr(items.id)[9:] + items.data_path                         
                    else:
                        tvar = repr(items.id)[9:] + "." + items.data_path            

                    tvar_ev = "bpy.data." + tvar
                    
                    '''
                    tvar = repr(items.id)[9:] + "." + items.data_path
                    tvar_ev = "bpy.data." + tvar
                    
                    if str(eval(tvar_ev)).find("Vector") != -1 or str(eval(tvar_ev)).find("Euler")  != -1 :  #Pour traiter le cas des Vectors
                        tvar2 += tvar+".x "
                        tvar2 += tvar+".y "
                        tvar2 += tvar+".z "
                    elif str(eval(tvar_ev)).find("Quaternion") != -1 :
                        tvar2 += tvar+".w "
                        tvar2 += tvar+".x "
                        tvar2 += tvar+".y "
                        tvar2 += tvar+".z "   
                    elif str(eval(tvar_ev)).find("Color") != -1 :    
                        tvar2 += tvar+".r "
                        tvar2 += tvar+".g "
                        tvar2 += tvar+".b "
                    else:
                        tvar2 = tvar
                    '''
                    
                    #Let's break tupple properties into several ones
                    if repr(type(eval(tvar_ev)))!="<class 'str'>":
                        try:
                            l=len(eval(tvar_ev)) 
                            if items.use_entire_array==True: 
                                j = 0
                                k = l                                
                            else:
                                j = items.array_index
                                k = j+1
                            for i in range(j,k):
                                tvar2 += tvar + "[" + str(i) + "]"+"\n"                                 
                        except:
                            tvar2 = tvar+"\n"
                    else:
                        tvar2 = tvar+"\n"
                  
                    for i in tvar2.split("\n")[:-1]:
                        my_item = bpy.context.scene.OSC_keys.add()
                        my_item.name = i
                        tvar2 = ""
                        my_item.ID = id_n
                        id_n += 1
                        my_item.address = bpy.context.scene.defaultaddr 
                        my_item.osc_type = repr(type(eval("bpy.data."+i)))[8:-2]
                        print("Imported keys:\n"+i)
                else:
                    self.report({'INFO'}, "Missing ID block !")
                                                         
        else:
            self.report({'INFO'}, "None found !")	  
        
        return{'FINISHED'}        


def register():
    bpy.utils.register_module(__name__)
        
def unregister():
    bpy.utils.unregister_module(__name__)
 
if __name__ == "__main__": 
    register()
 
 


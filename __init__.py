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

# TODO:
#
# attach the timer to the context window or not ?
# pbm not set to None du modal timer when opening a new blend file
# Bool are not part of OSC 1.0 (only later as extension)
# Deal with tupple (x,y,z) or (r,g,b) usr "type(key).__name__" for Vector, Euler, etc... 
# Monitoring in console report error "Improper..." due to Monitoring refresh hack overhead 


bl_info = {
    "name": "AddOSC",
    "author": "JPfeP",
    "version": (0, 17),
    "blender": (2, 6, 6),
    "location": "",
    "description": "Realtime control of Blender using OSC protocol",
    "warning": "Please read the disclaimer about network security on my site.",
    "wiki_url": "http://www.jpfep.net/pages/addosc/",
    "tracker_url": "",
    "category": "System"}

import bpy
import sys
import json
from select import select
from bpy.utils import register_module, unregister_module
import socket
import errno
from math import radians
from bpy.props import *

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


def OSC_callback(*args):
    fail = True   
    bpy.context.window_manager.addosc_lastaddr = args[0]
    content=""
    for i in args[1:]:
        content += str(i)+" "
    bpy.context.window_manager.addosc_lastpayload = content
    
    # for simple properties
    for item in bpy.context.scene.OSC_keys:
        ob = eval(item.data_path)
        idx = 1 + item.idx
        
        if item.address == args[0]:
            #For ID custom properties (with brackets)
            if item.id[0:2] == '["' and item.id[-2:] == '"]':
                try:
                    ob[item.id[2:-2]] = args[idx]
                    fail = False
            
                except:
                    if bpy.context.window_manager.addosc_monitor == True:
                        print ("Improper content received: "+content+"for OSC route: "+args[0]+" and key: "+item.id)
                        
            #For normal properties
            #with index in brackets -: i_num
            elif item.id[-1] == ']':
                d_p = item.id[:-3]
                i_num = int(item.id[-2])
                try:
                    getattr(ob,d_p)[i_num] = args[idx]
                    fail = False
                except:
                    if bpy.context.window_manager.addosc_monitor == True: 
                        print ("Improper content received: "+content+"for OSC route: "+args[0]+" and key: "+item.id) 
            #without index in brackets
            else:
                try:
                    setattr(ob,item.id,args[idx])
                    fail = False
                except:
                    if bpy.context.window_manager.addosc_monitor == True: 
                        print ("Improper content received: "+content+"for OSC route: "+args[0]+" and key: "+item.id)
                 
                        
    if bpy.context.window_manager.addosc_monitor == True and fail == True: 
        print("Rejected OSC message, route: "+args[0]+" , content: "+content)

#For saving/restoring settings in the blendfile        
def upd_settings_sub(n):
    text_settings = None
    for text in bpy.data.texts:
        if text.name == '.addosc_settings':
            text_settings = text
    if text_settings == None:
        bpy.ops.text.new()
        text_settings = bpy.data.texts[-1]
        text_settings.name = '.addosc_settings'   
        text_settings.write("\n\n\n\n\n\n")
    if n==0:
        text_settings.lines[0].body = str(int(bpy.context.window_manager.addosc_monitor))
    elif n==1:
        text_settings.lines[1].body = str(bpy.context.window_manager.addosc_port_in)
    elif n==2:
        text_settings.lines[2].body = str(bpy.context.window_manager.addosc_port_out)
    elif n==3:
        text_settings.lines[3].body = str(bpy.context.window_manager.addosc_rate)
    elif n==4:
        text_settings.lines[4].body = bpy.context.window_manager.addosc_udp_in
    elif n==5:
        text_settings.lines[5].body = bpy.context.window_manager.addosc_udp_out
    elif n==6:
        text_settings.lines[6].body = str(int(bpy.context.window_manager.addosc_autorun))

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

def osc_export_config(scene):
    config_table = {};
    for osc_item in scene.OSC_keys:
        config_table[osc_item.address] = {
            "data_path" : osc_item.data_path,
            "id" : osc_item.id,
            "osc_type" : osc_item.osc_type
        };
    
    return json.dumps(config_table);

class OSC_Export(bpy.types.Operator):
    """Export the current OSC configuration to a file in JSON format"""
    bl_idname = "addosc.export"
    bl_label = "Export Config"

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        file = open(self.filepath, 'w')
        file.write(osc_export_config(context.scene))
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def osc_import_config(scene, config_file):
    config_table = json.load(config_file);
    for address, values in config_table.items():
        print(address)
        print(values)
        item = scene.OSC_keys.add()
        item.address = address;
        item.data_path = values["data_path"];
        item.id = values["id"];
        item.osc_type = values["osc_type"];

class OSC_Import(bpy.types.Operator):
    """Import OSC configuration from a file in JSON format"""
    bl_idname = "addosc.import"
    bl_label = "Import Config"

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        context.scene.OSC_keys.clear() 
        config_file = open(self.filepath, 'r')
        osc_import_config(context.scene, config_file)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class OSC_Reading_Sending(bpy.types.Operator):
    bl_idname = "addosc.modal_timer_operator"
    bl_label = "OSCMainThread"
    
    _timer = None 
    client = "" #for the sending socket
    count = 0
    
    def upd_trick_addosc_monitor(self,context):
        upd_setting_0()
    
    def upd_trick_portin(self,context):
        upd_setting_1()
    
    def upd_trick_portout(self,context):
        upd_setting_2()
           
    def upd_trick_rate(self,context):
        upd_setting_3()
               
    def upd_trick_addosc_udp_in(self,context):
        upd_setting_4()
        
    def upd_trick_addosc_udp_out(self,context):
        upd_setting_5()

    def upd_trick_addosc_autorun(self,context):
        upd_setting_6()        
    
    bpy.types.WindowManager.addosc_udp_in  = bpy.props.StringProperty(default="127.0.0.1", update=upd_trick_addosc_udp_in, description='The IP of the interface of your Blender machine to listen on, set to 0.0.0.0 for all of them')
    bpy.types.WindowManager.addosc_udp_out = bpy.props.StringProperty(default="127.0.0.1", update=upd_trick_addosc_udp_out, description='The IP of the destination machine to send messages to')
    bpy.types.WindowManager.addosc_port_in = bpy.props.IntProperty(default=9001, min=0, max=65535, update=upd_trick_portin, description='The input network port (0-65535)')
    bpy.types.WindowManager.addosc_port_out = bpy.props.IntProperty(default=9002, min=0, max= 65535, update=upd_trick_portout, description='The output network port (0-65535)')
    bpy.types.WindowManager.addosc_rate = bpy.props.IntProperty(default=10 ,description="The refresh rate of the engine (millisecond)", min=1, update=upd_trick_rate)
    bpy.types.WindowManager.status = bpy.props.StringProperty(default="Stopped", description='Show if the engine is running or not')
    bpy.types.WindowManager.addosc_monitor = bpy.props.BoolProperty(description="Display the current value of your keys, the last message received and some infos in console", update=upd_trick_addosc_monitor)
    bpy.types.WindowManager.addosc_autorun = bpy.props.BoolProperty(description="Start the OSC engine automatically after loading a project", update=upd_trick_addosc_autorun)
    bpy.types.WindowManager.addosc_lastaddr = bpy.props.StringProperty(description="Display the last OSC address received")
    bpy.types.WindowManager.addosc_lastpayload = bpy.props.StringProperty(description="Display the last OSC message content")
    
    #modes_enum = [('Replace','Replace','Replace'),('Update','Update','Update')]
    #bpy.types.WindowManager.addosc_mode = bpy.props.EnumProperty(name = "import mode", items = modes_enum)
    
    def modal(self, context, event):
         
        if context.window_manager.status == "Stopped" :
            return self.cancel(context)	  
       
        if event.type == 'TIMER':
            #hack to refresh the GUI
            bcw = bpy.context.window_manager
            self.count = self.count + bcw.addosc_rate
            if self.count >= 500:
                self.count = 0
                if bpy.context.window_manager.addosc_monitor == True:
                    for window in bpy.context.window_manager.windows:
                        screen = window.screen
                        for area in screen.areas:
                            if area.type == 'VIEW_3D':
                                area.tag_redraw()
            
            #Reception is no more done in the timer modal operator, see the handler 

            #Sending
            for item in bpy.context.scene.OSC_keys:
                if item.id[0:2] == '["' and item.id[-2:] == '"]':
                    prop = eval(item.data_path+item.id)
                else:
                    prop = eval(item.data_path+'.'+item.id)
                
                if str(prop) != item.value: 
                    item.value = str(prop)
                    
                    if item.idx == 0:
                        msg = osc_message_builder.OscMessageBuilder(address=item.address)
                        msg.add_arg(prop)
                        msg = msg.build()
                        self.client.send(msg)
   
        return {'PASS_THROUGH'}      
      
    def execute(self, context):
        global _report 
        bcw = bpy.context.window_manager
        
        #For sending
        try:
            self.client = udp_client.UDPClient(bcw.addosc_udp_out, bcw.addosc_port_out)
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
            self.dispatcher.set_default_handler(OSC_callback)
            self.server = osc_server.ThreadingOSCUDPServer((bcw.addosc_udp_in, bcw.addosc_port_in), self.dispatcher)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.start()
        except OSError as err:
            _report[0] = err
            return {'CANCELLED'}

          
        #inititate the modal timer thread
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(bcw.addosc_rate/1000, context.window)
        context.window_manager.status = "Running"
        
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        self.server.shutdown()
        context.window_manager.status = "Stopped"
        return {'CANCELLED'}


class OSC_UI_Panel(bpy.types.Panel):
    bl_label = "AddOSC Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "AddOSC"
 
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="OSC Settings:")
        row = col.row(align=True)
        row.operator("addosc.startudp", text='Start', icon='PLAY')
        row.operator("addosc.stopudp", text='Stop', icon='PAUSE')
        layout.prop(bpy.context.window_manager, 'status', text="Running Status")
        layout.prop(bpy.context.window_manager, 'addosc_udp_in', text="Listen on ")
        layout.prop(bpy.context.window_manager, 'addosc_udp_out', text="Destination address")
        col2 = layout.column(align=True)
        row2 = col2.row(align=True)
        row2.prop(bpy.context.window_manager, 'addosc_port_in', text="Input port")
        row2.prop(bpy.context.window_manager, 'addosc_port_out', text="Outport port")
        layout.prop(bpy.context.window_manager, 'addosc_rate', text="Update rate(ms)")    
        layout.prop(bpy.context.window_manager, 'addosc_autorun', text="Start at Launch")

class OSC_UI_Panel2(bpy.types.Panel):
    bl_label = "AddOSC Operations"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "AddOSC"
        
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=False)
        row.prop(bpy.context.scene, 'addosc_defaultaddr', text="Default Address")
        row.prop(bpy.context.window_manager, 'addosc_monitor', text="Monitoring")
       
        if context.window_manager.addosc_monitor == True:
            box = layout.box()
            row5 = box.column(align=True)
            row5.prop(bpy.context.window_manager, 'addosc_lastaddr', text="Last OSC address")
            row5.prop(bpy.context.window_manager, 'addosc_lastpayload', text="Last OSC message")   
                
        layout.separator()
        layout.operator("addosc.importks", text='Import Keying Set')
        row = layout.row(align=True)
        row.operator("addosc.export", text='Export OSC Config')
        row.operator("addosc.import", text='Import OSC Config')
        
        layout.separator()
        layout.label(text="Imported Keys:")
        for item in bpy.context.scene.OSC_keys:
            box3 = layout.box()
            split = box3.split()
            col = split.column()
            col.prop(item,'data_path',text='Path')
            col.prop(item, 'address')
            col2 = split.column()
            row4 = col2.row(align=True)
            row4.prop(item,'id',text='')
            row4.label(text="("+item.osc_type+")")            

            row5 = col2.row(align=True)
            row5.operator("addosc.pick", text='Pick').i_addr = item.address
            row5.prop(item, 'idx', text='Index')
            
            if bpy.context.window_manager.addosc_monitor == True:
                col.prop(item, 'value')
                
      
            
class StartUDP(bpy.types.Operator):
    bl_idname = "addosc.startudp"
    bl_label = "Start UDP Connection"
    bl_description ="Start the OSC engine"
 
    def execute(self, context):
        global _report
        if context.window_manager.addosc_port_in == context.window_manager.addosc_port_out:
            self.report({'INFO'}, "Ports must be different.")
            return{'FINISHED'} 
        if bpy.context.window_manager.status != "Running" :
            bpy.ops.addosc.modal_timer_operator()
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
    bl_idname = "addosc.stopudp"
    bl_label = "Stop UDP Connection"
    bl_description ="Stop the OSC engine"
 
    def execute(self, context):
        self.report({'INFO'}, "Disconnected !")
        bpy.context.window_manager.status = "Stopped"
        return{'FINISHED'}


class PickOSCaddress(bpy.types.Operator):
    bl_idname = "addosc.pick"
    bl_label = "Pick the last event OSC address"
    bl_options = {'UNDO'}
    bl_description ="Pick the address of the last OSC message received"
   
    i_addr = bpy.props.StringProperty()  
 
    def execute(self, context):
        last_event = bpy.context.window_manager.addosc_lastaddr
        if len(last_event) > 1 and last_event[0] == "/": 
            for item in bpy.context.scene.OSC_keys:
                if item.address == self.i_addr :
                    item.address = last_event
        return{'FINISHED'}
    

def parse_ks(item):
    dp = item.data_path
    ID = repr(item.id)
    
    #custom prop:
    if dp[-1] == ']':
        #it's a simple datapath like ['plop']
        if dp[0] == '[' :
            full_p = ID + dp
            path = ID 
            prop = dp
        #it's a composed datapath like foo.bones["bar"]['plop']
        else:
            full_p = ID + '.' + dp
            path = str(full_p.split('][')[0]) + ']'  
            prop = '[' + str(full_p.split('][')[1]) 
    #normal prop:
    else:
        full_p = ID + '.' + dp
        path = '.'.join(full_p.split('.')[:-1])
        prop = full_p.split('.')[-1]
    
    return full_p, path, prop
    
    
class AddOSC_ImportKS(bpy.types.Operator):
    bl_idname = "addosc.importks"  
    bl_label = "Import a Keying Set"
    bl_options = {'UNDO'}
    bl_description ="Import the keys of the active Keying Set"
    
    def verifdefaddr(self,context):
        if context.scene.addosc_defaultaddr[0] != "/":
            context.scene.addosc_defaultaddr = "/"+context.scene.addosc_defaultaddr
        
    class SceneSettingItem(bpy.types.PropertyGroup):
        #key_path = bpy.props.StringProperty(name="Key", default="Unknown")
        address = bpy.props.StringProperty(name="Address", default="")
        data_path = bpy.props.StringProperty(name="Data path", default="")
        id = bpy.props.StringProperty(name="ID", default="")
        osc_type = bpy.props.StringProperty(name="Type", default="Unknown")
        value = bpy.props.StringProperty(name="Value", default="Unknown")
        idx = bpy.props.IntProperty(name="Index", min=0, default=0)
    bpy.utils.register_class(SceneSettingItem)    
                        
    bpy.types.Scene.OSC_keys = bpy.props.CollectionProperty(type=SceneSettingItem)
    bpy.types.Scene.OSC_keys_tmp = bpy.props.CollectionProperty(type=SceneSettingItem)
    
    bpy.types.Scene.addosc_defaultaddr = bpy.props.StringProperty(default="/blender", description='Form new addresses based on this keyword',update=verifdefaddr)

    def execute(self, context):
        ks = bpy.context.scene.keying_sets.active
        t_arr = [] #temporary array for data_path,id
        id_n = -1
        
        if str(ks) != "None":
            for items in ks.paths:               
                if str(items.id) != "None":     #workaround to avoid bad ID Block (Nodes)
                    
                    tvar_ev,path,prop = parse_ks(items)
               
                    
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
                                t_arr.append([prop + "[" + str(i) + "]",path])
                        except:
                            t_arr.append([prop,path])
                    else:
                        t_arr.append([prop,path])
                    
                    
                  
                else:
                    self.report({'INFO'}, "Missing ID block !")
                
                
            #what is the highest ID number ?
            for item in bpy.context.scene.OSC_keys:
                split = item.address.split('/')
                try:
                    if split[1] == bpy.context.scene.addosc_defaultaddr[1:]:
                        if int(split[-1]) > id_n:
                            id_n = int(split[-1])
                except:
                    pass
                

            #Transfer of tvar2 into the OSC_keys_tmp property
            bpy.context.scene.OSC_keys_tmp.clear()            
            for i,j in t_arr:
                my_item = bpy.context.scene.OSC_keys_tmp.add()
                my_item.id = i
                my_item.data_path = j
                #for custom prop
                if i[0:2] == '["' and i[-2:] == '"]':
                    t_eval = my_item.data_path + my_item.id
                #for the others
                else:
                    t_eval = my_item.data_path + "." + my_item.id   
                
                my_item.osc_type = repr(type(eval(t_eval)))[8:-2]
    
            #Copy addresses from OSC_keys if there are some
            for item_tmp in bpy.context.scene.OSC_keys_tmp:
                for item in bpy.context.scene.OSC_keys:
                    if item_tmp.id == item.id and item_tmp.data_path == item.data_path:
                        item_tmp.address = item.address
                        item_tmp.idx = item.idx
                if item_tmp.address == "":
                    id_n += 1
                    item_tmp.address = bpy.context.scene.addosc_defaultaddr + "/" + str(id_n)
                                          
            #Simple copy OSC_keys_tmp toward OSC_keys
            item = bpy.context.scene.OSC_keys.clear()            
            for tmp_item in bpy.context.scene.OSC_keys_tmp:
                item = bpy.context.scene.OSC_keys.add()
                item.id = tmp_item.id
                item.data_path = tmp_item.data_path
                item.address = tmp_item.address
                item.osc_type = tmp_item.osc_type
                item.idx = tmp_item.idx
                                                     
        else:
            self.report({'INFO'}, "None found !")	  
        
        return{'FINISHED'}        

#Restore saved settings
@persistent
def addosc_handler(scene):
    for text in bpy.data.texts:
        if text.name == '.addosc_settings':
            try:
                bpy.context.window_manager.addosc_monitor = int(text.lines[0].body)
            except:
                pass
            try:
                bpy.context.window_manager.addosc_port_in  = int(text.lines[1].body)
            except:
                pass
            try:
                bpy.context.window_manager.addosc_port_out = int(text.lines[2].body)
            except:
                pass
            try:
                bpy.context.window_manager.addosc_rate = int(text.lines[3].body) 
            except:
                bpy.context.window_manager.addosc_rate = 10
            if text.lines[4].body != '':
                bpy.context.window_manager.addosc_udp_in = text.lines[4].body 
            if text.lines[5].body != '':
                bpy.context.window_manager.addosc_udp_out = text.lines[5].body 
            try:
                bpy.context.window_manager.addosc_autorun = int(text.lines[6].body) 
            except:
                pass

            #if error_device == True:
            #    bpy.context.window_manager.addosc_autorun = False

            if bpy.context.window_manager.addosc_autorun == True:
                bpy.ops.addosc.startudp()  

def register():
    bpy.utils.register_module(__name__)
    bpy.app.handlers.load_post.append(addosc_handler)
        
def unregister():
    bpy.utils.unregister_module(__name__)
 
if __name__ == "__main__": 
    register()

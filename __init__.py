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

from bpy.app.handlers import persistent

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
    
#Restore saved settings
@persistent
def nodeosc_handler(scene):
    if bpy.context.scene.nodeosc_envars.autorun == True:
        if bpy.context.scene.nodeosc_envars.status == "Stopped":
            bpy.ops.nodeosc.startudp()


from . import preferences
from .server import server, operators, keys
from .ui import panels
from .nodes.AN import auto_load
auto_load.init()

panel_classes = (
    StartUDP,
)

def register():
    preferences.register()
    keys.register()
    operators.register()
    panels.register()
    server.register()
    auto_load.register()
    for cls in panel_classes:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_post.append(nodeosc_handler)

def unregister():
    for cls in reversed(panel_classes):
        bpy.utils.unregister_class(cls)
    auto_load.unregister()
    server.unregister()
    panels.unregister()
    operators.unregister()
    keys.unregister()
    preferences.unregister()

if __name__ == "__main__":
    register()

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
# pbm not set to None du modal timer when opening a new blend file


bl_info = {
    "name": "NodeOSC",
    "author": "maybites",
    "version": (2, 3, 2),
    "blender": (2, 80, 0),
    "location": "View3D > Tools > NodeOSC",
    "description": "Realtime control of Blender using OSC data protocol",
    "wiki_url": "https://github.com/maybites/blender.NodeOSC/wiki",
    "tracker_url": "https://github.com/maybites/blender.NodeOSC/issues",
    "support": "COMMUNITY",
    "category": "System"}

import bpy

from bpy.app.handlers import persistent
    
#Restore saved settings
@persistent
def nodeosc_handler(scene):
    if bpy.context.scene.nodeosc_envars.autorun == True:
        if bpy.context.scene.nodeosc_envars.isServerRunning == False:
            preferences = bpy.context.preferences
            addon_prefs = preferences.addons[__package__].preferences
            if addon_prefs.usePyLiblo == False:
                bpy.ops.nodeosc.oscpy_operator()
            else:
                bpy.ops.nodeosc.pythonosc_operator()


from . import preferences
from .server import server, operators
from .ui import panels
from .nodes import nodes
from .utils import keys

def register():
    preferences.register()
    keys.register()
    operators.register()
    panels.register()
    server.register()
    nodes.register()
    bpy.app.handlers.load_post.append(nodeosc_handler)

def unregister():
    nodes.unregister()
    server.unregister()
    panels.unregister()
    operators.unregister()
    keys.unregister()
    preferences.unregister()

if __name__ == "__main__":
    register()

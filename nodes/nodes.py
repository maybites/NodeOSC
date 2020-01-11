import bpy
import os
import addon_utils
import importlib
import nodeitems_utils

from nodeitems_utils import NodeItem
from pathlib import Path
from animation_nodes.events import propertyChanged
from Sorcar.helper import print_log
from Sorcar.tree.ScNodeCategory import ScNodeCategory

# fill up the OSC_handles with all the current OSC_keys and OSC_nodes
def nodes_createHandleCollection():
    bpy.context.scene.OSC_nodes.clear()
    for node_group in bpy.data.node_groups:
        if node_group.bl_idname == 'an_AnimationNodeTree':
            for node in node_group.nodes:
                if node.bl_idname.find("an_OSC") != -1:
                    node.refresh()
                    item = bpy.context.scene.OSC_nodes.add()
                    item.data_path = node.data_path
                    item.id = node.id
                    item.osc_address = node.osc_address
                    item.osc_type = node.osc_type
                    item.osc_index = node.osc_index
                    item.osc_direction = node.osc_direction
                    item.node_data_type = node.node_data_type
        if node_group.bl_idname == 'ScNodeTree':
            for node in node_group.nodes:
                if node.bl_idname.find("ScOSC") != -1:
                    node.post_execute()
                    item = bpy.context.scene.OSC_nodes.add()
                    item.data_path = node.data_path
                    item.id = node.id
                    item.osc_address = node.osc_address
                    item.osc_type = node.osc_type
                    item.osc_index = node.osc_index
                    item.osc_direction = node.osc_direction
                    item.node_data_type = node.node_data_type

# checks if there is any active and supported node system
def hasNodes():
    if hasAnimationNodes() == True:
        return True
    return False

# checks if there is any active animation node system
def hasAnimationNodes():
    for node_group in bpy.data.node_groups:
        if node_group.bl_idname == 'an_AnimationNodeTree':
            return True
    return False

# executes all the active and supported node system
def executeNodeTrees():
    executeAnimationNodeTrees()
    #executeSorcarNodeTrees()

# executes only animation node systems
def executeAnimationNodeTrees():
    propertyChanged()
    # for node_group in bpy.data.node_groups:
    #    bpy.ops.an.execute_tree(name = node_group.name)

# executes only animation node systems
def executeSorcarNodeTrees():
    for node_group in bpy.data.node_groups:
        if node_group.bl_idname == 'ScNodeTree':
            node_group.execute_node()

def import_sorcar_nodes(path):
    out = {}
    for cat in [i for i in os.listdir(str(path) + "/nodes/sorcar/nodes") if not i.startswith("_") or not i.startswith(".")]:
        out[cat] = []
        for i in bpy.path.module_names(str(path) + "/nodes/sorcar/nodes/" + cat):
            out[cat].append(getattr(importlib.import_module(".nodes.sorcar.nodes." + cat + "." + i[0], path.name), i[0]))
            print_log("IMPORT NODE", bpy.path.display_name(cat), msg=i[0])
    return out
    
from .AN import auto_load
auto_load.init()

from Sorcar import all_classes
classes_nodes = []

def register():
    # importing and registering animation nodes...
    auto_load.register()
    
    # importing and registering sorcar nodes...
    packagePath = Path(__file__).parent.parent
    
    global classes_nodes
    
    classes_nodes = import_sorcar_nodes(packagePath)

#    global all_classes
    
    total_nodes = 0
    node_categories = []
    for cat in classes_nodes:
        total_nodes += len(classes_nodes[cat])
        node_categories.append(ScNodeCategory(identifier="sc_"+cat, name=bpy.path.display_name(cat), items=[NodeItem(i.bl_idname) for i in classes_nodes[cat]]))
#        all_classes.extend(classes_nodes[cat])
        for c in classes_nodes[cat]:
            bpy.utils.register_class(c)
    
    nodeitems_utils.register_node_categories("osc_node_categories", node_categories)

def unregister():
    auto_load.unregister()
    
    global classes_nodes

    for cat in classes_nodes:
        for c in classes_nodes[cat]:
            bpy.utils.unregister_class(c)
    nodeitems_utils.unregister_node_categories("osc_node_categories")

import bpy
import os
import addon_utils
import importlib
import nodeitems_utils
import platform

from nodeitems_utils import NodeItem
from pathlib import Path

# try loading the node modules
load_an_success = False
load_sc_success = False

try:
    from animation_nodes.events import propertyChanged
    load_an_success = True
except ModuleNotFoundError:
    load_an_success = False


try:
    if platform.system() == "Windows":
        from sorcar.helper import print_log
        from sorcar.tree.ScNodeCategory import ScNodeCategory
        load_sc_success = True
    else:
        from Sorcar.helper import print_log
        from Sorcar.tree.ScNodeCategory import ScNodeCategory
        load_sc_success = True
        
except ModuleNotFoundError:
    load_sc_success = False
    
# fill up the collections for further processing:
#   OSC_nodes with all the OSC nodes we can find
#   OSC_outputs with all the handles that need to be sent to the output
def nodes_createCollections():
    bpy.context.scene.NodeOSC_nodes.clear()
    for node_group in bpy.data.node_groups:
        if node_group.bl_idname == 'an_AnimationNodeTree':
            for node in node_group.nodes:
                if node.bl_idname.find("an_OSC") != -1:
                    node.refresh()
                    item = bpy.context.scene.NodeOSC_nodes.add()
                    item.data_path = node.data_path
                    item.props = node.props
                    item.osc_address = node.osc_address
                    item.osc_type = node.osc_type
                    item.osc_index = node.osc_index
                    item.osc_direction = node.osc_direction
                    item.node_data_type = node.node_data_type
                    item.node_type = node.node_type
        if node_group.bl_idname == 'ScNodeTree':
            for node in node_group.nodes:
                if node.bl_idname.find("ScOSC") != -1:
                    node.post_execute()
                    item = bpy.context.scene.NodeOSC_nodes.add()
                    item.data_path = node.data_path
                    item.props = node.props
                    item.osc_address = node.osc_address
                    item.osc_type = node.osc_type
                    item.osc_index = node.osc_index
                    item.osc_direction = node.osc_direction
                    item.node_data_type = node.node_data_type
                    item.node_type = node.node_type
    
    bpy.context.scene.NodeOSC_outputs.clear()
    for itemN in bpy.context.scene.NodeOSC_nodes:
        if itemN.enabled and itemN.osc_direction != "INPUT":
            item = bpy.context.scene.NodeOSC_outputs.add()
            item.data_path = itemN.data_path
            item.props = itemN.props
            item.osc_address = itemN.osc_address
            item.osc_type = itemN.osc_type
            item.osc_index = itemN.osc_index
            item.osc_direction = itemN.osc_direction
            item.node_data_type = itemN.node_data_type
            item.node_type = itemN.node_type
    for itemN in bpy.context.scene.NodeOSC_keys:
        if itemN.enabled and itemN.osc_direction != "INPUT":
            item = bpy.context.scene.NodeOSC_outputs.add()
            item.data_path = itemN.data_path
            item.props = itemN.props
            item.osc_address = itemN.osc_address
            item.osc_type = itemN.osc_type
            item.osc_index = itemN.osc_index
            item.osc_direction = itemN.osc_direction
            item.node_data_type = itemN.node_data_type
            item.node_type = itemN.node_type
       


# checks if there is any active and supported node system
def hasNodes():
    if hasAnimationNodes() or hasSorcarNodes():
        return True
    return False

# checks if there is any active animation node system
def hasAnimationNodes():
    if bpy.context.scene.nodeosc_AN_isLoaded:
        for node_group in bpy.data.node_groups:
            if node_group.bl_idname == 'an_AnimationNodeTree':
                return True
    return False

# checks if there is any active sorcar node system
def hasSorcarNodes():
    if bpy.context.scene.nodeosc_AN_isLoaded:
        for node_group in bpy.data.node_groups:
            if node_group.bl_idname == 'ScNodeTree':
                return True
    return False

# executes only animation node systems
def executeAnimationNodeTrees():
    if load_an_success:
        if bpy.context.scene.nodeosc_AN_needsUpdate:
            propertyChanged()
            bpy.context.scene.nodeosc_AN_needsUpdate = False

# executes only sorcar node systems
# this method needs to be called from a server Modal
def executeSorcarNodeTrees(context):
    if load_sc_success:
        if bpy.context.scene.nodeosc_SORCAR_needsUpdate:
            for node_group in bpy.data.node_groups:
                if node_group.bl_idname == 'ScNodeTree':
                    node_group.execute_node()
            bpy.context.scene.nodeosc_SORCAR_needsUpdate = False

def import_sorcar_nodes(path):
    out = {}
    for cat in [i for i in os.listdir(str(path) + "/nodes/sorcar/nodes") if not i.startswith("_") and not i.startswith(".")]:
        out[cat] = []
        for i in bpy.path.module_names(str(path) + "/nodes/sorcar/nodes/" + cat):
            out[cat].append(getattr(importlib.import_module(".nodes.sorcar.nodes." + cat + "." + i[0], path.name), i[0]))
            print_log("IMPORT NODE", bpy.path.display_name(cat), msg=i[0])
    return out

if load_an_success:
    from .AN import auto_load
    auto_load.init()

if load_sc_success:
    if platform.system() == "Windows":
        from sorcar import all_classes
    else:
        from Sorcar import all_classes
    classes_nodes = []

def register():
    global load_an_success
    global load_sc_success

    bpy.types.Scene.nodeosc_AN_needsUpdate = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.nodeosc_SORCAR_needsUpdate = bpy.props.BoolProperty(default=False)

    if load_an_success:
        # importing and registering animation nodes...
        auto_load.register()
        bpy.types.Scene.nodeosc_AN_isLoaded = bpy.props.BoolProperty(default=True, description='AN addon detected')
    else:
        bpy.types.Scene.nodeosc_AN_isLoaded = bpy.props.BoolProperty(default=False, description='AN addon detected')
    
    if load_sc_success:
        # importing and registering sorcar nodes...
        packagePath = Path(__file__).parent.parent
        
        global classes_nodes
        
        classes_nodes = import_sorcar_nodes(packagePath)
       
        total_nodes = 0
        node_categories = []
        for cat in classes_nodes:
            total_nodes += len(classes_nodes[cat])
            node_categories.append(ScNodeCategory(identifier="sc_"+cat, name=bpy.path.display_name(cat), items=[NodeItem(i.bl_idname) for i in classes_nodes[cat]]))
            for c in classes_nodes[cat]:
                bpy.utils.register_class(c)
        
        nodeitems_utils.register_node_categories("osc_node_categories", node_categories)
        bpy.types.Scene.nodeosc_SORCAR_isLoaded = bpy.props.BoolProperty(default=True, description='SORCAR addon detected')
    else:
        bpy.types.Scene.nodeosc_SORCAR_isLoaded = bpy.props.BoolProperty(default=False, description='SORCAR addon detected')


def unregister():
    del bpy.types.Scene.nodeosc_AN_isLoaded
    del bpy.types.Scene.nodeosc_AN_needsUpdate

    del bpy.types.Scene.nodeosc_SORCAR_isLoaded
    del bpy.types.Scene.nodeosc_SORCAR_needsUpdate
    
    if load_an_success:
        auto_load.unregister()
    
    if load_sc_success:
        global classes_nodes

        for cat in classes_nodes:
            for c in classes_nodes[cat]:
                bpy.utils.unregister_class(c)
        nodeitems_utils.unregister_node_categories("osc_node_categories")

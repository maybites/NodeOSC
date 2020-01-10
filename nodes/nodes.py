import bpy
from animation_nodes.events import propertyChanged

# fill up the OSC_handles with all the current OSC_keys and OSC_nodes
def createNodeHandleCollection():
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

# executes only animation node systems
def executeAnimationNodeTrees():
    propertyChanged()
    # for node_group in bpy.data.node_groups:
    #    bpy.ops.an.execute_tree(name = node_group.name)
    


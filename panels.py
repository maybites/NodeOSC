import bpy

#######################################
#  MAIN GUI PANEL                     #
#######################################

class OSC_PT_Settings(bpy.types.Panel):
    bl_category = "NodeOSC"
    bl_label = "NodeOSC Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="OSC Settings:")
        row = col.row(align=True)
        row.operator("nodeosc.startudp", text='Start', icon='PLAY')
        row.operator("nodeosc.stopudp", text='Stop', icon='PAUSE')
        layout.prop(bpy.context.window_manager, 'status', text="Running Status")
        layout.prop(bpy.context.window_manager, 'nodeosc_udp_in', text="Listen on ")
        layout.prop(bpy.context.window_manager, 'nodeosc_udp_out', text="Destination address")
        col2 = layout.column(align=True)
        row2 = col2.row(align=True)
        row2.prop(bpy.context.window_manager, 'nodeosc_port_in', text="Input port")
        row2.prop(bpy.context.window_manager, 'nodeosc_port_out', text="Outport port")
        layout.prop(bpy.context.window_manager, 'nodeosc_rate', text="Update rate(ms)")
        layout.prop(bpy.context.window_manager, 'nodeosc_autorun', text="Start at Launch")
 
#######################################
#  OPERATIONS GUI PANEL               #
#######################################

class OSC_PT_Operations(bpy.types.Panel):
    bl_category = "NodeOSC"
    bl_label = "NodeOSC Operations"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=False)
        row.prop(bpy.context.scene, 'nodeosc_defaultaddr', text="Default Address")
        row.prop(bpy.context.window_manager, 'nodeosc_monitor', text="Monitoring")

        if context.window_manager.nodeosc_monitor == True:
            box = layout.box()
            row5 = box.column(align=True)
            row5.prop(bpy.context.window_manager, 'nodeosc_lastaddr', text="Last OSC address")
            row5.prop(bpy.context.window_manager, 'nodeosc_lastpayload', text="Last OSC message")

        layout.separator()
        layout.operator("nodeosc.importks", text='Import Keying Set')
        row = layout.row(align=True)
        row.operator("nodeosc.export", text='Export OSC Config')
        row.operator("nodeosc.import", text='Import OSC Config')

        layout.separator()
        layout.label(text="Imported Keys:")
        index = 0
        for item in bpy.context.scene.OSC_keys:
            box3 = layout.box()
            #split = box3.split()
            rowItm1 = box3.row()
            if bpy.context.window_manager.nodeosc_monitor == True:
                rowItm1.operator("nodeosc.pick", text='', icon='EYEDROPPER').i_addr = item.address
            rowItm1.prop(item, 'address',text='Osc-addr')
            rowItm1.prop(item, 'osc_index',text='Osc-argument[index]')
            #rowItm1.label(text="("+item.osc_type+")")
             
            rowItm2 = box3.row()
            rowItm2.prop(item,'data_path',text='Blender-path')
            rowItm2.prop(item,'id',text='ID')
            rowItm2.operator("nodeosc.deleteitem", icon='CANCEL').index = index
            
            if bpy.context.window_manager.nodeosc_monitor == True:
                rowItm3 = box3.row()
                rowItm3.prop(item, 'value',text='current value')
            index = index + 1

panel_classes = (
    OSC_PT_Settings,
    OSC_PT_Operations,
)

def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(panel_classes):
        bpy.utils.unregister_class(cls)

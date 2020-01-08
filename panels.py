import bpy

#######################################
#  MAIN GUI PANEL                     #
#######################################

class OSC_PT_Settings(bpy.types.Panel):
    bl_category = "NodeOSC"
    bl_label = "NodeOSC Server"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="OSC Settings:")
        row = col.row(align=True)
        if bpy.context.scene.nodeosc_envars.status == "Stopped":
            row.operator("nodeosc.startudp", text='Start', icon='PLAY')
        else:
            row.operator("nodeosc.startudp", text='Stop', icon='PAUSE')
        #layout.prop(bpy.context.scene.nodeosc_envars, 'status', text="Running Status")
        col1 = layout.column(align=True)
        row1 = col1.row(align=True)
        row1.prop(bpy.context.scene.nodeosc_envars, 'udp_in', text="Input")
        row1.prop(bpy.context.scene.nodeosc_envars, 'port_in', text="Port")
        col2 = layout.column(align=True)
        row2 = col2.row(align=True)
        row2.prop(bpy.context.scene.nodeosc_envars, 'udp_out', text="Output")
        row2.prop(bpy.context.scene.nodeosc_envars, 'port_out', text="Port")
        layout.prop(bpy.context.scene.nodeosc_envars, 'output_rate', text="Update rate(ms)")
        layout.prop(bpy.context.scene.nodeosc_envars, 'autorun', text="Start at Launch")
 
#######################################
#  CUSTOM RX PANEL                    #
#######################################

class OSC_PT_Operations(bpy.types.Panel):
    bl_category = "NodeOSC"
    bl_label = "Custom RX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Message handlers:")
        index = 0
        for item in bpy.context.scene.OSC_keys:
            box3 = layout.box()
            colItm1 = box3.column(align=True)
            colItm1.prop(item, 'osc_direction',text='RX/TX')
            if bpy.context.scene.nodeosc_envars.message_monitor == True:
                rowItmA = colItm1.row(align=True)
                rowItmA.prop(item, 'osc_address',text='address')
                rowItmA.operator("nodeosc.pick", text='', icon='EYEDROPPER').i_addr = item.osc_address
            else: 
                colItm1.prop(item, 'osc_address',text='address')
            colItm1.prop(item, 'osc_index',text='arg [idx]')
            if item.osc_direction == "OUTPUT":
                colItm1.prop(item, 'osc_type',text='arg types')
            #rowItm1.label(text="("+item.osc_type+")")
             
            colItm2 = box3.column(align=True)
            colItm2.prop(item,'data_path',text='path')
            colItm2.prop(item,'id',text='id')
            
            if bpy.context.scene.nodeosc_envars.message_monitor == True:
                rowItm3 = box3.row()
                rowItm3.prop(item, 'value',text='current value')
            
            rowItm4 = box3.row()
            rowItm4.operator("nodeosc.deleteitem", icon='CANCEL').index = index
            
            index = index + 1
        
        layout.operator("nodeosc.createitem", icon='PRESET_NEW', text='Create new message handler')

        layout.separator()

        row = layout.row(align=False)
        row.prop(bpy.context.scene, 'nodeosc_defaultaddr', text="Default Address")
        row.prop(bpy.context.scene.nodeosc_envars, 'message_monitor', text="Monitoring")

        if bpy.context.scene.nodeosc_envars.message_monitor == True:
            box = layout.box()
            row5 = box.column(align=True)
            row5.prop(bpy.context.scene.nodeosc_envars, 'lastaddr', text="Last OSC address")
            row5.prop(bpy.context.scene.nodeosc_envars, 'lastpayload', text="Last OSC message")

        layout.separator()
        layout.operator("nodeosc.importks", text='Import Keying Set')
        row = layout.row(align=True)
        row.operator("nodeosc.export", text='Export OSC Config')
        row.operator("nodeosc.import", text='Import OSC Config')

#######################################
#  NODES RX PANEL                    #
#######################################

class OSC_PT_Nodes(bpy.types.Panel):
    bl_category = "NodeOSC"
    bl_label = "Node RX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Node message handlers:")
        index = 0
        for item in bpy.context.scene.OSC_nodes:
            box3 = layout.box()
            colItm1 = box3.column(align=True)
            colItm1.prop(item, 'osc_direction',text='RX/TX')
            colItm1.prop(item, 'osc_address',text='address')
            colItm1.prop(item, 'osc_index',text='arg[idx]')
             
            colItm2 = box3.column(align=True)
            colItm2.prop(item,'data_path',text='path')
            colItm2.prop(item,'id',text='id')
                                    
            index = index + 1


panel_classes = (
    OSC_PT_Settings,
    OSC_PT_Nodes,
    OSC_PT_Operations,
)

def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(panel_classes):
        bpy.utils.unregister_class(cls)

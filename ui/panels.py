import bpy
import platform
from pathlib import Path

#######################################
#  MAIN GUI PANEL                     #
#######################################

class OSC_PT_Settings(bpy.types.Panel):
    bl_category = "NodeOSC"
    bl_label = "NodeOSC Server"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[self.bl_category].preferences           
 
        envars = bpy.context.scene.nodeosc_envars
        layout = self.layout
        col = layout.column(align=True)
        if envars.status == "Stopped":
            row = col.row(align=True)
            if addon_prefs.usePyLiblo == False:
                row.operator("nodeosc.pythonosc_operator", text='Start', icon='PLAY')
            else:
                row.operator("nodeosc.pyliblo_operator", text='Start', icon='PLAY')
            if platform.system() != "Linux":
                row.prop(addon_prefs, "usePyLiblo", text = '', icon='CHECKBOX_HLT' if addon_prefs.usePyLiblo else 'CHECKBOX_DEHLT')

            
            col1 = layout.column(align=True)
            row1 = col1.row(align=True)
            row1.prop(envars, 'udp_in', text="In")
            row1.prop(envars, 'port_in', text="Port")
            col2 = layout.column(align=True)
            row2 = col2.row(align=True)
            row2.prop(envars, 'udp_out', text="Out")
            row2.prop(envars, 'port_out', text="Port")
            layout.prop(envars, 'output_rate', text="Update rate(ms)")
            layout.prop(envars, 'autorun', text="Start at Launch")
        else:
            if addon_prefs.usePyLiblo == False:
                col.operator("nodeosc.pythonosc_operator", text='Stop', icon='PAUSE')
                col.label(text="pure python server is running...")
            else:
                col.operator("nodeosc.pyliblo_operator", text='Stop', icon='PAUSE')
                col.label(text="pyLiblo server is running...")               
                 
            col.label(text=" listening at " + envars.udp_in + " on port " + str(envars.port_in))
            col.label(text=" sending to " + envars.udp_out + " on port " + str(envars.port_out))
        
            col.prop(bpy.context.scene.nodeosc_envars, 'message_monitor', text="Monitoring and Error reporting")

            if bpy.context.scene.nodeosc_envars.message_monitor == True: 
                box = col.box()
                row5 = box.column(align=True)
                if addon_prefs.usePyLiblo == False:
                    row5.label(text="Last OSC ..")
                    row5.prop(bpy.context.scene.nodeosc_envars, 'lastaddr', text="address")
                    row5.prop(bpy.context.scene.nodeosc_envars, 'lastpayload', text="values")
                else:
                    row5.label(text="pyLiblo server ignores all unknown osc messages")
                    

            
#######################################
#  CUSTOM RX PANEL                    #
#######################################

class OSC_PT_Operations(bpy.types.Panel):
    bl_category = "NodeOSC"
    bl_label = "Custom Messages"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        envars = bpy.context.scene.nodeosc_envars
        layout = self.layout
        if envars.status == "Stopped":
            layout.label(text="Message handlers:")
        else:
            layout.label(text="Message handlers: (restart server to apply changes)")
        index = 0
        col = layout.column()
        for item in bpy.context.scene.OSC_keys:
            col_box = col.column()
            box = col_box.box()
            colsub = box.column()
            row = colsub.row(align=True)

            row.prop(item, "ui_expanded", text = "", 
                        icon='DISCLOSURE_TRI_DOWN' if item.ui_expanded else 'DISCLOSURE_TRI_RIGHT', 
                        emboss = False)
            row.prop(item, "enabled", text = "", 
                        icon='CHECKBOX_HLT' if item.enabled else 'CHECKBOX_DEHLT', 
                        emboss = False)
            row.label(text = "", 
                        icon='EXPORT' if item.osc_direction == "OUTPUT" else 'IMPORT')
            
            sub = row.row()
            sub.active = item.enabled
            sub.label(text=item.osc_address)
            subsub = sub.row()
            subsub.operator("nodeosc.createitem", icon='PLUS', text='').copy = index
            subsub.operator("nodeosc.deleteitem", icon='CANCEL', text = "").index = index
            
            if item.ui_expanded:
                colItm1 = colsub.column(align=True)
                colItm1.prop(item, 'osc_direction',text='RX/TX')
                if bpy.context.scene.nodeosc_envars.message_monitor == True:
                    rowItmA = colItm1.row(align=True)
                    rowItmA.prop(item, 'osc_address',text='address')
                    rowItmA.operator("nodeosc.pick", text='', icon='EYEDROPPER').i_addr = item.osc_address
                else: 
                    colItm1.prop(item, 'osc_address',text='address')
                colItm1.prop(item, 'osc_index',text='arg [idx]')
                #if item.osc_direction == "OUTPUT":
                #    colItm1.prop(item, 'osc_type',text='arg types')
                #rowItm1.label(text="("+item.osc_type+")")
                
                colItm2 = colsub.column(align=True)
                colItm2.prop(item,'data_path',text='datapath')
                colItm2.prop(item,'id',text='property')
                
                if bpy.context.scene.nodeosc_envars.message_monitor == True:
                    rowItm3 = colsub.row()
                    rowItm3.prop(item, 'value',text='current value')
                                
            index = index + 1
        
        layout.operator("nodeosc.createitem", icon='PRESET_NEW', text='Create new message handler').copy = -1

        layout.separator()

        row = layout.row(align=False)
        row.prop(bpy.context.scene, 'nodeosc_defaultaddr', text="Default Address")

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
    bl_label = "Node Messages"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        envars = bpy.context.scene.nodeosc_envars
        layout = self.layout
        if envars.status == "Stopped":
            layout.label(text="Node tree execute mode:")
            layout.prop(envars, 'node_update', text="execute ")
            if envars.node_update == "MESSAGE":
                layout.prop(envars, 'node_frameMessage', text="message")        
        else:
            layout.label(text="Node tree execute mode:" + envars.node_update) 
            if envars.node_update == "MESSAGE":
                layout.label(text="Execute on message: " + envars.node_frameMessage)        
            layout.label(text="Node message handlers:")
            col = layout.column()
            for item in bpy.context.scene.OSC_nodes:
                col_box = col.column()
                box = col_box.box()
                colsub = box.column()
                row = colsub.row(align=True)

                row.prop(item, "ui_expanded", text = "", 
                         icon='DISCLOSURE_TRI_DOWN' if item.ui_expanded else 'DISCLOSURE_TRI_RIGHT', 
                         emboss = False)
                row.label(text = "", 
                        icon='EXPORT' if item.osc_direction == "OUTPUT" else 'IMPORT')
                
                sub = row.row()
                sub.active = item.enabled
                sub.label(text=item.osc_address)

                if item.ui_expanded:
                    split = colsub.row().split(factor=0.2)
                    split.label(text="direction:")
                    split.label(text=item.osc_direction)

                    split = colsub.row().split(factor=0.2)
                    split.label(text="address:")
                    split.label(text=item.osc_address)

                    split = colsub.row().split(factor=0.2)
                    split.label(text="datapath:")
                    split.label(text=item.data_path)
        
        #layout.label(text="Works only if \'Auto Execution\' and \'Porperty Changed\' is toggled on", icon="ERROR")
        layout.label(text="Works only with AnimationNodes if ", icon="ERROR")
        layout.label(text="      \'Auto Execution\' and")
        layout.label(text="      \'Property Changed\' is toggled on")
                            

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

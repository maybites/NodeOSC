import bpy
import platform
from pathlib import Path

def prettyTime(seconds):
    if seconds > 1.5: return "{:.2f} s".format(seconds)
    else: return "{:.4f} ms".format(seconds * 1000)
    
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
        column = layout.column(align=True)
        col_box = column.column()
        col = col_box.box()
        if envars.isServerRunning == False:
            row = col.row(align=True)
            row.prop(envars, 'isUIExpanded', text = "", 
                        icon='DISCLOSURE_TRI_DOWN' if envars.isUIExpanded else 'DISCLOSURE_TRI_RIGHT', 
                        emboss = False)
            if addon_prefs.usePyLiblo == False:
                row.operator("nodeosc.oscpy_operator", text='Start', icon='PLAY')
            else:
                row.operator("nodeosc.pythonosc_operator", text='Start', icon='PLAY')
            row.prop(addon_prefs, "usePyLiblo", text = '', icon='CHECKBOX_HLT' if addon_prefs.usePyLiblo else 'CHECKBOX_DEHLT')

            if envars.isUIExpanded:
                col1 = col.column(align=True)
                row1 = col1.row(align=True)
                row1.prop(envars, 'udp_in', text="In")
                row1.prop(envars, 'port_in', text="Port")
                col2 = col.column(align=True)
                row2 = col2.row(align=True)
                row2.prop(envars, 'udp_out', text="Out")
                row2.prop(envars, 'port_out', text="Port")
                col.prop(envars, 'input_rate', text="input rate(ms)")
                col.prop(envars, 'output_rate', text="output rate(ms)")
                col.prop(envars, 'repeat_address_filter_IN', text="Filter incomming")
                col.prop(envars, 'repeat_argument_filter_OUT', text="Filter outgoing")
                col.prop(envars, 'autorun', text="Start at Launch")
        else:
            row = col.row(align=True)
            row.prop(envars, 'isUIExpanded', text = "", 
                        icon='DISCLOSURE_TRI_DOWN' if envars.isUIExpanded else 'DISCLOSURE_TRI_RIGHT', 
                        emboss = False)
            if addon_prefs.usePyLiblo == False:
                row.operator("nodeosc.oscpy_operator", text='osc server is running...', icon='PAUSE')
            else:
                row.operator("nodeosc.pythonosc_operator", text='python osc server is running..', icon='PAUSE')
                 
            if envars.isUIExpanded:
                col.label(text=" listening at " + envars.udp_in + " on port " + str(envars.port_in))
                col.label(text=" sending to " + envars.udp_out + " on port " + str(envars.port_out))
            
                col.prop(envars, 'input_rate', text="input rate(ms)")

                col.prop(bpy.context.scene.nodeosc_envars, 'message_monitor', text="Monitoring and Error reporting")
                col.prop(envars, 'repeat_address_filter_IN', text="Filter incomming")
                col.prop(envars, 'repeat_argument_filter_OUT', text="Filter outgoing")
                col.prop(envars, 'debug_monitor')

                if bpy.context.scene.nodeosc_envars.message_monitor == True: 
                    box = col.box()
                    row5 = box.column(align=True)
                    row5.label(text = "input: " + prettyTime(envars.executionTimeInput), icon = "TIME")
                    row5.label(text = "output: " + prettyTime(envars.executionTimeOutput), icon = "TIME")
                    row6 = box.column(align=True)
                    if addon_prefs.usePyLiblo == False:
                        row6.label(text="Last OSC message:")
                        row6.prop(envars, 'lastaddr', text="address")
                        row6.prop(envars, 'lastpayload', text="values")
            
                    

            
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
        if envars.isServerRunning == False:
            layout.label(text="Message handlers:")
        else:
            layout.label(text="Message handlers: (stop server for changes)")
        index = 0
        col = layout.column()
        for item in bpy.context.scene.NodeOSC_keys:
            col_box = col.column()
            box = col_box.box()
            #box.enabled = not envars.isServerRunning
            colsub = box.column()
            row = colsub.row(align=True)

            row.prop(item, "ui_expanded", text = "", 
                        icon='DISCLOSURE_TRI_DOWN' if item.ui_expanded else 'DISCLOSURE_TRI_RIGHT', 
                        emboss = False)

            sub1 = row.row()
            sub1.enabled = not envars.isServerRunning
            sub1.prop(item, "enabled", text = "", 
                        icon='CHECKBOX_HLT' if item.enabled else 'CHECKBOX_DEHLT', 
                        emboss = False)
            if item.osc_direction != 'INPUT' and item.dp_format_enable:
                sub1.label(icon='ERROR')
            sub1.prop(item, "osc_direction", text = "", emboss = False, icon_only = True)
                        
            sub2 = row.row()
            sub2.active = item.enabled
            sub2.label(text=item.osc_address)

            submove = sub2.row(align=True)
            submove.operator("nodeosc.moveitem_up", icon='TRIA_UP', text='').index = index
            submove.operator("nodeosc.moveitem_down", icon='TRIA_DOWN', text = '').index = index

            subsub = sub2.row(align=True)
            if not envars.isServerRunning:
                subsub.operator("nodeosc.createitem", icon='ADD', text='').copy = index
                subsub.operator("nodeosc.deleteitem", icon='PANEL_CLOSE', text = "").index = index

            if envars.isServerRunning and envars.message_monitor:
                subsub.operator("nodeosc.pick", text='', icon='EYEDROPPER').i_addr = item.osc_address
            
            if item.ui_expanded:
                dataColumn = colsub.column(align=True)
                dataColumn.enabled = not envars.isServerRunning
                dataSplit = dataColumn.split(factor = 0.2)
                
                colLabel = dataSplit.column(align = True)
                colData = dataSplit.column(align = True)
                
                colLabel.label(text='address')
                address_row = colData.row(align = True)
                address_row.prop(item, 'osc_address',text='', icon_only = True)
                if item.osc_direction != "INPUT":
                    address_row.prop(item, 'filter_repetition',text='', icon='CHECKBOX_HLT' if item.filter_repetition else 'CHECKBOX_DEHLT', 
                        emboss = False)
                if item.osc_direction != "OUTPUT":
                    address_row.prop(item, 'filter_enable',text='', icon='MODIFIER' if item.filter_enable else 'MODIFIER_DATA', 
                        emboss = False)
 
                if item.filter_enable and item.osc_direction != "OUTPUT":
                    colLabel.label(text='')
                    colData.prop(item,'filter_eval',text='filter')   
                             
                colLabel.label(text='datapath')
                datapath_row = colData.row(align = True)
                datapath_row.prop(item, 'data_path',text='')
                
                if item.osc_direction == "INPUT":
                    datapath_row.prop(item, 'dp_format_enable',text='', icon='MODIFIER' if item.dp_format_enable else 'MODIFIER_DATA', 
                        emboss = False)
                if item.osc_direction != 'INPUT' and item.dp_format_enable:
                    datapath_row.label(icon='ERROR')
                                
                if item.dp_format_enable and item.osc_direction == "INPUT":
                    colLabel.label(text='')
                    colData.prop(item,'dp_format',text='format')   
               
                colLabel.label(text='args[idx]')
                args_row = colData.row(align = True)
                args_row.prop(item, 'osc_index',text='')
                if item.dp_format_enable and item.osc_direction == "INPUT":
                    args_row.prop(item, 'loop_enable',text='', icon='MODIFIER' if item.loop_enable else 'MODIFIER_DATA', 
                        emboss = False)
                    if item.loop_enable:
                        colLabel.label(text='')
                        colData.prop(item,'loop_range',text='range')    
                                              
            index = index + 1
        
        if envars.isServerRunning == False:
            layout.operator("nodeosc.createitem", icon='PRESET_NEW', text='Create new message handler').copy = -1

        layout.separator()

        row = layout.row(align=True)
        row.operator("nodeosc.export", text='Export OSC Config')
        row.operator("nodeosc.import", text='Import OSC Config')
        layout.operator("nodeosc.importks", text='Import Keying Set')

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
        if envars.isServerRunning == False:
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
            for item in bpy.context.scene.NodeOSC_nodes:
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
    OSC_PT_Operations,
    OSC_PT_Nodes,
)

def register():
    for cls in panel_classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(panel_classes):
        bpy.utils.unregister_class(cls)

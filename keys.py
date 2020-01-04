import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

class NodeOSCMsgValues(bpy.types.PropertyGroup):
        #key_path = bpy.props.StringProperty(name="Key", default="Unknown")
        address: bpy.props.StringProperty(name="Address", default="")
        data_path: bpy.props.StringProperty(name="Data path", default="")
        id: bpy.props.StringProperty(name="ID", default="")
        osc_type: bpy.props.StringProperty(name="Type", default="Unknown")
        osc_index: bpy.props.StringProperty(name="Type", default="Unknown")
        value: bpy.props.StringProperty(name="Value", default="Unknown")
        idx: bpy.props.IntProperty(name="Index", min=0, default=0)

class NodeOSC_ImportKS(Operator):
    bl_idname = "nodeosc.importks"
    bl_label = "Import a Keying Set"
    bl_options = {'UNDO'}
    bl_description ="Import the keys of the active Keying Set"

    def verifdefaddr(self,context):
        if context.scene.nodeosc_defaultaddr[0] != "/":
            context.scene.nodeosc_defaultaddr = "/"+context.scene.nodeosc_defaultaddr

    bpy.types.Scene.nodeosc_defaultaddr = bpy.props.StringProperty(default="/blender", description='Form new addresses based on this keyword',update=verifdefaddr)

    def execute(self, context):
        ks = bpy.context.scene.keying_sets.active
        t_arr = [] #temporary array for data_path,id
        id_n = -1

        if str(ks) != "None":
            for items in ks.paths:
                if str(items.id) != "None":     #workaround to avoid bad ID Block (Nodes)

                    tvar_ev,path,prop = parse_ks(items)

                    #Let's break tuple properties into several ones
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
                    self.report({'ERROR'}, "Missing ID block !")


            #what is the highest ID number ?
            for item in bpy.context.scene.OSC_keys:
                split = item.address.split('/')
                try:
                    if split[1] == bpy.context.scene.nodeosc_defaultaddr[1:]:
                        if int(split[-1]) > id_n:
                            id_n = int(split[-1])
                except:
                    pass


            #Transfer of tvar2 into the OSC_keys_tmp property
            bpy.context.scene.OSC_keys_tmp.clear()
            index = 0
            for i,j in t_arr:
                my_item = bpy.context.scene.OSC_keys_tmp.add()
                my_item.id = i
                my_item.idx = index
                my_item.data_path = j
                #for custom prop
                if i[0:2] == '["' and i[-2:] == '"]':
                    t_eval = my_item.data_path + my_item.id
                #for the others
                else:
                    t_eval = my_item.data_path + "." + my_item.id

                my_item.osc_type = repr(type(eval(t_eval)))[8:-2]
                index = index + 1

            #Copy addresses from OSC_keys if there are some
            for item_tmp in bpy.context.scene.OSC_keys_tmp:
                for item in bpy.context.scene.OSC_keys:
                    if item_tmp.id == item.id and item_tmp.data_path == item.data_path:
                        item_tmp.address = item.address
                        item_tmp.idx = item.idx
                if item_tmp.address == "":
                    id_n += 1
                    item_tmp.address = bpy.context.scene.nodeosc_defaultaddr + "/" + str(id_n)

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


def register():
    bpy.utils.register_class(NodeOSCMsgValues)
    bpy.types.Scene.OSC_keys = bpy.props.CollectionProperty(type=NodeOSCMsgValues)
    bpy.types.Scene.OSC_keys_tmp = bpy.props.CollectionProperty(type=NodeOSCMsgValues)
    bpy.utils.register_class(NodeOSC_ImportKS)


def unregister():
    bpy.utils.unregister_class(NodeOSC_ImportKS)
    del bpy.types.Scene.OSC_keys
    del bpy.types.Scene.OSC_keys_tmp
    bpy.utils.unregister_class(NodeOSCMsgValues)



# AddOSC
OSC support in the viewport for Blender, see: http://www.jpfep.net/pages/addosc/

## Usage

This fork has some redesign and uses a new Osc config file structure:

    {
        "/skeleton/Avatar2/bone/1/position":{  
            "data_path":"bpy.data.objects['Cube']",
            "id":"location",
            "osc_type":"fff",
            "osc_index":"(0, 1, 2)"
        },
        "/skeleton/Avatar2/bone/1/quat":{
            "data_path":"bpy.data.objects['Cube']",
            "id":"rotation_quaternion",
            "osc_type":"ffff",
            "osc_index":"(3, 0, 1, 2)"
        }
    }

you MUST now specify the osc-indices to be used.

for example:

if you receive a message like

/skeleton/Avatar2/bone/1/quat 0.1 0.2 0.3 1.

and you know that this quaternion has a different order (qx, qy, qz, qw) than blender (qw, qx, qy, qz), you can now specify which osc-arguments should be used in which order:

    "osc_index":"(3, 0, 1, 2)"

will us thus send a list like

    1. 0.1 0.2 0.3

to the specified path and ID

This fork is updated to work with blender 2.8

AddOSC relies on the python module python-osc (by Attwad): 
https://pypi.python.org/pypi/python-osc/
https://github.com/attwad/python-osc

 

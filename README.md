# NodeOSC 2.3.1
OSC support for nodes and general usage.

This add-on does not require any other add-on to work.

Currently it has node support for
* [Animation Nodes](https://animation-nodes.com/)
* [Sorcar](https://blender-addons.org/sorcar-addon/)

## Download

latest release from [here](https://github.com/maybites/blender.NodeOSC/releases/latest)

## Usage

please visit the [wiki](https://github.com/maybites/blender.NodeOSC/wiki) for more info.

### Video Tutorial

<a href="https://youtu.be/w_Nye09FyRQ" target="_blank"><img src="http://img.youtube.com/vi/w_Nye09FyRQ/0.jpg"
alt="NodeOSC Part One" width="240" height="180" border="10" /></a>

## Credits

written by maybites (2021)

heavily inspired by and code used from http://www.jpfep.net/pages/addosc/ and http://www.jpfep.net/pages/addroutes/.

NodeOSC relies on

* the pure [python module](https://pypi.org/project/oscpy/) [oscPy](https://github.com/kivy/oscpy) (by Kivy).
* the pure [python module](https://pypi.org/project/python-osc/) [python-osc](https://github.com/attwad/python-osc) (by Attwad).


## ChangeLog

### V2.3.1
fixed output from animation nodes

### V2.3.0
fixed server crash on windows
added incomming address filter

### V2.2.0
added argument filtering
updated testbeds with examples for filter

### V2.1.0
better error reporting
updated testbeds with examples for statement

### V2.0.2
Added ability to execute datapaths as statements

### V2.0.0
Added dynamic evaluation format functionality combined with loops. Inspired by functionality introduced in http://www.jpfep.net/pages/addroutes/. Code cleanup and improved user interface.

### V1.0.9
Added the neat operator I found in http://www.jpfep.net/pages/addroutes/ to create new osc handlers from the context menu while hovering over a user element.

### V1.0.8
Allows to execute function calls with datapath. For example: bpy.ops.screen.animation_play(). values passed on with osc message are ignored.

### V1.0.6
Fixed (hopefully) the reference of the dynamic link library for liblo.

### V1.0.5
It plays now nice if liblo library is not installed.

### V1.0.4
Moved the transformation of AnimationNodes datatype DoubleList into the node.

### V1.0.3
Added AnimationNodes datatype DoubleList to be able to send via OscNumber node.

# NodeOSC
OSC support for nodes and general usage.

This add-on does not require any other add-on to work.

Currently it has node support for
* [Animation Nodes](https://animation-nodes.com/)
* [Sorcar](https://blender-addons.org/sorcar-addon/)


## Download

latest release from [here](https://github.com/maybites/blender.NodeOSC/releases/latest)

## Usage

### Video Tutorial

<a href="https://youtu.be/o9bzujeOyc8" target="_blank"><img src="http://img.youtube.com/vi/o9bzujeOyc8/0.jpg"
alt="NodeOSC Part One" width="240" height="180" border="10" /></a>


see the [wiki](https://github.com/maybites/blender.NodeOSC/wiki) for more info.

I think it is fairly self explanatory (with some intricacies). However, if you have questions please make an issue. This helps me to see where I should focus on the docs...

## Credits

written by maybites (2020)

inspired by and code used from http://www.jpfep.net/pages/addosc/.

NodeOSC relies on

* the pure [python module](https://pypi.python.org/pypi/python-osc/) [python-osc](https://github.com/attwad/python-osc) (by Attwad).
* the [pyliblo wrapper](http://das.nasophon.de/pyliblo/) for [liblo](http://liblo.sourceforge.net/) OSC library.

the addon contains the compiled pyliblo wrapper for windows and OSX, but not for linux.

## ChangeLog

### V1.0.4
Moved the transformation of AnimationNodes datatype DoubleList into the node.

### V1.0.3
Added AnimationNodes datatype DoubleList to be able to send via OscNumber node.

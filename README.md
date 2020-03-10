# NodeOSC
OSC support for nodes and general usage.

This add-on does not require any other add-on to work.

Currently it has node support for
* [Animation Nodes](https://animation-nodes.com/)
* [Sorcar](https://blender-addons.org/sorcar-addon/)

## Download

latest release from [here](https://github.com/maybites/blender.NodeOSC/releases/latest)

## Usage

Always restart the server after any changes to the settings.

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

### V1.0.6
Fixed (hopefully) the reference of the dynamic link library for liblo.

### V1.0.5
It plays now nice if liblo library is not installed

### V1.0.4
Moved the transformation of AnimationNodes datatype DoubleList into the node.

### V1.0.3
Added AnimationNodes datatype DoubleList to be able to send via OscNumber node.

## Building

### pyliblo on osx

* download and install liblo via homebrew.

* then download the [pyliblo](http://das.nasophon.de/pyliblo/) wrapper and build it.

* the pyliblo library (**liblo.cpython-37m-darwin.so**) requires changes of the dynamic link library paths: (described [here](https://stackoverflow.com/questions/33991581/install-name-tool-to-update-a-executable-to-search-for-dylib-in-mac-os-x)).

  `install_name_tool -change /usr/local/opt/liblo/lib/liblo.7.dylib @loader_path/liblo.7.dylib liblo.cpython-37m-darwin.so`

  `install_name_tool -add_rpath @loader_path/. liblo.cpython-37m-darwin.so`

  this way it looks for the **liblo.7.dylib** next to itself and not inside the folder homebrew stored it.

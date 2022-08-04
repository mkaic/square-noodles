# Square Noodles
A Blender addon that makes your noodles straight so you don't have to be.

![short_noodle](https://user-images.githubusercontent.com/80430764/182304566-c04dd279-cea2-4c3e-97b9-98c8709ac7c5.gif)

## Installation
To install, simply click the big green "Code" button at the top of this page, then click Download ZIP. Unzip the result. In Blender, click **Edit > Preferences**, then inside the **Addons** panel, click **Install**. Navigate to the unzipped folder you just downloaded and double click on `square_noodles.py`. Check the box next to the addon in the addons list to enable it.

## Usage
*Note: if you use a non-zero `Noodle Curving` value, right-angle corners that flow "down-left" or "left-down" will have a weird little artifact on them due to node noodles not curving smoothly out of the bottom or left sides of reroute nodes (I think). If you want to fix this, you'll need to set `Noodle Curving` to 0 under `Edit > Preferences > Themes > Node Editor`.*

The addon has only one operator, Square Noodles, which works in any node editor space (compositor/geometry/shader/texture etc.). It only operates on nodes that you have selected. You can run Square Noodles by either searching for it in the `F3` search menu, or by using the default keyboard shortcut, `SHIFT+COMMA` (you actually press the `,` key, you don't type "COMMA").

After using the operator, if you hit `F9` you can edit some of its parameters:
* **Tolerance:** How badly off-axis a noodle has to be before the addon will affect it.
* **Nudge Limit:** The maximum distance the addon will nudge already-existing reroute nodes to make them line up nicely.
* **Noodle Margin:** The minimum distance the addon will try to keep between noodles from multiple outputs on the same node. If that's not intuitive, just mess with it, you'll figure it out.

This addon is not magic and is meant to save time, not revolutionize your workflow. It works best when the node noodles are already decently organized. I hope you find it useful!

I'm fully open to pull requests if anyone wants to submit them. I'm sure my code could be optimized considerably and there are still several missing features I plan to add.

## License
This code is made available under the [GNU GPL 3.0 License](https://www.gnu.org/licenses/gpl-3.0.txt). This is a very permissive open-source software license that allows you to more-or-less do whatever you like with this code.
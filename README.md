# Square Noodles
A Blender addon that converts all your node noodles into neat little right-angled circuitboard-looking-shenanigans.

![short_noodle](https://user-images.githubusercontent.com/80430764/182304566-c04dd279-cea2-4c3e-97b9-98c8709ac7c5.gif)

## Installation
To install, simply click the big green "Code" button, then click Download ZIP. Unzip the result. In Blender, click **Edit > Preferences**, then inside the **Addons** panel, click **Install**. Navigate to the unzipped download folder and double click on `square_noodles.py`. Check the box next to the addon in the addons list to enable it.

## Usage
*Note: If you have Noodle Curving turned on (it's on by default), you might see a few visual glitches when using the addon.*

The addon has only one operator, Square Noodles, which works in any node editor space (compositor/geometry/shader/texture etc.). It only operates on nodes that you have selected. You can run Square Noodles by either searching for it in the `F3` search menu, or by using the default keyboard shortcut, `SHIFT+COMMA` (you actually press the `,` key, you don't type "COMMA").

After using the operator, if you hit `F9` you can edit some of its parameters:
* **Tolerance:** How badly off-axis a noodle has to be before the addon will affect it.
* **Nudge Limit:** The maximum distance the addon will nudge already-existing reroute nodes to make them line up nicely.
* **Noodle Margin:** The minimum distance the addon will try to keep between noodles from multiple outputs on the same node. If that's not intuitive, just mess with it, you'll figure it out.

This addon is not magic and is meant to save time, not revolutionize your workflow. It works best when the node noodles are already decently organized. I hope you find it useful!

I'm fully open to pull requests if anyone wants to submit them. I'm sure my code could be optimized considerably and there are still several missing features I plan to add.

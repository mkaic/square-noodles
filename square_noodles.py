from collections import namedtuple

import bpy
import numpy as np

bl_info = {
    "name": "Square Noodles",
    "description": "Forces selected node noodles to use exclusively right angle turns",
    "author": "Kai Christensen",
    "version": (1, 0),
    "blender": (3, 2, 1),
    "doc_url": "https://github.com/mkaic/square-noodles",
    "support": "COMMUNITY",
    "category": "Node",
}

Socket = namedtuple('Socket', ['socket', 'direction', 'x', 'y'])
Point = namedtuple('Point', ['x', 'y'])

bpy.types.Node.is_reroute = bpy.props.BoolProperty(name="Is Reroute Node", default=False)
bpy.types.Node.x_lock = bpy.props.BoolProperty(name="X Lock", default=False)
bpy.types.Node.y_lock = bpy.props.BoolProperty(name="Y Lock", default=False)
bpy.types.NodeSocket.center_offset = bpy.props.FloatProperty(name="Center Offset", default=0)


def get_active_tree(context):
    tree = context.space_data.node_tree
    path = []
    # Get nodes from currently edited tree.
    # If user is editing a group, space_data.node_tree is still the base level (outside group).
    # context.active_node is in the group though, so if space_data.node_tree.nodes.active is not
    # the same as context.active_node, the user is in a group.
    # Check recursively until we find the real active node_tree:
    if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree
            path.append(tree)
    return tree, path


def get_nodes_links(context):
    tree, path = get_active_tree(context)
    return tree.nodes, tree.links


def is_orphan(node):
    sockets = [*node.inputs, *node.outputs]
    linked_status = [x.is_linked for x in sockets]
    return not any(linked_status)

# code for calculating socket positions is taken from a SO post by Markus von Broady


def is_hidden(socket):
    return socket.hide or not socket.enabled


def is_tall(node, socket):
    if socket.type != 'VECTOR':
        return False
    if socket.hide_value:
        return False
    if socket.is_linked:
        return False
    if node.type == 'BSDF_PRINCIPLED' and socket.identifier == 'Subsurface Radius':
        return False  # an exception confirms a rule?
    return True


def assign_output_offsets(node, gap):

    outputs = [n for n in node.outputs if (not n.hide_value) and (n.is_linked)]
    n_out = len(outputs)

    if n_out > 1:
        spread = gap*(n_out-1)
        start = -1*spread/2
        stop = spread/2
        offsets = np.linspace(start=start, stop=stop, num=n_out)
        for offset, output in zip(offsets, outputs):
            output.center_offset = offset
            print(offset)
        print([output.center_offset for output in outputs])


def get_socket_dict(node):
    inputs = list(reversed(node.inputs))
    outputs = node.outputs

    # Empty dict for holding input and output socket coordinates
    socket_dict = {'input': {}, 'output': {}}

    Y_TOP = 35.0

    NORMAL_Y_BOTTOM = 17.0
    NORMAL_HEIGHT = 22.0

    VEC_Y_BOTTOM = 75
    VEC_HEIGHT = 82.5

    if (node.bl_idname != 'NodeReroute') and (not node.hide):
        # node.dimensions is mysteriously off by a factor of 2
        node_width = node.dimensions.x / 2
        node_height = node.dimensions.y / 2

        # Walk up the inputs and store their positions (have to account for "tall" inputs)
        x = node.location.x
        y = node.location.y - node_height
        counter = 0
        for i in inputs:

            if is_hidden(i):
                continue

            tall = is_tall(node, i)

            if (counter == 0) and (tall):
                y += VEC_Y_BOTTOM
            if (counter == 0) and (not tall):
                y += NORMAL_Y_BOTTOM
            if (counter != 0) and (tall):
                y += VEC_HEIGHT
            if (counter != 0) and (not tall):
                y += NORMAL_HEIGHT

            socket_dict['input'][i.identifier] = Socket(i, 'input', x, y)
            counter += 1

        # Walk down the outputs and store their positions
        x = node.location.x + node_width - 1.0
        y = node.location.y

        counter = 0
        for o in outputs:
            if is_hidden(o):
                continue

            if counter == 0:
                y -= Y_TOP
            if counter != 0:
                y -= NORMAL_HEIGHT

            socket_dict['output'][o.identifier] = Socket(o, 'output', x, y)
            counter += 1

    # For when the node is collapsed with sockets arranged in a semicircle at either end
    if (node.bl_idname != 'NodeReroute') and (node.hide):
        # node.dimensions is mysteriously off by a factor of 2
        node_width = node.dimensions.x / 2
        node_height = node.dimensions.y / 2

        Y_CENTER_OFFSET = 10.0

        radius = node_height/2
        input_circle_center = Point(node.location.x + radius, node.location.y - Y_CENTER_OFFSET)
        output_circle_center = Point(node.location.x + node_width - radius, node.location.y - Y_CENTER_OFFSET)

        visible_inputs = [i for i in inputs if not is_hidden(i)]
        n_in = len(visible_inputs)
        slice_angle = np.pi/(n_in+1)
        for idx, i in enumerate(visible_inputs):

            slice = idx+1
            start = 3*np.pi/2
            x = input_circle_center.x + (np.cos(start-(slice*slice_angle))*radius)
            y = input_circle_center.y + (np.sin(start-(slice*slice_angle))*radius)

            socket_dict['input'][i.identifier] = Socket(i, 'input', x, y)

        visible_outputs = [o for o in outputs if not is_hidden(o)]
        n_out = len(visible_outputs)
        slice_angle = np.pi/(n_out+1)
        for idx, o in enumerate(visible_outputs):

            slice = idx+1
            start = np.pi/2
            x = output_circle_center.x + (np.cos(start-(slice*slice_angle))*radius)
            y = output_circle_center.y + (np.sin(start-(slice*slice_angle))*radius)

            socket_dict['output'][o.identifier] = Socket(o, 'output', x, y)

    if node.bl_idname == 'NodeReroute':
        x, y = node.location
        for i in node.inputs:
            socket_dict['input'][i.identifier] = Socket(i, 'input', x, y)
        for o in node.outputs:
            socket_dict['output'][o.identifier] = Socket(o, 'output', x, y)

    return socket_dict


def check_aligned(socket_1, socket_2, tolerance):
    x1, y1 = (socket_1.x, socket_1.y)
    x2, y2 = (socket_2.x, socket_2.y)
    return (abs(x1 - x2) < tolerance) or (abs(y1 - y2) < tolerance)


class NODE_OT_square_noodles(bpy.types.Operator):

    # Metadata class variables used by Blender to construct the operator's F3 menu button
    bl_idname = "node.square_noodles"
    bl_label = "Square Noodles"
    bl_description = \
        "Forces all non-locked noodles connect to selected nodes to be \
        straight lines with right-angle connections where necessary"
    bl_options = {'REGISTER', 'UNDO'}

    tolerance: bpy.props.FloatProperty(name="Tolerance",
                                       description="How off-axis a noodle must be before it is operated on.",
                                       default=5.0,
                                       min=1.0,
                                       max=25.0)
    nudge_limit: bpy.props.FloatProperty(name="Nudge Limit",
                                         description="Maximum distance existing reroute nodes will be nudged to try to align them before adding new reroute nodes.",
                                         default=100.0,
                                         min=0.0,
                                         max=200)
    noodle_margin: bpy.props.FloatProperty(name="Noodle Margin",
                                           description="Distance which overlapping noodles from different node outputs will hopefully be separated by.",
                                           default=20,
                                           min=0,
                                           max=100)

    # The poll classmethod is called by Blender to determine whether the operator can be used in a given context. In our case,
    # we don't want it to be possible to use the operator outside of a Node Editor because we'd get an error if we tried that.
    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        status = (space_data.type == 'NODE_EDITOR') and (space_data.node_tree is not None)
        return status

    # The function that's run when you click on the operator in the menu.
    def execute(self, context):

        # If snapping is on, turn it off. If it was on we'll turn it back on when we're done.
        snapping_on = context.tool_settings.use_snap_node
        if snapping_on:
            context.tool_settings.use_snap_node = False

        global_nodes, global_links = get_nodes_links(context)

        valid_nodes = [n for n in global_nodes if n.select
                       and not is_orphan(n)]

        if len(valid_nodes) == 0:
            print('No nodes selected')
            return {'CANCELLED'}

        socket_dict = {}
        # Loops over all selected nodes
        for node in global_nodes:
            socket_dict[node.name] = get_socket_dict(node)
            node.is_reroute = node.bl_idname == 'NodeReroute'
            node.x_lock = not node.is_reroute
            node.y_lock = not node.is_reroute
            assign_output_offsets(node, self.noodle_margin)

        for root_node in valid_nodes:

            root_socket_dict = socket_dict[root_node.name]

            # for each linked socket, we'll loop through its links
            for root_direction in ['input', 'output']:
                linked_sockets = [s[1] for s in root_socket_dict[root_direction].items() if s[1].socket.is_linked]
                for root_socket_info in linked_sockets:
                    links = root_socket_info.socket.links
                    target_sockets = []
                    for link in links:

                       # Determining the target node and socket our root node and socket are connected to.
                        if root_direction == 'input':
                            target_node = link.from_node
                            target_socket = link.from_socket
                            target_direction = 'output'

                        if root_direction == 'output':
                            target_node = link.to_node
                            target_socket = link.to_socket
                            target_direction = 'input'

                        # Get a list of the sockets of the node we're connected to with this link,
                        # then filter for either inputs or outputs depending on the root socket direction
                        target_sockets.append((target_node.name, target_direction, target_socket.identifier))

                    # If we're a reroute node, try to ajust our position:
                    # 1. to be horizontally aligned with the nearest non-reroute socket we're connected to
                    # 2. to be aligned with the socket that requires the smallest non-breaking nudge to align with
                    if root_node.is_reroute:
                        non_reroute_targets, non_reroute_distances = [], []
                        reroute_targets, reroute_x_distances, reroute_y_distances = [], [], []
                        for path in target_sockets:
                            target = socket_dict[path[0]]
                            target = target[path[1]]
                            target = target[path[2]]
                            target_node = target.socket.node
                            x_distance = (target.x - root_socket_info.x)
                            y_distance = (target.y - root_socket_info.y)
                            distance = x_distance**2 + y_distance**2
                            if not target_node.is_reroute:
                                non_reroute_targets.append(target)
                                non_reroute_distances.append(distance)
                            if target_node.is_reroute:
                                reroute_targets.append(target)
                                reroute_x_distances.append(x_distance)
                                reroute_y_distances.append(y_distance)

                        if (len(non_reroute_targets)) > 0 and (not root_node.y_lock):
                            closest_non_reroute_target = non_reroute_targets[np.argmin(non_reroute_distances)]
                            if abs(root_node.location.y - closest_non_reroute_target.y) < self.nudge_limit:
                                root_node.location.y = closest_non_reroute_target.y
                                root_node.y_lock = True

                            # Now that we've tried to align horizontally with the closest non-reroute socket,
                            # we will try to align with the closest reroute node we're connected to, then the
                            # next-closest if that doesn't work, then the next and the next etc. If we do align,
                            # on an axis, we lock that axis for both us and the node we align with.
                            if(len(reroute_targets)) > 0:
                                if (not root_node.x_lock) or (not root_node.y_lock):
                                    distances = list(np.square(reroute_x_distances) + np.square(reroute_y_distances))

                                    for attempt in range(len(reroute_targets)):
                                        closest_idx = np.argmin(distances)
                                        closest_reroute = reroute_targets.pop(closest_idx)
                                        x_distance = reroute_x_distances.pop(closest_idx)
                                        y_distance = reroute_y_distances.pop(closest_idx)
                                        closest_axis = np.argmin((x_distance, y_distance))
                                        if closest_axis == 0:
                                            if (abs(x_distance) < self.nudge_limit) and (not root_node.x_lock):
                                                root_node.location.x = closest_reroute.x
                                                root_node.x_lock = True
                                                closest_reroute.socket.node.x_lock = True
                                            elif (abs(y_distance) < self.nudge_limit) and (not root_node.y_lock):
                                                root_node.location.y = closest_reroute.y
                                                root_node.y_lock = True
                                                closest_reroute.socket.node.y_lock = True

                                        if closest_axis == 1:
                                            if (abs(y_distance) < self.nudge_limit) and (not root_node.y_lock):
                                                root_node.location.y = closest_reroute.y
                                                root_node.y_lock = True
                                                closest_reroute.socket.node.y_lock = True
                                            elif (abs(x_distance) < self.nudge_limit) and (not root_node.x_lock):
                                                root_node.location.x = closest_reroute.x
                                                root_node.x_lock = True
                                                closest_reroute.socket.node.x_lock = True

        # SECOND LOOP. IT DOES NEED TO BE TWO LOOPS.

        for root_node in valid_nodes:

            # We have to refresh our snapshot of the nodetree periodically because we're adding new nodes
            global_nodes, global_links = get_nodes_links(context)
            valid_nodes = [n for n in global_nodes if n.select
                           and not is_orphan(n)]
            for check_node in global_nodes:
                socket_dict[check_node.name] = get_socket_dict(check_node)
                check_node.is_reroute = check_node.bl_idname == 'NodeReroute'

            root_socket_dict = socket_dict[root_node.name]

            # for each linked socket, we'll loop through its links
            for root_direction in ['input', 'output']:
                linked_sockets = [s[1] for s in root_socket_dict[root_direction].items() if s[1].socket.is_linked]
                for root_socket_info in linked_sockets:
                    links = root_socket_info.socket.links
                    target_sockets = []
                    for link in links:

                       # Determining the target node and socket our root node and socket are connected to.
                        if root_direction == 'input':
                            target_direction = 'output'
                            target_node = link.from_node
                            target_socket = link.from_socket

                        if root_direction == 'output':
                            target_direction = 'input'
                            target_node = link.to_node
                            target_socket = link.to_socket

                        target_socket_info = socket_dict[target_node.name][target_direction][target_socket.identifier]

                        # First, we check if these coordinates are already aligned (within a margin of error)
                        if check_aligned(root_socket_info, target_socket_info, self.tolerance):
                            # If they are, we can skip this link
                            continue
                        else:

                            root_x, root_y = root_socket_info.x, root_socket_info.y
                            target_x, target_y = target_socket_info.x, target_socket_info.y

                            global_links.remove(link)

                            root_socket = root_socket_info.socket

                            both_nodes = (not root_node.is_reroute) and (not target_node.is_reroute)
                            both_reroutes = (root_node.is_reroute) and (target_node.is_reroute)
                            hetero = (not both_nodes) and (not both_reroutes)

                            # If the nodes are both non-reroutes, create a "stairstep" pattern
                            # between them by deleting the existing link and adding two new reroute nodes and 3 new links
                            if both_nodes:
                                average_x_coord = (root_x + target_x) / 2

                            # Adding a calculated offset to the center x coords so multiple wires are less
                            # likely to overlap
                                if root_socket_info.direction == 'input':
                                    middle_x_coord = average_x_coord + target_socket.center_offset
                                if root_socket_info.direction == 'output':
                                    middle_x_coord = average_x_coord + root_socket.center_offset

                                reroute_1 = global_nodes.new('NodeReroute')
                                reroute_1.location = (middle_x_coord, root_y)

                                reroute_2 = global_nodes.new('NodeReroute')
                                reroute_2.location = (middle_x_coord, target_y)

                                if root_socket_info.direction == 'input':
                                    global_links.new(reroute_1.outputs[0], root_socket)
                                    global_links.new(target_socket, reroute_2.inputs[0])
                                    global_links.new(reroute_2.outputs[0], reroute_1.inputs[0])
                                if root_socket_info.direction == 'output':
                                    global_links.new(root_socket, reroute_1.inputs[0])
                                    global_links.new(reroute_2.outputs[0], target_socket)
                                    global_links.new(reroute_1.outputs[0], reroute_2.inputs[0])

                            # If one node is a reroute and the other isn't, though, we can add in just one reroute node
                            # and have it horizontally aligned with the normal node while vertically aligned with the
                            # reroute node.
                            if hetero:
                                if root_node.is_reroute:
                                    reroute = global_nodes.new('NodeReroute')
                                    reroute.location = root_x, target_y
                                if target_node.is_reroute:
                                    reroute = global_nodes.new('NodeReroute')
                                    reroute.location = target_x, root_y

                                if root_socket_info.direction == 'input':
                                    global_links.new(reroute.outputs[0], root_socket)
                                    global_links.new(target_socket, reroute.inputs[0])
                                if root_socket_info.direction == 'output':
                                    global_links.new(root_socket, reroute.inputs[0])
                                    global_links.new(reroute.outputs[0], target_socket)

                            # If both nodes are reroutes, we just travel sideways from the root node,
                            # place a reroute, then up/down to the target node
                            if both_reroutes:

                                reroute = global_nodes.new('NodeReroute')
                                reroute.location = target_x, root_y

                                if root_socket_info.direction == 'input':
                                    global_links.new(reroute.outputs[0], root_socket)
                                    global_links.new(target_socket, reroute.inputs[0])
                                if root_socket_info.direction == 'output':
                                    global_links.new(root_socket, reroute.inputs[0])
                                    global_links.new(reroute.outputs[0], target_socket)

        # If the user had snapping on before, turn it back on.
        if snapping_on:
            context.tool_settings.use_snap_node = True

        return {'FINISHED'}


# store keymaps here to access after registration
addon_keymaps = []


def register():
    bpy.utils.register_class(NODE_OT_square_noodles)

    # handle the keymap
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')

    kmi = km.keymap_items.new(NODE_OT_square_noodles.bl_idname, ',', 'PRESS', ctrl=False, shift=True)
    kmi.properties.total = 4

    addon_keymaps.append((km, kmi))


def unregister():
    bpy.utils.unregister_class(NODE_OT_square_noodles)

    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == '__main__':
    register()

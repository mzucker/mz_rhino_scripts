import rhinoscriptsyntax as rs
import mzrhinoutils as mz

def make_hinge(num_knuckles,
               knuckle_height,
               knuckle_radius,
               thickness,
               leaf_length,
               gap,
               add_vents):

    origin = [0,0,0]
    hinge_height = num_knuckles * knuckle_height

    ######################################################################
    # Make pin with caps

    cap_radius = knuckle_radius - 0.5*thickness - gap
    cap_height = thickness
    
    cap_bottom = rs.AddCylinder(origin, cap_height, cap_radius)
    
    cap_top = rs.AddCylinder([0, 0, hinge_height-cap_height],
                              cap_height, cap_radius)
    
    pin_radius = knuckle_radius - (gap + thickness)
 
    pin = rs.AddCylinder(origin, hinge_height, pin_radius)

    pin = rs.BooleanUnion([pin, cap_bottom, cap_top])

    ######################################################################
    # Make knuckle and holes

    right_knuckle = rs.AddCylinder(origin, hinge_height, knuckle_radius)

    knuckle_pin_hole = rs.AddCylinder(origin, hinge_height, knuckle_radius-thickness)
    
    knuckle_bottom_hole = rs.AddCylinder(origin, cap_height + gap,
                                         cap_radius+gap)
    
    knuckle_top_hole = rs.AddCylinder([0, 0, hinge_height-cap_height-gap],
                                    cap_height + gap, cap_radius+gap)


    ######################################################################
    # Make leaves

    right_p0 = (0,  knuckle_radius, 0)
    right_p1 = (leaf_length, knuckle_radius-thickness, hinge_height)

    right_leaf = rs.AddBox(mz.box_verts_from_corners(right_p0, right_p1))

    right_leaf = rs.BooleanUnion([right_knuckle, right_leaf])

    right_leaf, = rs.BooleanDifference([right_leaf],
                                       [knuckle_pin_hole,
                                        knuckle_bottom_hole,
                                        knuckle_top_hole])

    mirror_leaf = rs.XformMirror(origin, (1, 0, 0))
    
    left_leaf = rs.TransformObject(right_leaf, mirror_leaf, True)
    
    ######################################################################
    # Cut out alternating knuckles

    z0 = 0
    sz = knuckle_radius + gap

    left_boxes = []
    right_boxes = []

    vent_height = knuckle_height - 4*thickness

    for stage in range(num_knuckles):

        z1 = z0 + knuckle_height

        if stage == 0:
            cur_z0 = z0
        else:
            cur_z0 = z0 - 0.5*gap

        if stage == num_knuckles-1:
            cur_z1 = z1
        else:
            cur_z1 = z1 + 0.5*gap
            
        knuckle_box = rs.AddBox(mz.box_verts_from_corners((-sz, -sz, cur_z0),
                                                          (sz, sz, cur_z1)))

        if stage % 2 == 0:
            left_boxes.append(knuckle_box)
        else:
            right_boxes.append(knuckle_box)

        if add_vents:
            zmid = z0 + 0.5*knuckle_height
            za = zmid - 0.5*vent_height
            zb = zmid + 0.5*vent_height
            mid_box = rs.AddBox(mz.box_verts_from_corners((-sz, -pin_radius-gap,  za),
                                                          (sz, pin_radius+gap, zb)))

            if stage % 2 == 0:
                right_boxes.append(mid_box)
            else:
                left_boxes.append(mid_box)

        z0 += knuckle_height


    left_leaf, = rs.BooleanDifference([left_leaf], left_boxes)
    right_leaf, = rs.BooleanDifference([right_leaf], right_boxes)

    rs.SelectObjects([left_leaf, right_leaf, pin])
    rs.Command('MergeAllFaces')

def default_hinge():

    param_info = [
        ('integer', 'Number of knuckles', 3),
        ('real', 'Height of knuckle', 20.0),
        ('real', 'Radius of knuckle', 5.0),
        ('real', 'Thickness', 2.0),
        ('real', 'Length of leaf', 40.0),
        ('real', 'Gap width', 0.25),
        ('boolean', 'Add vents?', True)
    ]

    params = mz.get_params(param_info)
    if params is None:
        return
        
    make_hinge(*params)

if __name__ == '__main__':
    default_hinge()

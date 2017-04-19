import rhinoscriptsyntax as rs
import mzrhinoutils as mz

num_levels = 8
num_sides = 5
strut_rad = 0.25
ring_rad = 0.3
ring_vscale = 2.0

######################################################################
# given a curve in the XZ plane, find the point along it
# that is closest to a supplied "origin" point.
#
# return the closest distance, along with the closest displacement
# (point - origin)
#
def get_inscribed_radius(curve, origin=(0,0,0)):

    # find out how many segments in this curve
    nsegs = rs.PolyCurveCount(curve)

    # record closest distance & point
    best_r = None
    best_point = None

    # for each curve segment
    for seg in range(nsegs):
        # get the curve parameter (i.e. input to spline function) that
        # approaches the origin most closely for this segment.
        param = rs.CurveClosestPoint(curve, origin, seg)

        # evaluate the curve at that parameter to get 3D point location
        point = rs.EvaluateCurve(curve, param)

        # get the displacement from the origin
        point = mz.vec_sub(list(point), origin)

        # get length
        r = mz.vec_length(point)

        # update best 
        if best_r is None or r < best_r:
            best_r = r
            best_point = point

    # return distance & point
    return best_r, best_point

######################################################################
# return the profile curve and cross-section curve

def get_two_curves():

    # get list of selected objects
    sel = rs.SelectedObjects()

    # clear selection
    rs.UnselectAllObjects()

    # if there were 2 objects selected...
    if len(sel) == 2:
        c1, c2 = sel
        # ...and they are curves...
        if rs.IsCurve(c1) and rs.IsCurve(c2):
            # the closed one is the cross-section, the open one is profile
            if rs.IsCurveClosed(c2):
                return c1, c2
            elif rs.IsCurveClosed(c1):
                return c2, c1

    # none of the things above worked, ask the user
    profile = rs.GetObject('Pick the profile curve', rs.filter.curve)

    # let user cancel
    if profile is None:
        return None, None

    cross = rs.GetObject('Pick the cross-section curve', rs.filter.curve)

    # return the curves
    return profile, cross

######################################################################
# convert a list of 8 points that form an axis-aligned bounding box to
# 2 points: min & max

def box_to_points(box):

    pmin = list(box[0])
    pmax = list(box[0])

    for p in box[1:]:
        pmin = mz.vec_minimum(pmin, p)
        pmax = mz.vec_maximum(pmax, p)

    return pmin, pmax

######################################################################
# our main function

def main():

    # get our curves
    profile, cross = get_two_curves()
    if profile is None or cross is None:
        return

    ##################################################
    # get bounding box for cross section
    
    cross_bbox = rs.BoundingBox([cross])

    cmin, cmax = box_to_points(cross_bbox)

    cz_range = cmax[2] - cmin[2]
    cz = 0.5 * (cmax[2] + cmin[2])

    # make sure it's planar in XY
    if cz_range > 1e-9:
        print 'cross section curve should be planar in XY plane'
        return

    ##################################################
    # get bounding box for profile
    
    profile_bbox = rs.BoundingBox([profile])

    # make sure it's planar in in YZ
    pmin, pmax = box_to_points(profile_bbox)
    
    px_range = pmax[0] - pmin[0]
    
    if px_range > 1e-9:
        print 'profile curve should be planar in YZ plane'
        return

    ##################################################
    # get the point closest to the center for the
    # cross-section curve
    
    r, pc = get_inscribed_radius(cross, [0, 0, cz])

    ##################################################
    # get the range of z-values for the profile curve

    _, _, z0 = pmin
    _, _, z1 = pmax

    ##################################################
    # build list of rings and list of points

    points = []
    ring_pipes = []

    # for each level
    for i in range(num_levels):

        # get the Z value of the ith plane
        u = float(i) / (num_levels-1)
        z = z0 + u*(z1 - z0)

        # build the i'th plane
        plane = rs.PlaneFromNormal([0, 0, z], [0, 0, 1], [1, 0, 0])

        # find out where the plane intersects the profile curve
        intersect = rs.PlaneCurveIntersection(plane, profile)

        # there should be exactly one intersection of type 1 (point)
        if intersect is None or len(intersect) > 1 or intersect[0][0] != 1:
            print 'bad intersection'
            return

        # get the intersection point
        pi = intersect[0][1]

        # get the desired XY radius at this z value
        ri = abs(pi[1])

        # we need to set up some transformations:

        # translate cross section curve down to z=0
        T1 = rs.XformTranslation([0, 0, -cz])

        # scale it along XY by the ratio of radii
        S1 = rs.XformScale([ri/r, ri/r, 1.0])

        # scale a piped cross section along Z by a vertical scale factor
        S2 = rs.XformScale([1.0, 1.0, ring_vscale])

        # translate piped cross section up to our desired z value
        T2 = rs.XformTranslation([0, 0, z])

        # scale and translate cross section curve
        ci = rs.TransformObject(cross, rs.XformMultiply(S1, T1), copy=True)

        # pipe it
        ring = rs.AddPipe(ci, [0, 1], [ring_rad, ring_rad])

        # scale vertically and transform up
        ring = rs.TransformObject(ring, rs.XformMultiply(T2, S2))

        # delete the copy of the cross section curve
        rs.DeleteObject(ci)

        # add to list of ring pipes
        ring_pipes.append(ring)

        # create a rotation by the i'th angle
        angle_i_deg = i*360.0/num_sides
        Ri = rs.XformRotation2(angle_i_deg, [0, 0, 1], [0, 0, 0])

        # transform the closest point by rotation and scale
        pci = rs.PointTransform(pc,
                                rs.XformMultiply(rs.XformMultiply(Ri, T2), S1))

        # add to list of points
        points.append(pci)

    # we have built up a list of points for a single spiral of struts to connect,
    # now we need to pipe them all together and do the ArrayPolar thing around
    # the z axis

    # first build a single spiral of struts
    strut_pipes = []

    for i0 in range(num_levels-1):
        i1 = i0+1
        p0 = points[i0]
        p1 = points[i1]
        l01 = rs.AddLine(p0, p1)
        pipe = rs.AddPipe(l01, [0, 1], [strut_rad, strut_rad], 1)
        rs.DeleteObject(l01)
        strut_pipes.append(pipe)

    # then array polar around Z axis
    all_strut_pipes = []
    all_strut_pipes += strut_pipes

    for j in range(1, num_sides):
        angle_j_deg = j*360.0/num_sides
        Rj = rs.XformRotation2(angle_j_deg, [0, 0, 1], [0, 0, 0])
        all_strut_pipes += rs.TransformObjects(strut_pipes, Rj, copy=True)

    # now just select all the objects we created
    rs.SelectObjects(ring_pipes + all_strut_pipes)

    # done!
    print 'yay'

    
if __name__ == '__main__':

    main()

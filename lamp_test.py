import rhinoscriptsyntax as rs
import mzrhinoutils as mz

num_levels = 8
num_sides = 5
strut_rad = 0.25
ring_rad = 0.3
ring_vscale = 2.0


def get_inscribed_radius(curve, origin=(0,0,0)):

    nsegs = rs.PolyCurveCount(curve)

    best_r = None
    best_point = None

    for seg in range(nsegs):
        param = rs.CurveClosestPoint(curve, origin)
        point = rs.EvaluateCurve(curve, param)
        point = mz.vec_sub(list(point), origin)
        r = mz.vec_length(point)
        if best_r is None or r < best_r:
            best_r = r
            best_point = point

    return best_r, best_point

def get_objects():

    sel = rs.SelectedObjects()
    rs.UnselectAllObjects()
    
    if len(sel) == 2:
        c1, c2 = sel
        if rs.IsCurve(c1) and rs.IsCurve(c2):
            if rs.IsCurveClosed(c2):
                return c1, c2
            elif rs.IsCurveClosed(c1):
                return c2, c1


    profile = rs.GetObject('Pick the profile curve', rs.filter.curve)
    if profile is None:
        return None, None
        
    cross = rs.GetObject('Pick the cross-section curve', rs.filter.curve)

    return profile, cross

def box_to_points(box):

    pmin = list(box[0])
    pmax = list(box[0])

    for p in box[1:]:
        pmin = mz.vec_minimum(pmin, p)
        pmax = mz.vec_maximum(pmax, p)

    return pmin, pmax


def main():

    profile, cross = get_objects()
    if profile is None or cross is None:
        return

    cross_bbox = rs.BoundingBox([cross])

    cmin, cmax = box_to_points(cross_bbox)

    cz_range = cmax[2] - cmin[2]
    cz = 0.5 * (cmax[2] + cmin[2])
    
    if cz_range > 1e-9:
        print 'cross section curve should be planar in XY plane'
        return

    profile_bbox = rs.BoundingBox([profile])
    
    pmin, pmax = box_to_points(profile_bbox)
    
    px_range = pmax[0] - pmin[0]
    
    if px_range > 1e-9:
        print 'profile curve should be planar in YZ plane'
        return


    r, pc = get_inscribed_radius(cross, [0, 0, cz])

    _, _, z0 = pmin
    _, _, z1 = pmax

    points = []
    rings = []

    for i in range(num_levels):
        
        u = float(i) / (num_levels-1)
        z = z0 + u*(z1 - z0)
        plane = rs.PlaneFromNormal([0, 0, z], [0, 0, 1], [1, 0, 0])

        angle_i_deg = i*360.0/num_sides
        Ri = rs.XformRotation2(angle_i_deg, [0, 0, 1], [0, 0, 0])

        intersect = rs.PlaneCurveIntersection(plane, profile)

        if intersect is None or len(intersect) > 1 or intersect[0][0] != 1:
            print 'bad intersection'
            return

        p = intersect[0][1]
        ri = abs(p[1])

        T1 = rs.XformTranslation([0, 0, -cz])
        S1 = rs.XformScale([ri/r, ri/r, 1.0])
        S2 = rs.XformScale([1.0, 1.0, ring_vscale])
        T2 = rs.XformTranslation([0, 0, z])

        ci = rs.TransformObject(cross, rs.XformMultiply(S1, T1), copy=True)

        ring = rs.AddPipe(ci, [0, 1], [ring_rad, ring_rad])

        ring = rs.TransformObject(ring, rs.XformMultiply(T2, S2))
        
        rs.DeleteObject(ci)

        rings.append(ring)

        pci = rs.PointTransform(mz.vec_mul(pc, ri/r),
                                rs.XformMultiply(Ri, T2))
                            
        points.append(pci)

    pipes = []

    for i0 in range(num_levels-1):
        i1 = i0+1
        p0 = points[i0]
        p1 = points[i1]
        l01 = rs.AddLine(p0, p1)
        pipe = rs.AddPipe(l01, [0, 1], [strut_rad, strut_rad], 1)
        rs.DeleteObject(l01)
        pipes.append(pipe)

    all_pipes = []
    all_pipes += pipes

    for j in range(1, num_sides):
        angle_j_deg = j*360.0/num_sides
        Rj = rs.XformRotation2(angle_j_deg, [0, 0, 1], [0, 0, 0])
        pipes2 = rs.TransformObjects(pipes, Rj, copy=True)
        all_pipes += pipes2

    rs.SelectObjects(rings + all_pipes)


    print 'yay'

    
if __name__ == '__main__':

    main()

import rhinoscriptsyntax as rs

################################################################################
# Vector utility functions

def vec_add(a, b):
    return type(a)(ai+bi for ai, bi in zip(a, b))

def vec_sub(a, b):
    return type(a)(ai-bi for ai, bi in zip(a, b))

def vec_dot(a, b):
    return sum(ai*bi for ai, bi in zip(a, b))

def vec_scalar_product(k, a):
    return type(a)(k*ai for ai in a)

def vec_cwise_product(a, b):
    return type(a)(ai*bi for ai, bi in zip(a, b))

def vec_axpy(alpha, a, b):
    return type(a)(alpha*ai + bi for ai, bi in zip(a, b))

def vec_minimum(a, b):
    return type(a)(min(ai, bi) for ai, bi in zip(a,b))

def vec_maximum(a, b):
    return type(a)(max(ai, bi) for ai, bi in zip(a,b))

def vec_argmin(a):
    return min((ai, i) in enumerate(a))[1]

def vec_argmax(a):
    return max((ai, i) in enumerate(a))[1]

def vec3_cross(a, b):
    return type(a)([a[1]*b[2] - a[2]*b[1],
                    a[2]*b[0] - a[0]*b[2],
                    a[0]*b[1] - a[1]*b[0]])

################################################################################
# Geometric utility functions

def box_verts_from_corners(p0, p1):

    x0, y0, z0 = vec_minimum(p0, p1)
    x1, y1, z1 = vec_maximum(p0, p1)
    
    return [(x0, y0, z0), 
            (x1, y0, z0), 
            (x1, y1, z0), 
            (x0, y1, z0),
            (x0, y0, z1), 
            (x1, y0, z1), 
            (x1, y1, z1), 
            (x0, y1, z1)]

def box_verts_from_center_extents(center, extents):
    p0 = vec_axpy(-0.5, extents, center)
    p1 = vec_axpy( 0.5, extents, center)
    return box_verts_from_corners(p0, p1)

################################################################################
# Get parameters

def get_param(dtype, prompt, default):

    if dtype == 'integer':
        rval = rs.GetInteger(prompt, default)
    elif dtype == 'real':
        rval = rs.GetReal(prompt, default)
    elif dtype == 'boolean':
        rval = rs.GetString(prompt, str(default), ['True', 'False'])
        if rval is not None:
            rval = (rval == 'True')
    else:
        raise RuntimeError('bad type in get_param')

    return rval

def get_params(pinfolist):

    rvals = []

    for pinfo in pinfolist:
        dtype, prompt, default = pinfo
        
        rval = get_param(dtype, prompt, default)
        print 'got rval=', rval
        
        if rval is None:
            return None
        
        rvals.append(rval)

    return rvals

################################################################################
# Test functions

def test_vec3():

    a = (1.0, 2.0, 3.0)
    b = (-4.0, 5.0, -6.0)
    c = vec3_cross(a, b)

    print vec_axpy(1.0, a, b)
    print c
    print vec_dot(a, c)
    print vec_dot(b, c)

if __name__ == '__main__':
    test_vec3()

# cython: cdivision=True
# cython: wraparound=False
# cython: boundscheck=False
# cython: language_level=3

from astropy import units as u

cimport numpy as np
import numpy as np

from libc.math cimport sin, cos, atan, round


cpdef interpolate(object region, object two_points_list,sample_density):
    # cdef double lx, ly, rx, ry = region.extent
        
    ret = np.ndarray(two_points_list.shape[0], dtype=object)
    for i in range(len(ret)):
        line = two_points_list[i]
        ret[i] = u.Quantity(_slice_line(line,region,sample_density),'rad')
    return ret



cdef _slice_line(pts,region,sample_density):
    cdef double x1, y1, x2, y2, m, angle, dx, dy, lefX, rigX, topY, botY, x, y, resolution
    x1 = pts[0]
    y1 = pts[1]
    x2 = pts[2]
    y2 = pts[3]
    m = (y2 - y1)/(x2 - x1)
    angle = atan(m)
    resolution = ((sample_density)**(-1)).to('rad').value
    dx = resolution*cos(angle)
    dy = resolution*sin(angle)
    dims = region.dimensions.to('rad')
    center = region.center.to('rad')
    lefX = center.x.value - dims.x.value/2.0
    rigX = center.x.value + dims.x.value/2.0
    topY = center.y.value + dims.y.value/2.0
    botY = center.y.value - dims.y.value/2.0
    possible_length = (((rigX - lefX)**2 + (topY - botY)**2)**(0.5))/resolution
    cdef int flag = 1
    cdef int count = 0
    cdef np.ndarray[np.float64_t, ndim=2] buff = np.ndarray((int(possible_length)+2,2))
    x = x1
    y = y1
    while flag == 1:
        x -= dx
        y -= dy
        flag = x >= lefX and x <= rigX and y >= botY and y <= topY
    flag = 1
    while flag:
        x += dx
        y += dy
        buff[count,0] = x
        buff[count,1] = y
        count += 1
        if not (x >= lefX and x <= rigX and y >= botY and y <= topY):
            flag = 0
    return buff[:count,:]


cpdef arbitrary_slice_axis(pt1,pt2,region,data):
        start = region.loc_to_pixel(pt1)
        end = region.loc_to_pixel(pt2)
        delta = (end - start)
        unit_vec = (end - start).unit_vector
        # ret = np.ndarray((length))
        cdef double sx, sy, x, y
        cdef double ux, uy
        ux = unit_vec.x.value
        uy = unit_vec.y.value
        sx = start.x.value
        sy = start.y.value
        cdef int length = int(delta.magnitude.value)
        cdef int i = 0
        cdef np.ndarray[np.float64_t,ndim=1] ret = np.ndarray(length)
        for i in range(length):
            x = sx + ux * i
            y = sy + uy * i
            # loc = start + unit_vec * i
            # x = int(loc.x.value)
            # y = int(loc.y.value)

            ret[i] = data[<int> round(x),<int> round(y)]
        return ret

cpdef caustic_characteristic_inplace(np.ndarray[np.float64_t,ndim=2] stars, np.ndarray[np.float64_t,ndim=2] locations, double &macro_convergence, double &macro_shear):
    cdef double kapMin = 1.0 - macro_convergence
    cdef double kapMin2 = kapMin*kapMin
    cdef int i, num_stars = stars.shape[0], j, num_locations = locations.shape[0]
    cdef double x1, x2, x1i, x2i, mi
    #accumulators
    cdef double complex gam, gamBar, gamPrime, gamBarPrime, gamPrimeUBar, gamPrimeBarUBar, du, dubar
    #Local only
    cdef double complex u, ubar,r
    cdef double complex I = 1.0j
    cdef np.ndarray[np.float64_t,ndim=2] ret = locations.copy()
    for j in range(0,num_locations):
        gam = macro_shear + 0j
        x1 = locations[j,0]
        x2 = locations[j,1]
        gamBar = macro_shear + 0j
        gamBarPrime = 0 + 0j
        gamPrime = 0 + 0j
        gamPrimeUBar = 0 + 0j
        gamPrimeBarUBar = 0 + 0j
        for i in range(0,num_stars):
            x1i = stars[i,0]
            x2i = stars[i,1]
            u = (x1-x1i) + (x2 - x2i)*I
            ubar = (x1-x1i) - (x2 - x2i)*I
            mi = stars[i,2]
            r = u*ubar
            gam += mi*u*u/r/r
            # gamBar -= mi*ubar*ubar/r/r
            # gamPrime += mi*ubar/r/r
            # gamBarPrime += 2*mi/r/ubar/ubar
            # gamPrimeUBar += 2*mi/r/ubar/ubar
            # gamPrimeBarUBar += mi/r/r
            # gam -= mi*u/((u*uBar)**(2.5))
            # gamBar -= mi*uBar/((u*uBar)**(2.5))
            # gamPrime -= -(1.5*mi*(x1**2.0 - 2.0*x1*x1i + x1i**2.0 + x2**2.0 - 2.0*x2*x2i + x2i**2.0)**(-2.5))/2.0
            # gamBarPrime -= (2.5*mi*((x1 - x1i - I*x2 + I*x2i)*(x1 - x1i + I*x2 - I*x2i))**(-2.5)*(-x1 + x1i + I*x2 - I*x2i)/(x1 - x1i + I*x2 - I*x2i))/2.0
            # gamPrimeUBar -= (2.5*mi*((x1 - x1i - I*x2 + I*x2i)*(x1 - x1i + I*x2 - I*x2i))**(-2.5)*(-x1 + x1i - I*x2 + I*x2i)/(x1 - x1i - I*x2 + I*x2i))/2.0
            # gamPrimeBarUBar -= (-1.5*mi*(x1**2.0 - 2.0*x1*x1i + x1i**2.0 + x2**2.0 - 2.0*x2*x2i + x2i**2.0)**(-2.5))/2.0
        # du = (0.25)*gamBar*gamPrime + (0.25)*gamBarPrime*gam
        # dubar = (0.25)*gamBar*gamPrimeUBar + (0.25)*gamPrimeBarUBar*gam
        ret[j,0] = kapMin2 - abs(gam*gam.conjugate())
        ret[j,1] = abs(dubar*kapMin - du*gam)
    return ret

    
cpdef isolate_caustics(np.ndarray[np.float64_t,ndim=2] magmap, np.ndarray[np.uint8_t, ndim=2] caustics):
    """
    Given a partially completed map of caustics and a magnification map, this function "fills in" the missing caustics.
    """
    print("BROKEN FUNCTION. WILL GO INTO INFINITE LOOP")
    cdef int i, j, ki, kj
    cdef int ii, jj, x, y
    cdef int c = 0
    cdef int rows = magmap.shape[0]
    cdef int cols = magmap.shape[1]
    cdef double highestFound = -40.0;
    while i < rows:
        while j < cols:
            c = 0
            highestFound = -40
            if caustics[i,j] != 0:
                for ki in range(-1,2):
                    for kj in range(-1,2):
                        ii = i + ki
                        jj = j + kj
                        if ii >= 0 and jj >= 0 and ii < rows and jj < cols:
                            if caustics[ii,jj] != 0:
                                c += 1
                            else:
                                if magmap[ii,jj] > highestFound:
                                    x = ii
                                    y = jj
                if c < 3:
                    caustics[x,y] = 1






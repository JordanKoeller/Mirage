from astropy import units as u

cimport numpy as np
import numpy as np

from libc.math cimport sin, cos, atan, round


cpdef interpolate(object region, object two_points_list,sample_density):
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
		print(data.shape)
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

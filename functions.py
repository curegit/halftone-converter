from sys import float_info
from itertools import product
from math import floor, ceil, sqrt, sin, cos, acos, pi
from PIL import Image, ImageFilter, ImageCms
from cairo import ImageSurface, Context, Antialias, Filter, FORMAT_ARGB32, OPERATOR_SOURCE

def make_occupancy(pitch):
	def occupancy(radius):
		if radius < 0:
			return 0.0
		elif radius < pitch / 2:
			return pi * radius ** 2 / pitch ** 2
		elif radius < sqrt(2) / 2 * pitch:
			theta = acos(pitch / (2 * radius))
			return (radius / pitch) ** 2 * (pi - 4 * theta) + 2 * radius * sin(theta) / pitch
		else:
			return 1.0
	return occupancy

def bisection(f, x1, x2, eps):
	while True:
		x = (x1 + x2) / 2
		y = f(x)
		if abs(y) < eps:
			return x
		if f(x1) * y > 0:
			x1 = x
		else:
			x2 = x

def radius_table(pitch, depth):
	color = 0
	occupancy = 0.0
	while occupancy <= pi / 4:
		yield pitch * sqrt(occupancy / pi)
		color += 1
		occupancy = color / (depth - 1)
	r = pitch / 2
	rmax = sqrt(2) / 2 * pitch
	while color < depth - 1:
		f = make_occupancy(pitch)
		y = lambda x: f(x) - occupancy
		r = bisection(y, r, rmax, float_info.epsilon * 2)
		yield r
		color += 1
		occupancy = color / (depth - 1)
	yield rmax

def make_radius(pitch, depth):
	table = list(radius_table(pitch, depth))
	def radius(occupancy):
		if occupancy < 0:
			return 0.0
		elif occupancy >= depth:
			return sqrt(2) / 2 * pitch
		else:
			return table[occupancy]
	return radius

def make_transforms(pitch, angle, origin=(0.0, 0.0)):
	theta = angle / 180 * pi
	def transform(x, y):
		x -= origin[0]
		y -= origin[1]
		u = (x * cos(theta) - y * sin(theta)) / pitch
		v = (x * sin(theta) + y * cos(theta)) / pitch
		return (u, v)
	def inverse_transform(u, v):
		x = (u * cos(theta) + v * sin(theta)) * pitch
		y = (v * cos(theta) - u * sin(theta)) * pitch
		x += origin[0]
		y += origin[1]
		return (x, y)
	return (transform, inverse_transform)

def halftone_dots(image, pitch, angle, depth):
	center = (image.width / 2, image.height / 2)
	transform, inverse_transform = make_transforms(pitch, angle, center)
	xy_bounds = [(-pitch, -pitch), (image.width + pitch, -pitch), (image.width + pitch, image.height + pitch), (-pitch, image.height + pitch)]
	uv_bounds = [transform(*p) for p in xy_bounds]
	lower_u = min([u for u, v in uv_bounds])
	upper_u = max([u for u, v in uv_bounds])
	lower_v = min([v for u, v in uv_bounds])
	upper_v = max([v for u, v in uv_bounds])
	boundary = lambda u, v: lower_u <= u <= upper_u and lower_v <= v <= upper_v
	#blurred = image.filter(ImageFilter.GaussianBlur(pitch / 2))
	blurred = image.filter(ImageFilter.BoxBlur(pitch / 2))
	valid_uvs = [p for p in product(range(floor(lower_u), ceil(upper_u) + 1), range(floor(lower_v), ceil(upper_v) + 1)) if boundary(*p)]
	for u, v in valid_uvs:
		x, y = inverse_transform(u, v)
		color = blurred.getpixel((min(max(x, 0), image.width-1), min(max(y, 0), image.height-1)))
		yield (x, y, color)

def halftone_image(image, pitch, angle, scale):
	depth = 256
	width = image.width * scale
	height = image.height * scale
	foreground = (1.0, 1.0, 1.0, 1.0)
	background = (0.0, 0.0, 0.0, 1.0)
	radius = make_radius(pitch, depth)
	surface = ImageSurface(FORMAT_ARGB32, width, height)
	context = Context(surface)
	pattern = context.get_source()
	pattern.set_filter(Filter.BEST)
	#context.set_antialias(Antialias.BEST)
	context.set_antialias(Antialias.GRAY)
	context.set_operator(OPERATOR_SOURCE)
	context.set_source_rgba(*background)
	context.rectangle(0, 0, width, height)
	context.fill()
	context.set_source_rgba(*foreground)
	for x, y, color in halftone_dots(image, pitch, angle, depth):
		r = radius(color) * scale
		context.arc(x * scale, y * scale, r, 0, 2 * pi)
		context.fill()
	return Image.frombuffer("RGBA", (width, height), surface.get_data(), "raw", "RGBA", 0, 1).getchannel("G")

def halftone_cmyk_image(image, pitch, angles=(15, 75, 30, 45), scale=1.0):
	c, m, y, k = image.split()
	cyan = halftone_image(c, pitch, angles[0], scale)
	magenta = halftone_image(m, pitch, angles[1], scale)
	yellow = halftone_image(y, pitch, angles[2], scale)
	key = halftone_image(k, pitch, angles[3], scale)
	return Image.merge("CMYK", [cyan, magenta, yellow, key])

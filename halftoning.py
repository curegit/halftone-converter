from sys import float_info
from itertools import product
from argparse import ArgumentParser
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

def newton(f, df, x0, eps):
	while True:
		x1 = x0 - f(x0) / df(x0)
		if abs(x0 - x1) < eps:
			return x1
		x0 = x1

def radius_table(pitch, depth):
	color = 0
	occupancy = 0.0
	f = make_occupancy(pitch)
	while occupancy <= pi / 4:
		yield pitch * sqrt(occupancy / pi)
		color += 1
		occupancy = color / (depth - 1)
	r = 2 / pitch
	while color < depth - 1:
		y = lambda x: f(x) - occupancy
		dy = lambda x: 2 * x / pitch ** 2 * (pi - 4 * acos(pitch / (2 * x))) if x > pitch / 2 else 1
		r = newton(y, dy, r, float_info.epsilon * 4)
		yield r
		color += 1
		occupancy = color / (depth - 1)
	yield sqrt(2) / 2 * pitch

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
	return Image.frombuffer("RGBA", (width, height), surface.get_data(), "raw", "RGBA", 0, 1).getchannel("R")

'''
def halftone_cmyk_image(image, pitch, angles, scale):
	cyan, m, y, k = image.split()
	cyan_angle,
	c = halftone_image(cyan, pitch, cyan_angle, scale)

	return Image.merge("CMYK", [c, m, y, k])
'''

'''
# コマンドライン引数をパース
parser = arg.ArgumentParser(allow_abbrev=False, description="Halftoning ")
parser.add_argument("images", metavar="FILE", nargs="+", help="")
parser.add_argument("-d", "--directory", help="")
parser.add_argument("-rp", "--rgb-profile", help="")
parser.add_argument("-cp", "--cmyk-profile", help="")
parser.add_argument("-p", "--prefix", help="")
parser.add_argument("-s", "--suffix", help="")
parser.add_argument("-c", "--cmyk", action="store_true", help="")
parser.add_argument("-l", "--layers", action="store_true", help="")
parser.add_argument("-f", "--force", action="store_true", help="")
parser.add_argument("-e", "--enumerate", action="store_true", help="")
args = parser.parse_args()

# debug
print(vars(args))
print(args.directory)

# 引数のバリデーションと展開
directory = args.directory if args.direcotry != None else ""
rgb_profile = args.
cmyk_profile =
force = args.force

radius
pitch
c =
m =
y =
k =

# 出力ディレクトリの確認

#
for (i, image) in enumerate(images):
'''

for i in range(0, 3):
	img = Image.open("i2.jpg")
	cmyk = ImageCms.profileToProfile(img, 'sRGB Color Space Profile.icm', 'JapanColor2011Coated.icc', renderingIntent=i, outputMode='CMYK')

	rgb = ImageCms.profileToProfile(cmyk, 'JapanColor2011Coated.icc', 'sRGB Color Space Profile.icm', renderingIntent=3, outputMode='RGB')
	rgb.save(f"h-cmyk-{i}to3.png")

	c, m, y, k = cmyk.split()

	nc = halftone_image(c, 2, 15, scale=2)
	nm = halftone_image(m, 2, 75, scale=2)
	ny = halftone_image(y, 2, 35, scale=2)
	nk = halftone_image(k, 2, 45, scale=2)

	img = Image.merge("CMYK", [nc, nm, ny, nk])
	rgb = ImageCms.profileToProfile(img, 'JapanColor2011Coated.icc', 'sRGB Color Space Profile.icm', renderingIntent=3, outputMode='RGB')
	rgb.save(f"h-out{i}to3.png")

for i in range(0, 3):
	img = Image.open("D0iNh3hUcAAcXhM.jpg")
	cmyk = ImageCms.profileToProfile(img, 'sRGB Color Space Profile.icm', 'JapanColor2011Coated.icc', renderingIntent=i, outputMode='CMYK')

	rgb = ImageCms.profileToProfile(cmyk, 'JapanColor2011Coated.icc', 'sRGB Color Space Profile.icm', renderingIntent=3, outputMode='RGB')
	rgb.save(f"a-h-cmyk-{i}to3.png")

	c, m, y, k = cmyk.split()

	nc = halftone_image(c, 2, 15, scale=2)
	nm = halftone_image(m, 2, 75, scale=2)
	ny = halftone_image(y, 2, 35, scale=2)
	nk = halftone_image(k, 2, 45, scale=2)

	img = Image.merge("CMYK", [nc, nm, ny, nk])
	rgb = ImageCms.profileToProfile(img, 'JapanColor2011Coated.icc', 'sRGB Color Space Profile.icm', renderingIntent=3, outputMode='RGB')
	rgb.save(f"a-h-out{i}to3.png")

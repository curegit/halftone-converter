from sys import float_info
from io import BytesIO
from itertools import product
from math import floor, ceil, pow, sqrt, sin, cos, acos, pi
from numpy import frompyfunc, frombuffer, uint8, float64, rint
from PIL import Image, ImageFilter, ImageCms
from cairo import ImageSurface, Context, Antialias, Filter, FORMAT_ARGB32, OPERATOR_SOURCE

# ドット半径から占有率を返す関数を返す
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

# 2分法による求根
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

# 占有率からドット半径への変換テーブルをつくる
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

# 占有率からドット半径を返す関数を返す
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

# ピクセル空間から網点空間への変換と逆変換をする関数を返す
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

# シングルバンドの画像から網点の位置と階調のイテレータを返す
def halftone_dots(image, pitch, angle, blur):
	center = (image.width / 2, image.height / 2)
	transform, inverse_transform = make_transforms(pitch, angle, center)
	xy_bounds = [(-pitch, -pitch), (image.width + pitch, -pitch), (image.width + pitch, image.height + pitch), (-pitch, image.height + pitch)]
	uv_bounds = [transform(*p) for p in xy_bounds]
	lower_u = min([u for u, v in uv_bounds])
	upper_u = max([u for u, v in uv_bounds])
	lower_v = min([v for u, v in uv_bounds])
	upper_v = max([v for u, v in uv_bounds])
	boundary = lambda u, v: lower_u <= u <= upper_u and lower_v <= v <= upper_v
	blurred = image.filter(ImageFilter.GaussianBlur(pitch / 2)) if blur == "gaussian" else (image.filter(ImageFilter.BoxBlur(pitch / 2)) if blur == "box" else image)
	img_array = frombuffer(blurred.tobytes(), dtype=uint8).reshape(blurred.height, blurred.width)
	valid_uvs = [p for p in product(range(floor(lower_u), ceil(upper_u) + 1), range(floor(lower_v), ceil(upper_v) + 1)) if boundary(*p)]
	for u, v in valid_uvs:
		x, y = inverse_transform(u, v)
		color = img_array[min(max(round(y - 0.5), 0), image.height-1), min(max(round(x - 0.5), 0), image.width-1)]
		yield (x, y, color)

# シングルバンドの画像を網点化した画像を返す
def halftone_image(image, pitch, angle=45, scale=1.0, blur=None, keep_flag=False):
	width = round(image.width * scale)
	height = round(image.height * scale)
	if keep_flag:
		return image.resize((width, height), Image.LANCZOS)
	foreground = (1.0, 1.0, 1.0, 1.0)
	background = (0.0, 0.0, 0.0, 1.0)
	radius = make_radius(pitch, 256)
	surface = ImageSurface(FORMAT_ARGB32, width, height)
	context = Context(surface)
	pattern = context.get_source()
	pattern.set_filter(Filter.BEST)
	context.set_antialias(Antialias.GRAY)
	context.set_operator(OPERATOR_SOURCE)
	context.set_source_rgba(*background)
	context.rectangle(0, 0, width, height)
	context.fill()
	context.set_source_rgba(*foreground)
	for x, y, color in halftone_dots(image, pitch, angle, blur):
		r = radius(color) * scale
		context.arc(x * scale, y * scale, r, 0, 2 * pi)
		context.fill()
	return Image.frombuffer("RGBA", (width, height), surface.get_data(), "raw", "RGBA", 0, 1).getchannel("G")

# CMYKの画像を網点化した画像を返す
def halftone_cmyk_image(image, pitch, angles=(15, 75, 30, 45), scale=1.0, blur=None, keep_flags=(False, False, False, False)):
	c, m, y, k = image.split()
	cyan = halftone_image(c, pitch, angles[0], scale, blur, keep_flags[0])
	magenta = halftone_image(m, pitch, angles[1], scale, blur, keep_flags[1])
	yellow = halftone_image(y, pitch, angles[2], scale, blur, keep_flags[2])
	key = halftone_image(k, pitch, angles[3], scale, blur, keep_flags[3])
	return Image.merge("CMYK", [cyan, magenta, yellow, key])

# プロファイル変換のラッパー関数を返す
def make_profile_transform(profiles, modes, intent, prefer_embedded=True):
	transform = ImageCms.buildTransform(*profiles, *modes, intent)
	def profile_conversion(image):
		maybe_icc = image.info.get("icc_profile")
		if not prefer_embedded or maybe_icc == None:
			return ImageCms.applyTransform(image, transform)
		em_profile = ImageCms.ImageCmsProfile(BytesIO(maybe_icc))
		return ImageCms.profileToProfile(image, em_profile, profiles[1], renderingIntent=intent, outputMode=modes[1])
	return profile_conversion

# sRGBのガンマ変換
def gamma_forward(u):
	if u <= 0.0031308:
		return 12.92 * u
	else:
		return 1.055 * pow(u, 1 / 2.4) - 0.055

# sRGBの逆ガンマ変換
def gamma_reverse(u):
	if u <= 0.04045:
		return u / 12.92
	else:
		return pow((u + 0.055) / 1.055, 2.4)

# 近似によるsRGBとCMYKの色の変換関数を返す
def make_fake_conversions(k_threshold, gamma_correction):
	def rgb_2_cmyk(r, g, b):
		if gamma_correction:
			r, g, b = gamma_reverse(r), gamma_reverse(g), gamma_reverse(b)
		k = max(0, min(1, (min(1 - r, 1 - g, 1 - b) - k_threshold) / (1 - k_threshold)))
		c = 0.0 if abs(1 - k) <= float_info.epsilon * 4 else max(0, min(1, (1 - r - k) / (1 - k)))
		m = 0.0 if abs(1 - k) <= float_info.epsilon * 4 else max(0, min(1, (1 - g - k) / (1 - k)))
		y = 0.0 if abs(1 - k) <= float_info.epsilon * 4 else max(0, min(1, (1 - b - k) / (1 - k)))
		return c, m, y, k
	def cmyk_2_rgb(c, m, y, k):
		r = min(1, 1 - min(1, c * (1 - k) + k))
		g = min(1, 1 - min(1, m * (1 - k) + k))
		b = min(1, 1 - min(1, y * (1 - k) + k))
		if gamma_correction:
			r, g, b = gamma_forward(r), gamma_forward(g), gamma_forward(b)
		return r, g, b
	return (rgb_2_cmyk, cmyk_2_rgb)

# 近似によるsRGBとCMYKの画像の変換関数を返す
def make_fake_transforms(k_threshold=0.5, gamma_correction=True):
	rgb2cmyk, cmyk2rgb = make_fake_conversions(k_threshold, gamma_correction)
	rgb2cmyk_univ = frompyfunc(rgb2cmyk, 3, 4)
	cmyk2rgb_univ = frompyfunc(cmyk2rgb, 4, 3)
	def rgb_2_cmyk(image):
		r, g, b = image.split()
		r_array = frombuffer(r.tobytes(), dtype=uint8) / 255
		g_array = frombuffer(g.tobytes(), dtype=uint8) / 255
		b_array = frombuffer(b.tobytes(), dtype=uint8) / 255
		cmyk_array = rgb2cmyk_univ(r_array, g_array, b_array)
		c = Image.frombuffer("L", (image.width, image.height), rint(cmyk_array[0].astype(float64) * 255).astype(uint8), "raw", "L", 0, 1)
		m = Image.frombuffer("L", (image.width, image.height), rint(cmyk_array[1].astype(float64) * 255).astype(uint8), "raw", "L", 0, 1)
		y = Image.frombuffer("L", (image.width, image.height), rint(cmyk_array[2].astype(float64) * 255).astype(uint8), "raw", "L", 0, 1)
		k = Image.frombuffer("L", (image.width, image.height), rint(cmyk_array[3].astype(float64) * 255).astype(uint8), "raw", "L", 0, 1)
		return Image.merge("CMYK", [c, m, y, k])
	def cmyk_2_rgb(image):
		c, m, y, k = image.split()
		c_array = frombuffer(c.tobytes(), dtype=uint8) / 255
		m_array = frombuffer(m.tobytes(), dtype=uint8) / 255
		y_array = frombuffer(y.tobytes(), dtype=uint8) / 255
		k_array = frombuffer(k.tobytes(), dtype=uint8) / 255
		rgb_array = cmyk2rgb_univ(c_array, m_array, y_array, k_array)
		r = Image.frombuffer("L", (image.width, image.height), rint(rgb_array[0].astype(float64) * 255).astype(uint8), "raw", "L", 0, 1)
		g = Image.frombuffer("L", (image.width, image.height), rint(rgb_array[1].astype(float64) * 255).astype(uint8), "raw", "L", 0, 1)
		b = Image.frombuffer("L", (image.width, image.height), rint(rgb_array[2].astype(float64) * 255).astype(uint8), "raw", "L", 0, 1)
		return Image.merge("RGB", [r, g, b])
	return (rgb_2_cmyk, cmyk_2_rgb)

import numpy as np
from sys import float_info
from functools import cache, lru_cache
from math import floor, ceil, sqrt, sin, cos, acos, pi
from PIL import Image, ImageFilter, ImageOps
from PIL.Image import Resampling
from cairo import ImageSurface, Context, Antialias, Filter, Operator, Format

# ドット半径から着色部分の占有率を返す関数を返す
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

# 二分法による求根アルゴリズム
def bisection(f, x1, x2, eps=float_info.epsilon):
	while True:
		x = (x1 + x2) / 2
		if abs(x1 - x2) <= eps + eps * abs(x):
			return x
		y = f(x)
		if f(x1) * y > 0:
			x1 = x
		else:
			x2 = x

# 着色部分の占有率からドット半径への変換テーブルをつくる
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
		r = bisection(y, r, rmax)
		yield r
		color += 1
		occupancy = color / (depth - 1)
	yield rmax

# 着色部分の占有率からドット半径を返す関数を返す
@cache
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
		return u, v
	def inverse_transform(u, v):
		x = (u * cos(theta) + v * sin(theta)) * pitch
		y = (v * cos(theta) - u * sin(theta)) * pitch
		x += origin[0]
		y += origin[1]
		return x, y
	return transform, inverse_transform

# 画像端で座標を折り返す関数
def reflect(x, k):
	if x < 0:
		return reflect(-x, k)
	elif x <= k:
		return x
	elif x <= 2 * k:
		return 2 * k - x
	else:
		return reflect(x % (2 * k), k)

# 画像端で座標を折り返して画素値を取得する関数
def getpixel(image, x, y):
	i = reflect(x, image.width)
	j = reflect(y, image.height)
	return image.getpixel((floor(min(max(i, 0), image.width - 1)), floor(min(max(j, 0), image.height - 1))))

# 最近傍リサンプリング
def resample_nearest(image, x, y):
	return image.getpixel((floor(min(max(x, 0), image.width - 1)), floor(min(max(y, 0), image.height - 1)))) / 255

# 線形窓関数
def linear(x):
	if -1 < x < 1:
		return 1.0 - abs(x)
	else:
		return 0.0

# 線形リサンプリング関数
def resample_bilinear(image, x, y):
	i = np.arange(-1, 1) + round(x)
	j = np.arange(-1, 1) + round(y)
	a = i - x + 0.5
	b = j - y + 0.5
	w = np.array([[linear(t) * linear(s) for t in a] for s in b])
	p = np.array([[getpixel(image, t, s) for t in i] for s in j])
	return float(np.clip(np.sum(w * p) / 255, 0.0, 1.0))

# Lanczos 窓関数
@lru_cache(10000 ** 2)
def lanczos(x, n):
	return float(np.sinc(x) * np.sinc(x / n)) if abs(x) < n else 0.0

# Lanczos リサンプリング関数を返す
def make_lanczos_resampler(n=2):
	def resample_lanczos(image, x, y):
		i = np.arange(-n, n) + round(x)
		j = np.arange(-n, n) + round(y)
		a = i - x + 0.5
		b = j - y + 0.5
		w_tmp = np.array([[lanczos(t, n) * lanczos(s, n) for t in a] for s in b])
		w = w_tmp / w_tmp.sum()
		p = np.array([[getpixel(image, t, s) for t in i] for s in j])
		return float(np.clip(np.sum(w * p) / 255, 0.0, 1.0))
	return resample_lanczos

# Spline36 窓関数
@lru_cache(10000 ** 2)
def spline36(x):
	d = abs(x)
	if d <= 1.0:
		return (((247.0 * d - 453.0) * d - 3.0) * d + 209.0) / 209.0
	if d <= 2.0:
		return (((-114.0 * d + 612.0) * d - 1038.0) * d + 540.0) / 209.0
	if d <= 3.0:
		return (((19.0 * d - 159.0) * d + 434.0) * d - 384.0) / 209.0
	else:
		return 0.0

# Spline36 リサンプリング関数を返す
def resample_spline36(image, x, y):
	i = np.arange(-3, 3) + round(x)
	j = np.arange(-3, 3) + round(y)
	a = i - x + 0.5
	b = j - y + 0.5
	w = np.array([[spline36(t) * spline36(s) for t in a] for s in b])
	p = np.array([[getpixel(image, t, s) for t in i] for s in j])
	return float(np.clip(np.sum(w * p) / 255, 0.0, 1.0))

# シングルバンドの画像から網点の位置と階調のイテレータを返す
def halftone_dots(image, pitch, angle, blur, resampler="lanczos2", progress_callback=None):
	center = image.width / 2, image.height / 2
	transform, inverse_transform = make_transforms(pitch, angle, center)
	xy_bounds = [(-pitch, -pitch), (image.width + pitch, -pitch), (image.width + pitch, image.height + pitch), (-pitch, image.height + pitch)]
	uv_bounds = [transform(*p) for p in xy_bounds]
	lower_u = min([u for u, v in uv_bounds])
	upper_u = max([u for u, v in uv_bounds])
	lower_v = min([v for u, v in uv_bounds])
	upper_v = max([v for u, v in uv_bounds])
	boundary = lambda u, v: lower_u <= u <= upper_u and lower_v <= v <= upper_v
	if blur is not None:
		blur_name, blur_radius = blur
		if blur_radius is None:
			blur_radius = pitch / 2
		if blur_name == "gaussian":
			image = image.filter(ImageFilter.GaussianBlur(blur_radius))
		elif blur_name == "box":
			image = image.filter(ImageFilter.BoxBlur(blur_radius))
		else:
			raise ValueError()
	if resampler == "nearest":
		resample = resample_nearest
	elif resampler == "linear":
		resample = resample_bilinear
	elif resampler == "lanczos2":
		resample = make_lanczos_resampler(n=2)
	elif resampler == "lanczos3":
		resample = make_lanczos_resampler(n=3)
	elif resampler == "spline36":
		resample = resample_spline36
	else:
		raise ValueError()
	us = range(floor(lower_u), ceil(upper_u) + 1)
	vs = range(floor(lower_v), ceil(upper_v) + 1)
	count = len(us) * len(vs)
	i = 0
	for u in us:
		for v in vs:
			i += 1
			if boundary(u, v):
				x, y = inverse_transform(u, v)
				if -pitch < x < image.width + pitch and -pitch < y < image.height + pitch:
					color = resample(image, x, y)
					if progress_callback is not None:
						progress_callback(i / count)
					yield x, y, color
	if progress_callback is not None:
		progress_callback(1.0)

# シングルバンドの画像を網点化した画像を返す
def halftone_image(image, pitch, angle, scale, blur=None, resampler="lanczos2", keep_flag=False, progress_callback=None):
	width = round(image.width * scale)
	height = round(image.height * scale)
	if keep_flag:
		res = image.resize((width, height), Resampling.LANCZOS)
		if progress_callback is not None:
			progress_callback(1.0)
		return res
	foreground = (1.0, 1.0, 1.0, 1.0)
	background = (0.0, 0.0, 0.0, 1.0)
	radius = make_radius(pitch, 2 ** 16)
	surface = ImageSurface(Format.ARGB32, width, height)
	context = Context(surface)
	pattern = context.get_source()
	pattern.set_filter(Filter.BEST)
	context.set_antialias(Antialias.GRAY)
	context.set_operator(Operator.SOURCE)
	context.set_source_rgba(*background)
	context.rectangle(0, 0, width, height)
	context.fill()
	context.set_source_rgba(*foreground)
	for x, y, color in halftone_dots(image, pitch, angle, blur, resampler, progress_callback=progress_callback):
		r = radius(round(color * (2 ** 16 - 1))) * scale
		context.arc(x * scale, y * scale, r, 0, 2 * pi)
		context.fill()
	return Image.frombuffer("RGBA", (width, height), surface.get_data(), "raw", "RGBA", 0, 1).getchannel("G")

# グレースケールの画像を網点化した画像を返す
def halftone_grayscale_image(image, pitch, angle=45, scale=1.0, blur=None, resampler="lanczos2", keep_flag=False, preserve_profile=True, progress_callback=None):
	inverted = ImageOps.invert(image)
	halftone = halftone_image(inverted, pitch, angle, scale, blur, resampler, keep_flag, progress_callback=progress_callback)
	result = ImageOps.invert(halftone)
	if preserve_profile and image.info.get("icc_profile") is not None:
		result.info.update(icc_profile=image.info.get("icc_profile"))
	return result

# RGB の画像を網点化した画像を返す
def halftone_rgb_image(image, pitch, angles=(15, 75, 30), scale=1.0, blur=None, resampler="lanczos2", keep_flags=(False, False, False), preserve_profile=True, progress_callbacks=(None, None, None)):
	r, g, b = image.split()
	red = halftone_grayscale_image(r, pitch, angles[0], scale, blur, resampler, keep_flags[0], False, progress_callback=progress_callbacks[0])
	green = halftone_grayscale_image(g, pitch, angles[1], scale, blur, resampler, keep_flags[1], False, progress_callback=progress_callbacks[1])
	blue = halftone_grayscale_image(b, pitch, angles[2], scale, blur, resampler, keep_flags[2], False, progress_callback=progress_callbacks[2])
	halftone = Image.merge("RGB", [red, green, blue])
	if preserve_profile and image.info.get("icc_profile") is not None:
		halftone.info.update(icc_profile=image.info.get("icc_profile"))
	return halftone

# CMYK の画像を網点化した画像を返す
def halftone_cmyk_image(image, pitch, angles=(15, 75, 30, 45), scale=1.0, blur=None, resampler="lanczos2", keep_flags=(False, False, False, False), preserve_profile=True, progress_callbacks=(None, None, None, None)):
	c, m, y, k = image.split()
	cyan = halftone_image(c, pitch, angles[0], scale, blur, resampler, keep_flags[0], progress_callback=progress_callbacks[0])
	magenta = halftone_image(m, pitch, angles[1], scale, blur, resampler, keep_flags[1], progress_callback=progress_callbacks[1])
	yellow = halftone_image(y, pitch, angles[2], scale, blur, resampler, keep_flags[2], progress_callback=progress_callbacks[2])
	key = halftone_image(k, pitch, angles[3], scale, blur, resampler, keep_flags[3], progress_callback=progress_callbacks[3])
	halftone = Image.merge("CMYK", [cyan, magenta, yellow, key])
	if preserve_profile and image.info.get("icc_profile") is not None:
		halftone.info.update(icc_profile=image.info.get("icc_profile"))
	return halftone

from io import BytesIO
from PIL import Image, ImageCms
from numpy import frompyfunc, frombuffer, uint8, float64, rint

# プロファイル変換のラッパー関数を返す
def make_profile_transform(profiles, modes, intent, prefer_embedded=True):
	transform = ImageCms.buildTransform(*profiles, *modes, intent)
	def profile_conversion(image):
		maybe_icc = image.info.get("icc_profile")
		if not prefer_embedded or maybe_icc is None:
			return ImageCms.applyTransform(image, transform)
		em_profile = ImageCms.ImageCmsProfile(BytesIO(maybe_icc))
		return ImageCms.profileToProfile(image, em_profile, profiles[1], renderingIntent=intent, outputMode=modes[1])
	return profile_conversion

# sRGBのガンマ変換
def gamma_forward(u):
	if u <= 0.0031308:
		return 12.92 * u
	else:
		return 1.055 * u ** (1 / 2.4) - 0.055

# sRGBの逆ガンマ変換
def gamma_reverse(u):
	if u <= 0.04045:
		return u / 12.92
	else:
		return ((u + 0.055) / 1.055) ** 2.4

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
	return rgb_2_cmyk, cmyk_2_rgb

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
	return rgb_2_cmyk, cmyk_2_rgb

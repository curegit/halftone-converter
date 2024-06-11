import io
import numpy as np
from sys import float_info
from PIL import Image, ImageCms

# プロファイル変換の関数を返す
def make_profile_transform(profiles, modes, intent, prefer_embedded=True, *, lazy=True):
	def build():
		return ImageCms.buildTransform(*profiles, *modes, intent)
	transform = None if lazy else build()
	def profile_conversion(image):
		nonlocal transform
		maybe_icc = image.info.get("icc_profile")
		if not prefer_embedded or maybe_icc is None:
			if transform is None:
				transform = build()
			return ImageCms.applyTransform(image, transform)
		em_profile = ImageCms.ImageCmsProfile(io.BytesIO(maybe_icc))
		return ImageCms.profileToProfile(image, em_profile, profiles[1], renderingIntent=intent, outputMode=modes[1])
	return profile_conversion

# sRGB のガンマ変換
def gamma_forward(u):
	if u <= 0.0031308:
		return 12.92 * u
	else:
		return 1.055 * u ** (1 / 2.4) - 0.055

# sRGB の逆ガンマ変換
def gamma_reverse(u):
	if u <= 0.04045:
		return u / 12.92
	else:
		return ((u + 0.055) / 1.055) ** 2.4

# sRGB と CMYK 間の色の近似的な変換関数を返す
def make_fake_conversions(k_threshold, gamma_correction):
	def rgb_2_cmyk(r, g, b):
		if gamma_correction:
			r, g, b = gamma_reverse(r), gamma_reverse(g), gamma_reverse(b)
		k = max(0, min(1, (min(1 - r, 1 - g, 1 - b) - k_threshold) / (1 - k_threshold)))
		c = 0.0 if abs(1 - k) <= float_info.epsilon else max(0, min(1, (1 - r - k) / (1 - k)))
		m = 0.0 if abs(1 - k) <= float_info.epsilon else max(0, min(1, (1 - g - k) / (1 - k)))
		y = 0.0 if abs(1 - k) <= float_info.epsilon else max(0, min(1, (1 - b - k) / (1 - k)))
		return c, m, y, k
	def cmyk_2_rgb(c, m, y, k):
		r = min(1, 1 - min(1, c * (1 - k) + k))
		g = min(1, 1 - min(1, m * (1 - k) + k))
		b = min(1, 1 - min(1, y * (1 - k) + k))
		if gamma_correction:
			r, g, b = gamma_forward(r), gamma_forward(g), gamma_forward(b)
		return r, g, b
	return rgb_2_cmyk, cmyk_2_rgb

# sRGB と CMYK 間の画像の近似的な変換関数を返す
def make_fake_transforms(k_threshold=0.5, gamma_correction=True):
	rgb2cmyk, cmyk2rgb = make_fake_conversions(k_threshold, gamma_correction)
	rgb2cmyk_univ = np.frompyfunc(rgb2cmyk, 3, 4)
	cmyk2rgb_univ = np.frompyfunc(cmyk2rgb, 4, 3)
	def rgb_2_cmyk(image):
		r, g, b = image.split()
		r_array = np.frombuffer(r.tobytes(), dtype=np.uint8) / 255
		g_array = np.frombuffer(g.tobytes(), dtype=np.uint8) / 255
		b_array = np.frombuffer(b.tobytes(), dtype=np.uint8) / 255
		cmyk_array = rgb2cmyk_univ(r_array, g_array, b_array)
		c = Image.frombuffer("L", (image.width, image.height), np.rint(cmyk_array[0].astype(np.float64) * 255).astype(np.uint8), "raw", "L", 0, 1)
		m = Image.frombuffer("L", (image.width, image.height), np.rint(cmyk_array[1].astype(np.float64) * 255).astype(np.uint8), "raw", "L", 0, 1)
		y = Image.frombuffer("L", (image.width, image.height), np.rint(cmyk_array[2].astype(np.float64) * 255).astype(np.uint8), "raw", "L", 0, 1)
		k = Image.frombuffer("L", (image.width, image.height), np.rint(cmyk_array[3].astype(np.float64) * 255).astype(np.uint8), "raw", "L", 0, 1)
		return Image.merge("CMYK", [c, m, y, k])
	def cmyk_2_rgb(image):
		c, m, y, k = image.split()
		c_array = np.frombuffer(c.tobytes(), dtype=np.uint8) / 255
		m_array = np.frombuffer(m.tobytes(), dtype=np.uint8) / 255
		y_array = np.frombuffer(y.tobytes(), dtype=np.uint8) / 255
		k_array = np.frombuffer(k.tobytes(), dtype=np.uint8) / 255
		rgb_array = cmyk2rgb_univ(c_array, m_array, y_array, k_array)
		r = Image.frombuffer("L", (image.width, image.height), np.rint(rgb_array[0].astype(np.float64) * 255).astype(np.uint8), "raw", "L", 0, 1)
		g = Image.frombuffer("L", (image.width, image.height), np.rint(rgb_array[1].astype(np.float64) * 255).astype(np.uint8), "raw", "L", 0, 1)
		b = Image.frombuffer("L", (image.width, image.height), np.rint(rgb_array[2].astype(np.float64) * 255).astype(np.uint8), "raw", "L", 0, 1)
		return Image.merge("RGB", [r, g, b])
	return rgb_2_cmyk, cmyk_2_rgb

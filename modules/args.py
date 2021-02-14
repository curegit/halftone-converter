from sys import float_info
from os.path import basename
from PIL import ImageCms

# 正の実数を受け入れる変換関数
def positive(str):
	value = float(str)
	if value >= float_info.epsilon:
		return value
	else:
		raise ValueError()

# 0-1 の実数を受け入れる変換関数
def rate(str):
	value = float(str)
	if 0 <= value <= 1:
		return value
	else:
		raise ValueError()

# 非空列を受け入れる変換関数
def nonempty(str):
	if str:
		return str
	else:
		raise ValueError()

# ファイル名の一部を受け入れる変換関数
def filenameseg(str):
	if str == basename(str):
		return str
	else:
		raise ValueError()

# 大小文字を区別しないラベルマッチのための変換関数
def choice(label):
	return str.lower(label)

# ラベルを受け入れてレンダリングインテントを表す整数を返す
def intent(label):
	label = str.lower(label)
	if label == "per":
		return ImageCms.INTENT_PERCEPTUAL
	if label == "sat":
		return ImageCms.INTENT_SATURATION
	if label == "rel":
		return ImageCms.INTENT_RELATIVE_COLORIMETRIC
	if label == "abs":
		return ImageCms.INTENT_ABSOLUTE_COLORIMETRIC
	if 0 <= int(label) <= 3:
		return int(label)
	else:
		raise ValueError()

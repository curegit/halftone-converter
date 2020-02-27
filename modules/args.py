from os.path import basename

# 正整数を受け入れる変換関数
def natural(str):
	value = int(str)
	if value > 0:
		return value
	else:
		raise ValueError()

# 正の実数を受け入れる変換関数
def positive(str):
	value = float(str)
	if value > 0:
		return value
	else:
		raise ValueError()

# ファイル名を受け入れる変換関数
def filename(str):
	if str == basename(str):
		return str
	else:
		raise ValueError()

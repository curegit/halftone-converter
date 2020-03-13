from argparse import ArgumentParser
from PIL import Image, ImageCms
from modules.args import positive, rate, filename, choice, intent
from modules.util import eprint, mkdirp, filepath, filerelpath, purefilename, altfilepath
from modules.color import make_profile_transform, make_fake_transforms
from modules.core import halftone_grayscale_image, halftone_rgb_image, halftone_cmyk_image

# コマンドライン引数をパース
parser = ArgumentParser(allow_abbrev=False, description="Halftoning")
parser.add_argument("images", metavar="FILE", nargs="+", help="")
parser.add_argument("-q", "--quiet", action="store_true", help="Interpret FILE values as glob patterns")
parser.add_argument("-g", "--glob", action="store_true", help="Interpret FILE values as glob patterns")
parser.add_argument("-f", "--force", action="store_true", help="")
parser.add_argument("-d", "--directory", metavar="DIR", default=".", help="")
parser.add_argument("-P", "--prefix", type=filename, default="", help="")
parser.add_argument("-s", "--suffix", type=filename, default="-halftone", help="")
parser.add_argument("-e", "--enumerate", metavar="START", type=int, nargs="?", const=1, help="")

parser.add_argument("-p", "--pitch", metavar="PX", type=positive, default=2, help="")
parser.add_argument("-x", "--scale", metavar="PX", type=positive, default=1, help="")
parser.add_argument("-b", "--blur", type=choice, choices=["none", "box", "gaussian"], default="gaussian", help="")

parser.add_argument("-m", "--mode", type=choice, choices=["auto", "gray", "rgb", "cmyk"], default="auto", help="")

parser.add_argument("-o", "--output", type=choice, choices=["auto", "gray", "rgb", "cmyk"], default="auto", help="")

parser.add_argument("-t", "--tiff", action="store_true", help="")



parser.add_argument("-G", "--gray-profile", help="")
parser.add_argument("-R", "--rgb-profile", help="")
parser.add_argument("-C", "--cmyk-profile", help="")
parser.add_argument("-A", "--input-gray-profile", help="")
parser.add_argument("-I", "--input-rgb-profile", help="")
parser.add_argument("-K", "--input-cmyk-profile", help="")
parser.add_argument("-E", "--ignore-embedded-profile", action="store_true", help="")
parser.add_argument("-W", "--wide", action="store_true", help="")
parser.add_argument("-N", "--naive", action="store_true", help="")
parser.add_argument("--black-start", type=rate, help="")
parser.add_argument("--gamma", action="store_true", help="")
parser.add_argument("-D", "--discard-profile", action="store_true", help="")

parser.add_argument("-L", "--gray-intent", type=intent, choices=["per", "sat", "rel", "abs", 0, 1, 2, 3], default="rel", help="")
parser.add_argument("-AA", "--rgb-intent", type=intent, choices=["per", "sat", "rel", "abs", 0, 1, 2, 3], default="rel", help="")
parser.add_argument("-B", "--cmyk-intent", type=intent, choices=["per", "sat", "rel", "abs", 0, 1, 2, 3], default="rel", help="")

parser.add_argument("--angle", "--gray-angle", metavar="DEG", dest="gray_angle", type=float, default=45, help="")
parser.add_argument("--Angles", "--rgb-angles", metavar="DEG", dest="rgb_angles", type=float, nargs=3, default=(15, 75, 30), help="")
parser.add_argument("--angles", "--cmyk-angles", metavar="DEG", dest="cmyk_angles", type=float, nargs=4, default=(15, 75, 30, 45), help="")
parser.add_argument("--keep-red", action="store_true", help="")
parser.add_argument("--keep-green", action="store_true", help="")
parser.add_argument("--keep-blue", action="store_true", help="")
parser.add_argument("--keep-cyan", action="store_true", help="")
parser.add_argument("--keep-magenta", action="store_true", help="")
parser.add_argument("--keep-yellow", action="store_true", help="")
parser.add_argument("--keep-key", "--keep-black", action="store_true", help="")
args = parser.parse_args()

#
cmyk_keep_flags = (args.keep_cyan, args.keep_magenta, args.keep_yellow, args.keep_key)
rgb_keep_flags = (args.keep_red, args.keep_green, args.keep_blue)

# ICC プロファイルを
if args.gray_profile is None:
	gray_profile = filerelpath("profiles/openicc/GrayCIE.icc")
else:
	gray_profile = ImageCms.getOpenProfile(args.gray_profile)
if args.input_gray_profile is None:
	in_gray_profile = filerelpath("profiles/openicc/GrayCIE.icc")
else:
	in_gray_profile = ImageCms.getOpenProfile(args.input_gray_profile)
if args.rgb_profile is None:
	rgb_profile = filerelpath("profiles/chromasoft/WideGamutD65.icc") if args.wide else filerelpath("profiles/openicc/sRGB.icc")
else:
	rgb_profile = ImageCms.getOpenProfile(args.rgb_profile)
if args.input_rgb_profile is None:
	in_rgb_profile = filerelpath("profiles/openicc/sRGB.icc")
else:
	in_rgb_profile = ImageCms.getOpenProfile(args.input_rgb_profile)
if args.cmyk_profile is None:
	cmyk_profile = filerelpath("profiles/colormanagement/ISOCoatedV2.icc")
else:
	cmyk_profile = ImageCms.getOpenProfile(args.cmyk_profile)
if args.input_cmyk_profile is None:
	in_cmyk_profile = filerelpath("profiles/colormanagement/ISOCoatedV2.icc")
else:
	in_cmyk_profile = ImageCms.getOpenProfile(args.input_cmyk_profile)

#
if args.naive:
	rgb_cmyk, cmyk_rgb = in_rgb_cmyk, in_cmyk_rgb = make_fake_transforms(args.black_start, args.gamma_correction)
	gray_rgb = in_gray_rgb = lambda img: img.convert("RGB")
	rgb_gray = in_rgb_gray = lambda img: img.convert("L")
	gray_cmyk = in_gray_cmyk = lambda img: rgb_cmyk(gray_rgb(img))
	cmyk_gray = in_cmyk_gray = lambda img: rgb_gray(cmyk_rgb(img))
else:
	rgb_cmyk = make_profile_transform((rgb_profile, cmyk_profile), ("RGB", "CMYK"), args.cmyk_intent, not args.ignore_embedded_profile)
	cmyk_rgb = make_profile_transform((cmyk_profile, rgb_profile), ("CMYK", "RGB"), args.rgb_intent, not args.ignore_embedded_profile)
	in_rgb_cmyk = make_profile_transform((in_rgb_profile, cmyk_profile), ("RGB", "CMYK"), args.cmyk_intent, not args.ignore_embedded_profile)
	in_cmyk_rgb = make_profile_transform((in_cmyk_profile, rgb_profile), ("CMYK", "RGB"), args.rgb_intent, not args.ignore_embedded_profile)
	gray_rgb = make_profile_transform((gray_profile, rgb_profile), ("L", "RGB"), args.rgb_intent, not args.ignore_embedded_profile)
	rgb_gray = make_profile_transform((rgb_profile, gray_profile), ("RGB", "L"), args.gray_intent, not args.ignore_embedded_profile)
	in_gray_rgb = make_profile_transform((in_gray_profile, rgb_profile), ("L", "RGB"), args.rgb_intent, not args.ignore_embedded_profile)
	in_rgb_gray = make_profile_transform((in_rgb_profile, gray_profile), ("RGB", "L"), args.gray_intent, not args.ignore_embedded_profile)
	gray_cmyk = make_profile_transform((gray_profile, cmyk_profile), ("L", "CMYK"), args.cmyk_intent, not args.ignore_embedded_profile)
	cmyk_gray = make_profile_transform((cmyk_profile, gray_profile), ("CMYK", "L"), args.gray_intent, not args.ignore_embedded_profile)
	in_gray_cmyk = make_profile_transform((in_gray_profile, cmyk_profile), ("L", "CMYK"), args.cmyk_intent, not args.ignore_embedded_profile)
	in_cmyk_gray = make_profile_transform((in_cmyk_profile, gray_profile), ("CMYK", "L"), args.gray_intent, not args.ignore_embedded_profile)

# 出力ディレクトリを作る
mkdirp(args.directory)

# 処理対象ファイルをリスティング
if args.glob:
	input_images = []
	for i in args.images:
		input_images += glob(i, recursive=True)
else:
	input_images = args.images

# 処理のメインループ
n = len(input_images)
for i, f in enumerate(input_images):
	try:
		# 画像を開く
		img = Image.open(f)
		if img.mode == "LA":
			img = img.convert("L")
		elif img.mode == "RGBA":
			img = img.convert("RGB")
		if not img.mode in ["L", "RGB", "CMYK"]:
			eprint("err") # TODO
		# ハーフトーンの色空間へ変換する
		if img.mode == "L":
			if args.mode == "gray":
				target, same = img, True
			elif args.mode == "rgb":
				target, same = in_gray_rgb(img), False
			elif args.mode == "cmyk":
				target, same = in_gray_cmyk(img), False
			else:
				target, same = img, True
		elif img.mode == "RGB":
			if args.mode == "gray":
				target, same = in_rgb_gray(img), False
			elif args.mode == "rgb":
				target, same = img, True
			elif args.mode == "cmyk":
				target, same = in_rgb_cmyk(img), False
			else:
				target, same = in_rgb_cmyk(img), False
		elif img.mode == "CMYK":
			if args.mode == "gray":
				target, same = in_cmyk_gray(img), False
			elif args.mode == "rgb":
				target, same = in_cmyk_rgb(img), False
			elif args.mode == "cmyk":
				target, same = img, True
			else:
				target, same = img, True
		# ハーフトーン化
		if target.mode == "L":
			halftone = halftone_grayscale_image(target, args.pitch, args.gray_angle, args.scale, args.blur, gray_keep_flag)
		elif target.mode == "RGB":
			halftone = halftone_rgb_image(target, args.pitch, args.rgb_angles, args.scale, args.blur, rgb_keep_flags)
		elif target.mode == "CMYK":
			halftone = halftone_cmyk_image(target, args.pitch, args.cmyk_angles, args.scale, args.blur, cmyk_keep_flags)
		# 目的の出力モードへ変換する
		if halftone.mode == "L":
			if args.output == "gray":
				complete = halftone
			elif args.output == "rgb":
				complete = in_gray_rgb(halftone) if same else gray_rgb(halftone)
			elif args.output == "cmyk":
				complete = in_gray_cmyk(halftone) if same else gray_cmyk(halftone)
			else:
				complete = halftone
		elif halftone.mode == "RGB":
			if args.output == "gray":
				complete = in_rgb_gray(halftone) if same else rgb_gray(halftone)
			elif args.output == "rgb":
				complete = halftone
			elif args.output == "cmyk":
				complete = in_rgb_cmyk(halftone) if same else rgb_cmyk(halftone)
			else:
				complete = halftone
		elif halftone.mode == "CMYK":
			if args.output == "gray":
				complete = in_cmyk_gray(halftone) if same else cmyk_gray(halftone)
			elif args.output == "rgb":
				complete = in_cmyk_rgb(halftone) if same else cmyk_rgb(halftone)
			elif args.output == "cmyk":
				complete = halftone
			else:
				complete = in_cmyk_rgb(halftone) if same else cmyk_rgb(halftone)
		# 必要なら ICC プロファイルを廃棄する
		if args.discard_profile:
			if complete.info.get("icc_profile"):
				complete.info.pop("icc_profile")
		# ファイルへ保存する
		if args.enumerate is None:
			name = args.prefix + purefilename(f) + args.suffix
		else:
			name = args.prefix + f"{arg.enumerate + i}" + args.suffix
		if complete.mode == "CMYK" or args.tiff:
			path = filepath(args.directory, name, "tiff")
		else:
			path = filepath(args.directory, name, "png")
		if not args.force:
			path = altfilepath(path)
		complete.save(path)
	# エラーを報告する
	except Exception as e:
		eprint(f"{i + 1} / {n} Error: {f}")
		eprint(e)
	# 成功を報告する
	else:
		print(f"{i + 1} / {n} Done: {path}")

from argparse import ArgumentParser
from PIL import Image, ImageCms
from modules.args import positive, rate, filename, choice, intent
from modules.util import eprint, mkdirp, filepath, filerelpath, purefilename, altfilepath
from modules.color import make_profile_transform, make_fake_transforms
from modules.core import halftone_grayscale_image, halftone_rgb_image, halftone_cmyk_image

# コマンドライン引数をパース
parser = ArgumentParser(allow_abbrev=False, description="Halftone Converter: an image converter to generate halftones.")
parser.add_argument("images", metavar="FILE", nargs="+", help="describe input image files")
parser.add_argument("-q", "--quiet", action="store_true", help="suppress non-error messages")
parser.add_argument("-g", "--glob", action="store_true", help="interpret FILE values as glob patterns")
parser.add_argument("-f", "--force", action="store_true", help="overwrite existing files by outputs")
parser.add_argument("-d", "--directory", metavar="DIR", default=".", help="save output images in DIR directory")
parser.add_argument("-P", "--prefix", type=filename, default="", help="specify a prefix string of output filenames")
parser.add_argument("-S", "--suffix", type=filename, default="-halftone", help="specify a suffix string of output filenames")
parser.add_argument("-e", "--enumerate", metavar="START", type=int, nargs="?", const=1, help="use consecutive numbers as output filenames")
parser.add_argument("-p", "--pitch", "--interval", metavar="PX", type=positive, default=4, help="arrange halftone dots at intervals of PX pixels")
parser.add_argument("-x", "-s", "--scale", type=positive, default=1, help="the scale factor of output images to input images")
parser.add_argument("-b", "--blur", type=choice, choices=["none", "box", "gaussian"], default="gaussian", help="blur type to calculate the mean of pixels")
parser.add_argument("-A", "--angle", "--gray-angle", metavar="DEG", dest="gray_angle", type=float, default=45, help="arrange dots by DEG degrees in Gray channel")
parser.add_argument("-t", "--Angles", "--rgb-angles", metavar="DEG", dest="rgb_angles", type=float, nargs=3, default=(15, 75, 30), help="arrange dots by DEG degrees in each RGB channels")
parser.add_argument("-a", "--angles", "--cmyk-angles", metavar="DEG", dest="cmyk_angles", type=float, nargs=4, default=(15, 75, 30, 45), help="arrange dots by DEG degrees in each CMYK channels")
parser.add_argument("-m", "--mode", type=choice, choices=["auto", "gray", "rgb", "cmyk"], default="auto", help="color space type to generate halftones")
parser.add_argument("-o", "--output", type=choice, choices=["auto", "gray", "rgb", "cmyk"], default="auto", help="color space type to save output images")
parser.add_argument("-T", "--tiff", "--out-tiff", action="store_true", help="save TIFF images instead of PNG images")
parser.add_argument("-G", "--input-gray-profile", metavar="GRAY_ICC_FILE", help="specify ICC profile for input Gray images")
parser.add_argument("-I", "--input-rgb-profile", metavar="RGB_ICC_FILE", help="specify ICC profile for input RGB images")
parser.add_argument("-M", "--input-cmyk-profile", metavar="CMYK_ICC_FILE", help="specify ICC profile for input CMYK images")
parser.add_argument("-L", "--gray-profile", metavar="GRAY_ICC_FILE", help="specify ICC profile for transform to Gray images")
parser.add_argument("-l", "--gray-intent", type=intent, choices=["per", "sat", "rel", "abs", 0, 1, 2, 3], default=1, help="rendering intent for transform to Gray images")
parser.add_argument("-R", "--rgb-profile", metavar="RGB_ICC_FILE", help="specify ICC profile for transform to RGB images")
parser.add_argument("-r", "--rgb-intent", type=intent, choices=["per", "sat", "rel", "abs", 0, 1, 2, 3], default=1, help="rendering intent for transform to RGB images")
parser.add_argument("-C", "--cmyk-profile", metavar="CMYK_ICC_FILE", help="specify ICC profile for transform to CMYK images")
parser.add_argument("-c", "--cmyk-intent", type=intent, choices=["per", "sat", "rel", "abs", 0, 1, 2, 3], default=1, help="rendering intent for transform to CMYK images")
parser.add_argument("--ignore", "--ignore-embedded-profile", action="store_true", help="don't use ICC profiles embedded in input images")
parser.add_argument("--discard", "--discard-profile", action="store_true", help="don't embed ICC profiles in output images")
parser.add_argument("--naive", "--naive-transform", action="store_true", help="use approximate conversion algorithm (naive transform) instead of ICC-based transform")
parser.add_argument("--gamma-correction", action="store_true", help="apply gamma correction for RGB-CMYK conversion when the naive transform is used")
parser.add_argument("--key-from", metavar="RATE", type=rate, default=0.5, help="black ingredient threshold within 0.0-1.0 for RGB-CMYK conversion")
parser.add_argument("--keep-red", action="store_true", help="don't convert R channels to halftones")
parser.add_argument("--keep-green", action="store_true", help="don't convert G channels to halftones")
parser.add_argument("--keep-blue", action="store_true", help="don't convert B channels to halftones")
parser.add_argument("--keep-cyan", action="store_true", help="don't convert C channels to halftones")
parser.add_argument("--keep-magenta", action="store_true", help="don't convert M channels to halftones")
parser.add_argument("--keep-yellow", action="store_true", help="don't convert Y channels to halftones")
parser.add_argument("--keep-key", action="store_true", help="don't convert K channels to halftones")
args = parser.parse_args()

# ICC プロファイルを読み込む
if args.gray_profile is None:
	gray_profile = ImageCms.getOpenProfile(filerelpath("profiles/sGray.icc"))
else:
	gray_profile = ImageCms.getOpenProfile(args.gray_profile)
if args.input_gray_profile is None:
	in_gray_profile = ImageCms.getOpenProfile(filerelpath("profiles/sGray.icc"))
else:
	in_gray_profile = ImageCms.getOpenProfile(args.input_gray_profile)
if args.rgb_profile is None:
	rgb_profile =  ImageCms.getOpenProfile(filerelpath("profiles/sRGB.icc"))
else:
	rgb_profile = ImageCms.getOpenProfile(args.rgb_profile)
if args.input_rgb_profile is None:
	in_rgb_profile = ImageCms.getOpenProfile(filerelpath("profiles/sRGB.icc"))
else:
	in_rgb_profile = ImageCms.getOpenProfile(args.input_rgb_profile)
if args.cmyk_profile is None:
	cmyk_profile = ImageCms.getOpenProfile(filerelpath("profiles/SWOP.icc"))
else:
	cmyk_profile = ImageCms.getOpenProfile(args.cmyk_profile)
if args.input_cmyk_profile is None:
	in_cmyk_profile = ImageCms.getOpenProfile(filerelpath("profiles/SWOP.icc"))
else:
	in_cmyk_profile = ImageCms.getOpenProfile(args.input_cmyk_profile)

# 色空間を変換する関数を作成する
if args.naive:
	rgb_cmyk, cmyk_rgb = in_rgb_cmyk, in_cmyk_rgb = make_fake_transforms(args.key_from, args.gamma_correction)
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
			halftone = halftone_grayscale_image(target, args.pitch, args.gray_angle, args.scale, args.blur)
		elif target.mode == "RGB":
			halftone = halftone_rgb_image(target, args.pitch, args.rgb_angles, args.scale, args.blur, (args.keep_red, args.keep_green, args.keep_blue))
		elif target.mode == "CMYK":
			halftone = halftone_cmyk_image(target, args.pitch, args.cmyk_angles, args.scale, args.blur, (args.keep_cyan, args.keep_magenta, args.keep_yellow, args.keep_key))
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
		if not args.quiet:
			print(f"{i + 1} / {n} Done: {path}")
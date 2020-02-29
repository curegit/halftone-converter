from argparse import ArgumentParser
from PIL import Image, ImageCms
from modules.args import natural, positive, filename
from modules.util import eprint, mkdirp, filepath, filerelpath, altfilepath
from modules.color import make_profile_transform, make_fake_transforms
from modules.core import halftone_grayscale_image, halftone_cmyk_image, halftone_rgb_image

# コマンドライン引数をパース
parser = ArgumentParser(allow_abbrev=False, description="Halftoning")
parser.add_argument("images", metavar="FILE", nargs="+", help="")
parser.add_argument("-d", "--directory", metavar="DIR", default=".", help="")
parser.add_argument("-f", "--force", action="store_true", help="")
parser.add_argument("-P", "--prefix", default="", help="")
parser.add_argument("-S", "--suffix", default="halftone", help="")
parser.add_argument("-E", "--enumerate", metavar="START", type=int, nargs="?", const=1, help="")



parser.add_argument("--gray", action="store_true", help="")
parser.add_argument("--cmyk", action="store_true", help="")
parser.add_argument("--rgb", action="store_true", help="")

parser.add_argument("--", action="store_true", help="")
parser.add_argument("--tiff", action="store_true", help="")

parser.add_argument("-p", "--pitch", metavar="PX", type=positive, help="")
parser.add_argument("-s", "--scale", metavar="PX", type=positive, help="")
parser.add_argument("-b", "--blur", choices=["none", "box", "gaussian"], default="gaussian", help="")
parser.add_argument("--channels", action="store_true", help="")
parser.add_argument("--split", action="store_true", help="")
parser.add_argument("-I", "--input-profile", help="")
parser.add_argument("-C", "--cmyk-profile", help="")
parser.add_argument("-R", "--rgb-profile", help="")
#parser.add_argument("-O", "--output-profile", help="")
parser.add_argument("-G", "--ignore-embedded-profile", action="store_true", help="")
parser.add_argument("-F", "--fake", action="store_true", help="")
cmyk_initent = 1
rgb_intent = 3

gray_group = parser.add_argument_group("gray mode")
gray_group.add_argument("--angle", "--gray-angle", metavar="DEG", type=float, help="")
cmyk_group = parser.add_argument_group("cmyk mode")
cmyk_group.add_argument("--angles", "--cmyk-angles", metavar="DEG", type=float, nargs=4, help="")
cmyk_group.add_argument("--keep-cyan", action="store_true", help="")
cmyk_group.add_argument("--keep-magenta", action="store_true", help="")
cmyk_group.add_argument("--keep-yellow", action="store_true", help="")
cmyk_group.add_argument("--keep-key", "--keep-black", action="store_true", help="")
rgb_group = parser.add_argument_group("rgb mode")
rgb_group.add_argument("--rgb-angles", metavar="DEG", type=float, nargs=3, help="")
rgb_group.add_argument("--keep-red", action="store_true", help="")
rgb_group.add_argument("--keep-green", action="store_true", help="")
rgb_group.add_argument("--keep-blue", action="store_true", help="")
args = parser.parse_args()


cmyk_keep_flags = (args.keep_cyan, args.keep_magenta, args.keep_yellow, args.keep_key)
rgb_keep_flags = (args.keep_red, args.keep_green, args.keep_blue)

in_profile = ImageCms.createProfile("sRGB")
cmyk_profile = "profile/JapanColor2011Coated.icc"
out_profile = in_profile

ignore_profile = args.ignore_embedded_profile

pt_cmyk = make_profile_transform((in_profile, cmyk_profile), ("RGB", "CMYK"), cmyk_initent, not ignore_profile)
pt_rgb = make_profile_transform((cmyk_profile, out_profile), ("CMYK", "RGB"), rgb_intent, False)

# 出力ディレクトリを作る
mkdirp(args.directory)

# Glob
if args.glob:
	input_images = []
	for i in args.images:
		input_images += glob(i, recursive=True)
else:
	input_images = args.images

# メインループ
n = len(input_images)
for i, f in enumerate(input_images, 1):
	try:
		#
		img = Image.open(f)
		if img.mode == "L":
			target = img
		elif img.mode == "CMYK":
			if args.mode == "gray":
				target = img.convert("L")
			elif args.mode == "cmyk":
				target = img
			elif args.mode == "rgb":
				target = img.


		elif img.mode == "RGB" or img.mode == "RGBA":
			if img.mode == "RGBA":
				img = img.convert("RGB")
			if args.mode == "gray":
				target = img.convert("L")
			elif args.mode == "cmyk":

			elif args.mode == "rgb":
				target = img
		else:
			raise ()


			cmyk = pt_cmyk(img)

			halftone = halftone_cmyk_image(cmyk, args.pitch, angles=args.cmyk_angles, scale=args.scale, blur=args.blur, keep_flags=cmyk_keep_flags)
			if out_cmyk:

			else:
				pt_rgb(halftone).save(f"{i}.png")
		else:
			pass


		# ハーフトーン化
		if target.mode == "L":
			halftone = halftone_grayscale_image(target, args.pitch)
		elif target.mode == "CMYK":
			halftone = halftone_cmyk_image(target)
		elif target.mode == "RGB":
			halftone = halftone_rgb_image(target)
		# 目的の出力モードへ変換する
		if halftone.mode == "L":

		elif halftone.mode == "CMYK":

		elif halftone.mode == "RGB":

		# ファイルへ保存する
		if complete.mode == "L":

		elif complete.mode == "CMYK":
			complete.save(f"{}.tiff")
		elif complete.mode == "RGB":




		print(f"{i} / {n} Done")
	except Exception as e:
		eprint(f"{i} / {n} Error")
		eprint(e)

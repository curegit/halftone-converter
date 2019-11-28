from os.path import basename
from argparse import ArgumentParser
from PIL import Image, ImageCms
from modules.util import mkdirp, filepath, filerelpath, altfilepath
from modules.color import make_profile_transform, make_fake_transforms
from modules.core import halftone_grayscale_image, halftone_cmyk_image, halftone_rgb_image

# コマンドライン引数をパース
parser = ArgumentParser(allow_abbrev=False, description="Halftoning ")
parser.add_argument("images", metavar="FILE", nargs="+", help="")

parser.add_argument("-d", "--directory", metavar="DEST", help="")
parser.add_argument("-f", "--force", action="store_true", help="")
parser.add_argument("-p", "--prefix", help="")
parser.add_argument("-s", "--suffix", help="")
parser.add_argument("-e", "--enumerate", metavar="START", type=int, nargs="?", const=1, help="")



parser.add_argument("-c", "--cmyk", action="store_true", help="")
parser.add_argument("--bands", action="store_true", help="")
parser.add_argument("-x", "--pitch", metavar="PX", type=float, help="")


parser.add_argument("-ig", "--ignore-embedded-profile", action="store_true", help="")

parser.add_argument("-ip", "--input-profile", help="")
parser.add_argument("-cp", "--cmyk-profile", help="")
parser.add_argument("-op", "--output-profile", help="")


parser.add_argument("-b", "--blur", choices=["none", "box", "gaussian"], default="gaussian", help="")

blur_group = parser.add_mutually_exclusive_group()
blur_group.add_argument("--no-blur", action="store_true", help="aa")
blur_group.add_argument("--box-blur", action="store_true", help="bb")
blur_group.add_argument("--gaussian-blur", action="store_true", help="cc")

gray_group = parser.add_argument_group("gray mode")
gray_group.add_argument("--angle")

cmyk_group = parser.add_argument_group("cmyk mode")
cmyk_group.add_argument("--cmyk-angles", metavar="DEG", nargs=4, help="")
cmyk_group.add_argument("--keep-cyan", action="store_true", help="")
cmyk_group.add_argument("--keep-magenta", action="store_true", help="")
cmyk_group.add_argument("--keep-yellow", action="store_true", help="")
cmyk_group.add_argument("--keep-key", action="store_true", help="")
cmyk_group.add_argument("--keep-black", action="store_true", help="")

rgb_group = parser.add_argument_group("rgb mode")
rgb_group.add_argument("--rgb-angles", metavar="DEG", nargs=3, help="")
rgb_group.add_argument("--keep-red", action="store_true", help="")
rgb_group.add_argument("--keep-green", action="store_true", help="")
rgb_group.add_argument("--keep-blue", action="store_true", help="")

args = parser.parse_args()


# 引数のバリデーションと展開
directory = args.directory
prefix = basename(args.prefix)
suffix = basename(args.suffix)
force = args.force
enum = args.enumerate

pitch = max(0.1, args.pitch)
cmyk_angles = ()
cmyk_keep_flags = (args.keep_cyan, args.keep_magenta, args.keep_yellow, args.keep_key or args.keep_black)
rgb_keep_flags = ()


if len([f for f in [args.no_blur, args.box_blur, args.gaussian_blur] if f]) > 1:
	print("")
	exit()
blur = None if args.no_blur else "box" if args.box_blur else "gaussian"





out_cmyk = False

cmyk_initent = 1
rgb_intent = 3


in_profile = ImageCms.createProfile("sRGB")
cmyk_profile = "profile/JapanColor2011Coated.icc"
out_profile = in_profile

ignore_profile = args.ignore_embedded_profile

#srgb =

pt_cmyk = make_profile_transform((in_profile, cmyk_profile), ("RGB", "CMYK"), cmyk_initent, not ignore_profile)
pt_rgb = make_profile_transform((cmyk_profile, out_profile), ("CMYK", "RGB"), rgb_intent, False)

# 出力ディレクトリの確認
mkdirp(directory)


# メインループ
n = len(args.images)
for i, f in enumerate(args.images, 1):
	try:
		img = Image.open(f)
		if img.mode == "L":
			pass
		elif img.mode == "CMYK":
			pass
		elif img.mode == "RGB":
			cmyk = pt_cmyk(img)
			cmyk.save(f"{i}.tiff")
			halftone = halftone_cmyk_image(cmyk, pitch, blur=blur, keep_flags=keep_flags)
			if out_cmyk:
				halftone.save(f"{i}.png")
			else:
				pt_rgb(halftone).save(f"{i}.png")
		else:
			pass
		print(f"{i} / {n} Done")
	except:
		print(f"{i} / {n} Error")

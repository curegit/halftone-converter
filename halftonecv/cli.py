import contextlib
from time import time
from glob import glob
from os.path import isfile
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from PIL import Image, ImageCms
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from .modules.args import positive, rate, nonempty, filenameseg, choice, intent
from .modules.utils import eprint, mkdirp, filepath, filerelpath, purefilename, altfilepath
from .modules.color import make_profile_transform, make_fake_transforms
from .modules.core import halftone_grayscale_image, halftone_rgb_image, halftone_cmyk_image

# メイン関数
def main():
	exit_code = 0

	try:
		# コマンドライン引数をパース
		parser = ArgumentParser(prog="halftonecv", allow_abbrev=False, formatter_class=ArgumentDefaultsHelpFormatter, description="Halftone Converter: an image converter to generate halftone images")
		parser.add_argument("images", metavar="FILE", type=nonempty, nargs="+", help="describe input image files")
		parser.add_argument("-q", "--quiet", action="store_true", help="suppress non-error messages")
		parser.add_argument("-e", "--exit", action="store_true", help="stop immediately by an error even if jobs remain")
		parser.add_argument("-g", "--glob", action="store_true", help="interpret FILE values as glob patterns")
		parser.add_argument("-f", "--force", action="store_true", help="overwrite existing files by outputs")
		parser.add_argument("-d", "--directory", metavar="DIR", type=nonempty, default=".", help="save output images in DIR directory")
		parser.add_argument("-P", "--prefix", type=filenameseg, default="", help="specify a prefix string of output filenames")
		parser.add_argument("-S", "--suffix", type=filenameseg, default="-halftone", help="specify a suffix string of output filenames")
		parser.add_argument("-E", "--enumerate", metavar="START", type=int, nargs="?", const=1, help="use consecutive numbers as output filenames")
		parser.add_argument("-p", "--pitch", "--interval", metavar="PX", type=positive, default=4, help="arrange halftone dots at intervals of PX pixels in input images")
		parser.add_argument("-x", "-s", "--scale", type=positive, default=1, help="the scale factor of output images to input images")
		parser.add_argument("-b", "--blur", type=choice, choices=["box", "gaussian"], nargs="?", const="gaussian", help="apply blur effect (if no blur type is specified, gaussian is used)")
		parser.add_argument("-B", "--blur-radius", metavar="PX", type=positive, help="specify blur radius (if not specified, half of the pitch is used)")
		parser.add_argument("-F", "--resample", type=choice, choices=["nearest", "linear", "lanczos2", "lanczos3", "spline36"], default="linear", help="resampling method for determining dot size")
		parser.add_argument("-A", "--angle", "--gray-angle", metavar="DEG", dest="gray_angle", type=float, default=45, help="arrange dots by DEG degrees in Gray channel")
		parser.add_argument("-t", "--Angles", "--rgb-angles", metavar="DEG", dest="rgb_angles", type=float, nargs=3, default=(15, 75, 30), help="arrange dots by DEG degrees in each RGB channels")
		parser.add_argument("-a", "--angles", "--cmyk-angles", metavar="DEG", dest="cmyk_angles", type=float, nargs=4, default=(15, 75, 30, 45), help="arrange dots by DEG degrees in each CMYK channels")
		parser.add_argument("-m", "--mode", type=choice, choices=["auto", "gray", "rgb", "cmyk"], default="auto", help="color space type to generate halftones")
		parser.add_argument("-o", "--output", type=choice, choices=["auto", "gray", "rgb", "cmyk"], default="auto", help="color space type to save output images")
		parser.add_argument("-T", "--tiff", "--out-tiff", action="store_true", help="save TIFF images instead of PNG images")
		parser.add_argument("-G", "--input-gray-profile", metavar="GRAY_ICC_FILE", type=nonempty, help="specify ICC profile for input Gray images")
		parser.add_argument("-I", "--input-rgb-profile", metavar="RGB_ICC_FILE", type=nonempty, help="specify ICC profile for input RGB images")
		parser.add_argument("-M", "--input-cmyk-profile", metavar="CMYK_ICC_FILE", type=nonempty, help="specify ICC profile for input CMYK images")
		parser.add_argument("-L", "--gray-profile", metavar="GRAY_ICC_FILE", type=nonempty, help="specify ICC profile for transform to Gray images")
		parser.add_argument("-l", "--gray-intent", type=intent, choices=["per", "sat", "rel", "abs", 0, 1, 2, 3], default=1, help="rendering intent for transform to Gray images")
		parser.add_argument("-R", "--rgb-profile", metavar="RGB_ICC_FILE", type=nonempty, help="specify ICC profile for transform to RGB images")
		parser.add_argument("-r", "--rgb-intent", type=intent, choices=["per", "sat", "rel", "abs", 0, 1, 2, 3], default=1, help="rendering intent for transform to RGB images")
		parser.add_argument("-C", "--cmyk-profile", metavar="CMYK_ICC_FILE", type=nonempty, help="specify ICC profile for transform to CMYK images")
		parser.add_argument("-c", "--cmyk-intent", type=intent, choices=["per", "sat", "rel", "abs", 0, 1, 2, 3], default=1, help="rendering intent for transform to CMYK images")
		parser.add_argument("-H", "--allow-huge", action="store_true", help="disable the limitation of input image size")
		parser.add_argument("--ignore", "--ignore-embedded-profile", action="store_true", help="don't use ICC profiles embedded in input images")
		parser.add_argument("--discard", "--discard-profile", action="store_true", help="don't embed ICC profiles in output images")
		parser.add_argument("--naive", "--naive-transform", action="store_true", help="use approximate conversion algorithm (naive transform) instead of ICC-based transform")
		parser.add_argument("--gamma-correction", action="store_true", help="apply gamma correction of sRGB for RGB-CMYK conversion when the naive transform is used")
		parser.add_argument("--key", "--key-from", metavar="RATE", type=rate, default=0.5, help="black ingredient threshold within 0.0-1.0 for RGB-CMYK conversion when the naive transform is used")
		parser.add_argument("-K", "--keep-all", action="store_true", help="don't convert any channels to halftones")
		parser.add_argument("--keep-red", action="store_true", help="don't convert R channels to halftones")
		parser.add_argument("--keep-green", action="store_true", help="don't convert G channels to halftones")
		parser.add_argument("--keep-blue", action="store_true", help="don't convert B channels to halftones")
		parser.add_argument("--keep-cyan", action="store_true", help="don't convert C channels to halftones")
		parser.add_argument("--keep-magenta", action="store_true", help="don't convert M channels to halftones")
		parser.add_argument("--keep-yellow", action="store_true", help="don't convert Y channels to halftones")
		parser.add_argument("--keep-key", action="store_true", help="don't convert K channels to halftones")
		args = parser.parse_args()

		# keep フラグの一括セット
		if args.keep_all:
			args.keep_red = True
			args.keep_green = True
			args.keep_blue = True
			args.keep_cyan = True
			args.keep_magenta = True
			args.keep_yellow = True
			args.keep_key = True

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
			rgb_profile = ImageCms.getOpenProfile(filerelpath("profiles/sRGB.icc"))
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
			rgb_cmyk = make_profile_transform((rgb_profile, cmyk_profile), ("RGB", "CMYK"), args.cmyk_intent, not args.ignore)
			cmyk_rgb = make_profile_transform((cmyk_profile, rgb_profile), ("CMYK", "RGB"), args.rgb_intent, not args.ignore)
			in_rgb_cmyk = make_profile_transform((in_rgb_profile, cmyk_profile), ("RGB", "CMYK"), args.cmyk_intent, not args.ignore)
			in_cmyk_rgb = make_profile_transform((in_cmyk_profile, rgb_profile), ("CMYK", "RGB"), args.rgb_intent, not args.ignore)
			gray_rgb = make_profile_transform((gray_profile, rgb_profile), ("L", "RGB"), args.rgb_intent, not args.ignore)
			rgb_gray = make_profile_transform((rgb_profile, gray_profile), ("RGB", "L"), args.gray_intent, not args.ignore)
			in_gray_rgb = make_profile_transform((in_gray_profile, rgb_profile), ("L", "RGB"), args.rgb_intent, not args.ignore)
			in_rgb_gray = make_profile_transform((in_rgb_profile, gray_profile), ("RGB", "L"), args.gray_intent, not args.ignore)
			gray_cmyk = make_profile_transform((gray_profile, cmyk_profile), ("L", "CMYK"), args.cmyk_intent, not args.ignore)
			cmyk_gray = make_profile_transform((cmyk_profile, gray_profile), ("CMYK", "L"), args.gray_intent, not args.ignore)
			in_gray_cmyk = make_profile_transform((in_gray_profile, cmyk_profile), ("L", "CMYK"), args.cmyk_intent, not args.ignore)
			in_cmyk_gray = make_profile_transform((in_cmyk_profile, gray_profile), ("CMYK", "L"), args.gray_intent, not args.ignore)

		# ピクセル数の制限を無くす
		if args.allow_huge:
			Image.MAX_IMAGE_PIXELS = None

		# 処理対象ファイルをリスティング
		if args.glob:
			input_images = []
			for i in args.images:
				input_images += [f for f in glob(i, recursive=True) if isfile(f)]
			input_images = list(dict.fromkeys(input_images))
		else:
			input_images = args.images
		n = len(input_images)

		# 処理対象のファイル数を表示
		if not args.quiet:
			if n == 0:
				print("No files matched")
			elif n == 1:
				print("One processing target has been queued")
			else:
				print(f"{n} processing targets have been queued")

		# 処理のメインループ
		for i, f in enumerate(input_images):
			t = time()
			try:
				# 画像を開く
				img = Image.open(f)
				if img.mode == "LA":
					img = img.convert("L")
				elif img.mode == "RGBA":
					img = img.convert("RGB")
				elif img.mode == "P":
					bg = Image.new("RGBA", img.size, "White")
					img = Image.alpha_composite(bg, img.convert("RGBA")).convert("RGB")
				if not img.mode in ["L", "RGB", "CMYK"]:
					raise ValueError("unsupported image type")
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
				blur = None if args.blur is None else (args.blur, args.blur_radius)
				cols = (
					TextColumn("[progress.description]{task.description}"),
					BarColumn(bar_width=50),
					TaskProgressColumn(),
				)
				with contextlib.nullcontext(None) if args.quiet else Progress(*cols) as progress:
					if target.mode == "L":
						if progress is None:
							fn = None
						else:
							t = progress.add_task("Gray", total=1.0)
							fn = lambda p: progress.update(t, completed=p)
						halftone = halftone_grayscale_image(target, args.pitch, args.gray_angle, args.scale, blur, args.resample, progress_callback=fn)
					elif target.mode == "RGB":
						if progress is None:
							fns = (None, None, None)
						else:
							r = progress.add_task("[red]Red", total=1.0)
							g = progress.add_task("[green]Green", total=1.0)
							b = progress.add_task("[blue]Blue", total=1.0)
							fns = (
								lambda p: progress.update(r, completed=p),
								lambda p: progress.update(g, completed=p),
								lambda p: progress.update(b, completed=p),
							)
						halftone = halftone_rgb_image(target, args.pitch, args.rgb_angles, args.scale, blur, args.resample, (args.keep_red, args.keep_green, args.keep_blue), progress_callbacks=fns)
					elif target.mode == "CMYK":
						if progress is None:
							fns = (None, None, None, None)
						else:
							c = progress.add_task("[cyan]Cyan", total=1.0)
							m = progress.add_task("[magenta]Magenta", total=1.0)
							y = progress.add_task("[yellow]Yellow", total=1.0)
							k = progress.add_task("Key", total=1.0)
							fns = (
								lambda p: progress.update(c, completed=p),
								lambda p: progress.update(m, completed=p),
								lambda p: progress.update(y, completed=p),
								lambda p: progress.update(k, completed=p),
							)
						halftone = halftone_cmyk_image(target, args.pitch, args.cmyk_angles, args.scale, blur, args.resample, (args.keep_cyan, args.keep_magenta, args.keep_yellow, args.keep_key), progress_callbacks=fns)
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
				if args.discard:
					if complete.info.get("icc_profile"):
						complete.info.pop("icc_profile")
				# 出力ディレクトリを作る
				mkdirp(args.directory)
				# ファイルへ保存する
				if args.enumerate is None:
					name = args.prefix + purefilename(f) + args.suffix
				else:
					name = args.prefix + f"{args.enumerate + i}" + args.suffix
				if complete.mode == "CMYK" or args.tiff:
					path = filepath(args.directory, name, "tiff")
				else:
					path = filepath(args.directory, name, "png")
				if not args.force:
					path = altfilepath(path, suffix="+")
				complete.save(path)
			# エラーを報告する
			except Exception as e:
				eprint(f"{i + 1}/{n} error: {f}")
				eprint(e)
				exit_code = 1
				if args.exit:
					return exit_code
			# 成功を報告する
			else:
				dt = time() - t
				if not args.quiet:
					print(f"{i + 1}/{n} done: {f} -> {path} ({dt:.1f} sec)")
		return exit_code

	except KeyboardInterrupt:
		eprint("KeyboardInterrupt")
		exit_code = 130
		return exit_code

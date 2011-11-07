#!/usr/bin/env python
# encoding: utf-8
"""
img2pdf

Created by See-ming Lee on 2011-11-06.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
from PIL import Image
import getopt
from reportlab.pdfgen import canvas
import os
import os.path
import sys

__version__ = "0.1"

def showVersion():
	print('img2pdf v'+__version__+', by See-ming Lee:')
	print('Convert images in folder to PDF document')

def showUsage():
	print('')
	showVersion()
	print('''
	Usage: img2pdf src dst
	  -h, -?, --help        display this help information
	  -V, --version         display version
	  -n, --name            name of the pdf file
	  -o, --no-outline      do not include outline
	  -c, --compression     use compression
	  -v, --verbose         verbose output

	default values:
	  outline: yes
	  compression: no
	  verbose: no

	''')

class Img2PdfException(Exception):
	pass

class InvalidFolderException(Img2PdfException):
	pass



class img2pdf(object):
	"""load images and create pdf"""

	def __init__(self, folder, out_folder, pdfname=None, outline=True,
	             verbose=False, compression=0, maxpages=None):
		self.folder = self.getPath(folder, os.path.abspath('./'))
		self.out_folder = self.getPath(out_folder, os.path.abspath('./'))
		self.pdfname = pdfname
		if self.pdfname is None:
			self.pdfname = "%s.pdf" % (
				self.folder.split('/')[-1]
			)
		self.pdfname = self.getRealNormAbsPath(
			os.path.join(self.out_folder, self.pdfname)
		)
		self.compression = compression
		self.images = []
		self.canvas = canvas.Canvas(
			filename=self.pdfname,
			pagesize=(600, 600),
		    pageCompression=self.compression
		)
		self.outline = outline
		self.verbose = verbose
		self.maxpages = maxpages

	@classmethod
	def getRealNormAbsPath(cls, path):
		return os.path.realpath(
			os.path.normpath(
				os.path.abspath(path)
			)
		)

	@classmethod
	def getPath(cls, folder, default=None):
		f = folder
		try:
			if f is None:
				if default is None:
					raise InvalidFolderException("No default set.")
				else:
					f = default

			f = cls.getRealNormAbsPath(f)
			if not os.path.isdir(f):
				raise InvalidFolderException
		except InvalidFolderException, err:
			print('%s: %s is not a folder.' % (err, folder))
			return
		return f

	def convert(self):
		"""Generate the pdf object"""
		self.loadImages()
		self.createPDF()
		self.log(self)

	def loadImages(self):
		"""load images from folder"""
		files = os.listdir(self.folder)
		for infile in files:
			file, ext = os.path.splitext(infile)
			ext = str.lower(ext)[1:]
			if ext in ('jpg', 'jpeg', 'png', 'tif'):
				path = os.path.abspath(
					os.path.join(self.folder, infile)
				)
				try:
					img = Image.open(path)
					self.images.append({
						"path": path,
						"width": img.size[0],
						"height": img.size[1]
					})
					self.log("image added: %s" % infile)
				except IOError, err:
					print ("%s %s" % (err, path))

	def createPDF(self):
		pagecount=1
		for img in self.images:
			self.log("processing page %d" % pagecount)
			# image
			p = img['path']
			w = img['width']
			h = img['height']
			self.canvas.setPageSize((w, h))
			self.canvas.drawImage(p, 0, 0, width=w, height=h)
			# outline
			if self.outline:
				k = "p%d" % pagecount
				self.canvas.bookmarkPage(k)
				self.canvas.addOutlineEntry(
					title="%s %dx%d" % (os.path.basename(p), w, h),
					key=k,
				    level=0,
				    closed=0
				)

			self.canvas.showPage()
			pagecount += 1
			if self.maxpages is not None and pagecount > self.maxpages:
				break
		self.canvas.save()

	def log(self, s):
		if self.verbose:
			print(s)

	def __repr__(self):
		return "\n".join([
			"PDF object",
		    ">>> Filename = %s" % self.pdfname
		])

	def imageList(self):
		lines = []
		for img in self.images:
			lines.append(
				" ".join(["%s: %s" % (key, img[key]) for key in img.keys()])
			)
		return "\n".join(lines)

def main():
	# parse options
	try:
		opts, args = getopt.getopt(
			sys.argv[1:], 'hV?n:ocv',
			['help', 'version', 'name', 'no-outline', 'compression', 'verbose']
		)
	except getopt.GetoptError:
		Img2PdfException()
		return
	# read src and dst folders
	if len(args) < 2:
		showUsage()
		return
	src, dst = args[0], args[1]
	#option defaults
	name, outline, compress, verbose_ = None, True, 0, False
	#process options
	for o, a in opts:
		if o in ("-h", "--help", "-?"):
			showUsage()
			return
		if o in ("-V", "--version"):
			showVersion();
			return
		if o in ("-n", "--name"):
			name = a
		if o in ("-o", "--no-outline"):
			outline = False
		if o in ("-c", "--compression"):
			compress = 1
		if o in ("-v", "--verbose"):
			verbose_ = True

	pdf = img2pdf(
		folder=src,
		out_folder=dst,
	    pdfname=name,
	    outline=outline,
	    compression=compress,
	    verbose=verbose_
	)
	pdf.convert()

if __name__ == '__main__':
	main()

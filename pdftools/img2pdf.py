#!/usr/bin/env python
# encoding: utf-8
"""
img2pdf

Created by See-ming Lee on 2011-11-06.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
from PIL import Image
import argparse
from reportlab.pdfgen import canvas
import os
import os.path
import subprocess

__version__ = "0.2"

def getVersion():
	return '\n'.join([
		'img2pdf v' + __version__ + ', by See-ming Lee:',
		'Convert images in folder to PDF document'
	])


class Img2PdfException(Exception):
	pass


class InvalidFolderException(Img2PdfException):
	pass


class img2pdf(object):
	"""load images and create pdf"""

	def __init__(self, folder, out_folder, pdfname=None, outline=True,
	             verbose=False, compression=0, maxpages=None,
	             pagesize_w='disabled', pagesize_h='disabled',
	             openpdf=False):
		if folder is not None and hasattr(folder, '__iter__'):
			folder = folder[0]
		if out_folder is not None and hasattr(out_folder, '__iter__'):
			out_folder = out_folder[0]

		self.folder = self.getPath(folder, os.path.abspath('./'))

		self.out_folder = self.getPath(out_folder, os.path.abspath('./'))

		self.pdfname = pdfname
		if self.pdfname is None:
			self.pdfname = "%s.pdf" % (
			self.folder.split('/')[-1]
			)
		self.pdfname = os.path.join(self.out_folder, self.pdfname)

		self.compression = compression
		self.images = []
		self.canvas = canvas.Canvas(
			filename=self.pdfname,
			pagesize=(600, 600),
			pageCompression=self.compression
		)
		self.outline = outline
		self.verbose = verbose
		self.pagesize_w = pagesize_w
		self.pagesize_h = pagesize_h
		self.page_w_min = None
		self.page_w_max = None
		self.page_h_min = None
		self.page_h_max = None
		self.openpdf = openpdf
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
		print("PDF file created using the %d images from %s:\n%s" %
		      (len(self.images), self.folder, self.pdfname)
		)
		if self.openpdf:
			subprocess.call(['open', self.pdfname])

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
					if self.page_h_max is None:
						self.page_h_max = img.size[1]
						self.page_h_min = img.size[1]
					self.page_h_max = max(self.page_h_max, img.size[1])
					self.page_h_min = min(self.page_h_min, img.size[1])
					self.log("image added: %s" % infile)
				except IOError, err:
					print ("%s %s" % (err, path))

	def createPDF(self):
		pagecount = 1
		for img in self.images:
			self.log("processing page %d" % pagecount)
			# image
			p = img['path']
			w = img['width']
			h = img['height']
			r = float(w) / float(h)
			if self.pagesize_h == 'max':
				h = self.page_h_max
				w = r * h
			elif self.pagesize_h == 'min':
				h = self.page_h_min
				w = r * h

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
	parser = argparse.ArgumentParser(
		description="Create PDF from images.",
		prefix_chars='-+'
	)
	parser.add_argument('folder', metavar='src', default='./',
	                    help='source folder path')
	parser.add_argument('out_folder', metavar='dst', default='./',
	                    help='destination folder path')
	parser.add_argument('--version', action='version', version=getVersion())
	parser.add_argument('-n', '--name',
	                    default=None, dest='pdfname',
	                    help='name (not full path) of the generated pdf file.')
	parser.add_argument('-o', '--outline',
	                    default=True, action='store_false', dest='outline',
	                    help='include an outline as the TOC in PDF')
	parser.add_argument('+o', '++outline',
	                    default=True, action='store_true', dest='outline',
	                    help='include an outline as the TOC in PDF')
	parser.add_argument('-c', '--compression',
	                    default=False, action='store_false', dest='compression'
	                    ,
	                    help='use compression in pdf. Note: will make it very slow.')
	parser.add_argument('+c', '++compression',
	                    default=False, action='store_true', dest='compression',
	                    help='disable compression in pdf. Note: will make it very slow.')
	parser.add_argument('-v', '--verbose', '+v', '++verbose',
	                    default=False, action='store_true', dest='verbose',
	                    help='display more information on the process')
	parser.add_argument('--width', choices=['max', 'min', 'disabled'],
	                    default='disabled', dest='pagesize_w',
	                    help='use the minimum / maximum width as the page width for all pages.')
	parser.add_argument('--height', choices=['max', 'min', 'disabled'],
	                    default='disabled', dest='pagesize_h',
	                    help='use the minimum / maximum height as the page height for all pages.')
	parser.add_argument('--openpdf', dest='openpdf', default=False,
	                    action='store_true',
	                    help='open pdf file in default app after conversion completes.')
	args = parser.parse_args()

	print(args)

	pdf = img2pdf(**args.__dict__)
	pdf.convert()

if __name__ == '__main__':
	main()


#!/usr/bin/env python
# encoding: utf-8
"""
folders2pdf

Created by See-ming Lee on 2011-11-07.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
__author__ = 'See-ming Lee'
__email__ = 'seeminglee@gmail.com'
import os, sys

from img2pdf import img2pdf

def main(args):
	if len(args) > 2:
		parent = args[1]
		outfolder = args[2]
		for folder in os.listdir(parent):
			pth = os.path.abspath(
				os.path.join(parent, folder)
			)
			if os.path.isdir(pth):

				pdf = img2pdf(
					folder=pth,
					out_folder=outfolder,
				    pagesize_h='max'
				)
				pdf.convert()


if __name__ == '__main__':
	main(sys.argv)
	


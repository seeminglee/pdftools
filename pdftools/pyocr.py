#!/usr/bin/env pythonw
# encoding: utf-8
"""
pyocr

Created by See-ming Lee on 2011-11-17.
Copyright (c) 2011 See-ming Lee. All rights reserved.
"""
__author__ = 'See-ming Lee'
__email__ = 'seeminglee@gmail.com'


import wx
from PIL import Image
from PIL import ImageOps
from PIL import ImageEnhance
import os

# Image Conversion: WxBitmap to PIL
def WxBitmapToPilImage(bitmap):
	return WxImageToPilImage(WxBitmapToWxImage(bitmap))

def WxBitmapToWxImage(bitmap):
	return wx.ImageFromBitmap(bitmap)

# Image Conversion: PIL to WxBitmap
def PilImageToWxBitmap(pilImage):
	return WxImageToWxBitmap(PilImageToWxImage(pilImage))

def PilImageToWxImage(pilImage):
	wxImage = wx.EmptyImage(pilImage.size[0], pilImage.size[1])
	wxImage.SetData(pilImage.tostring())
	return wxImage

# Image Conversion: WxImage to PIL
def WxImageToPilImage(wxImage):
	pilImage = Image.new('RGB', (wxImage.GetWidth(), wxImage.GetHeight()))
	pilImage.fromstring(wxImage.GetData())
	return pilImage

def WxImageToWxBitmap(wxImage):
	return wxImage.ConvertToBitmap()

# ----------------------------------------------------------------------------
class OcrAppError(Exception):
	pass

# ----------------------------------------------------------------------------
from time import asctime

def jmtime():
	return '[' + asctime()[11:19] + '] '


# ----------------------------------------------------------------------------
__alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
RAW_KEYS = dict(
	[(k, __alpha.index(k) + 65) for k in __alpha ]
)
__alpha = __alpha.lower()
RAW_KEYS.update(dict(
	[(k, __alpha.index(k) + 65) for k in __alpha ]
))
del __alpha


# ----------------------------------------------------------------------------
# Control / widget containing the drawing
class DrawingArea(wx.Window):

	SCALE_TO_FIT = 0
	SCALE_TO_FILL = 1

	def __init__(self, parent, id):
		sty = wx.NO_BORDER
		wx.Window.__init__(self, parent, id, style=sty)
		self.parent = parent
		self.SetBackgroundColour(wx.WHITE)
		self.SetCursor(wx.CROSS_CURSOR)

		self.BufferBmp = None

		self.LoadPilImage()
		self.imageScale = self.SCALE_TO_FIT


		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
		self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvents)

		self.ocrArea = ( (0, 0), (0, 0) )



	def OnSize(self, event):
		print jmtime() + 'OnSize in DrawingArea'
		self.UpdateUI()



	def UpdateUI(self):

		self.wi, self.he = self.GetSizeTuple()
		self.BufferBmp = wx.EmptyBitmap(self.wi, self.he)
		memdc = wx.MemoryDC()
		memdc.SelectObject(self.BufferBmp)
		ret = self.UpdateUIBufferBmp(memdc)

		if not ret: #error
			self.BufferBmp = None
			wx.MessageBox('Error in drawing', 'CommntedDrawing', wx.OK | wx.ICON_EXCLAMATION)



	def OnPaint(self, event):
		print jmtime() + 'OnPaint in DrawingArea'
		dc = wx.PaintDC(self)
#		dc.BeginDrawing()
		if self.BufferBmp is not None:
			print jmtime() + '...drawing'
			dc.DrawBitmap(self.BufferBmp, 0, 0, True)
		else:
			print jmtime() + '...nothing to draw'
#		dc.EndDrawing()




	def OnKeyUp(self, event):

		keycode = event.GetKeyCode()

		# KEY: Contrast
		if keycode in ( RAW_KEYS['Y'], RAW_KEYS['y'],
		                RAW_KEYS['U'], RAW_KEYS['u']):
			adj = 1.5
			if keycode   in ( RAW_KEYS['Y'], RAW_KEYS['y'] ):
				self.contrast_f *= 1.0/adj
			elif keycode in ( RAW_KEYS['U'], RAW_KEYS['u'] ):
				self.contrast_f *= adj

		# KEY: Sharpness
		elif keycode in ( RAW_KEYS['I'], RAW_KEYS['i'],
		                  RAW_KEYS['O'], RAW_KEYS['o']):
			adj = 1.5
			if keycode   in ( RAW_KEYS['I'], RAW_KEYS['i'] ):
				self.sharpness_f *= 1.0/adj
			elif keycode in ( RAW_KEYS['O'], RAW_KEYS['o'] ):
				self.sharpness_f *= adj

		self.UpdateUI()


	def OnMouseEvents(self, event):
		if event.LeftDown():
			self.ocrArea[0] = (event.GetX(), event.GetY())
		elif event.LeftUp():
			self.ocrArea[1] = (event.GetX(), event.GetY())
			self.ProcessOCR()
		elif event.LeftIsDown():
			pen = wx.Pen(wx.BLACK, 1)
			pen.SetDashes([1, 2])
			brush = wx.Brush(wx.TRANSPARENT, 1)
			dc = wx.PaintDC(self)
			dc.Clear()
			dc.BeginDrawing()
			dc.SetPen(pen)
			dc.SetBrush(brush)
			dc.DrawRectangle()



	def GetFilteredImage(self):
		self.filteredImage = None

		contrast = ImageEnhance.Contrast(self.pilImage)
		self.filteredImage = contrast.enhance(self.contrast_f)

		sharpness = ImageEnhance.Sharpness(self.filteredImage)
		self.filteredImage = sharpness.enhance(self.sharpness_f)

		print("contrast: %s   sharpness: %s" % (self.contrast_f, self.sharpness_f))


	def UpdateUIBufferBmp(self, dc):

		try:
			print jmtime() + '...UpdateUIBufferBmp in DrawingArea'

			dcwi, dche = dc.GetSizeTuple()
			self.GetFilteredImage()

			if self.filteredImage is not None:

				dc.BeginDrawing()

				if self.imageScale == self.SCALE_TO_FIT:
					thumb = self.filteredImage.copy()
					thumb.thumbnail((dcwi, dche), Image.ANTIALIAS)

					dc.DrawBitmap(
						PilImageToWxBitmap(
							thumb
						), 0, 0
					)

				elif self.imageScale == self.SCALE_TO_FILL:
					dc.DrawBitmap(
						PilImageToWxBitmap(
							ImageOps.fit(self.filteredImage, (dcwi, dche), Image.ANTIALIAS)
						), 0, 0
					)

				dc.EndDrawing()
			return True

		except OcrAppError:
			return False


	def LoadPilImage(self):
		print jmtime() + 'loading image in DrawingArea'
		self.pilImage = Image.open(
			os.path.abspath(
				'/Users/sml/Dropbox/prj/python_projects/pdftools/lab/page05.jpg'
			)
		)
		wi = self.pilImage.size[0]
		he = self.pilImage.size[1]
		n = 80
		#fake crop to get rid of page number
		self.pilImage = self.pilImage.crop(
			(n, n, wi-n, he-n)
		)
		#enhance contrat
		self.contrast_f = 1.5
		self.sharpness_f = 2.0
		out = self.pilImage.copy()
		out = ImageEnhance.Contrast(out).enhance(self.contrast_f)
		out = ImageEnhance.Sharpness(out).enhance(self.sharpness_f)

		#now crop to bbox
		out.crop(out.getbbox())
		self.pilImage = out.copy()

		self.imageSize = (self.pilImage.size[0], self.pilImage.size[1])

		print jmtime() + 'image loaded'
#		return self.pilImage


	def ProcessOCR(self):
		pass


# ----------------------------------------------------------------------------
# Panel in main frame
class MainPanel(wx.Panel):

	def __init__(self, parent, id):
		wx.Panel.__init__(self, parent, id, wx.DefaultPosition, wx.DefaultSize)

		self.drawingarea = DrawingArea(self, -1)

		self.SetAutoLayout(True)

		gap = 0
		lc = wx.LayoutConstraints()
		lc.top.SameAs(self, wx.Top, gap)
		lc.left.SameAs(self, wx.Left, gap)
		lc.right.SameAs(self, wx.Width, gap)
		lc.bottom.SameAs(self, wx.Bottom, gap)
		self.drawingarea.SetConstraints(lc)



# ----------------------------------------------------------------------------
# Usual frame which can be reized, max'ed and min'ed.
# Frame contains one pagnel
class AppFrame(wx.Frame):

	def __init__(self, parent, id):
		wx.Frame.__init__(self, parent, id, 'OCR App',
		                  wx.Point(200,100), wx.Size(800, 900))
		self.panel = MainPanel(self, -1)

		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

	def OnCloseWindow(self, event):
		print jmtime() + 'onCloseWindow in AppFrame'
		self.Destroy()



# ----------------------------------------------------------------------------
class App(wx.App):

	def OnInit(self):
		frame = AppFrame(None, -1)
		frame.Show(True)
		self.SetTopWindow(frame)

		return True



# ----------------------------------------------------------------------------
def main():
	print 'main is running...'
	app = App(0)
	app.MainLoop()

if __name__ == '__main__':
	main()


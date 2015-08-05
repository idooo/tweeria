# -*- coding: UTF-8 -*-

import basic
import cherrypy, re, os
import simplejson as json
import time
import md5
import time
from datetime import datetime

try:
	from PIL import ImageOps, Image
except ImportError:
	print("Image library not found")

class ajaxController(basic.defaultController):
	tmpVar = ""

	DIR = './ajax/'

	@basic.printpage
	def printPage(self, page, params):
		return {
			'ajax': self.printData,
		}

	@basic.methods
	def methods(self, params = {}):
		# print "<<<<<<<<<<",params,">>>>>>>>>>>>>>"
		return {
			'action': {
				'prepareImageToCrop': self.prepareImage,
			    'crop_image'        : self.cropImage
			}
		}
	def printData(self,fields,params):
		template = 'preview_image'
		if self.tmpVar != "":
			fields['param_img'] = self.tmpVar


		if 'action' in params and params['action']=='crop_image':
			fields = {
				'params': self.cropImage(params)
			}
			template = 'test_img'

		# print params
		return basic.defaultController._printTemplate(self, template, fields)

	def cropImage(self,params):

		original_image = self.sbuilder.core_settings.APP_DIR+"templates"+params['img_to_crop']
		dest_folder = ""

		if "type_of_form" in params and params['type_of_form'] == "create_artwork":
			dest_folder =  "artworks/"
		elif "type_of_form" in params and params['type_of_form'] == "create_item":
			dest_folder =  "items/"
		elif "type_of_form" in params and params['type_of_form'] == "create_spell":
			dest_folder =  "spells/"

		dest_image = original_image.replace(
			self.sbuilder.core_settings.TMP_IMG_PATH,
			self.sbuilder.core_settings.TEMPLATES_FOLDER + self.sbuilder.core_settings.RESIZED_IMG_PATH+dest_folder
		)

		image = Image.open(original_image)
		box = (
			int(float(params['x1'])),
			int(float(params['y1'])),
			int(float(params['x2'])),
			int(float(params['y2']))
		)
		image = image.crop(box)
		image.save(dest_image,"PNG")

		self.resizeImage(original_image, dest_image, params, image)

		os.remove(original_image)

		return dest_image.replace(self.sbuilder.core_settings.APP_DIR+"templates","")

	def resizeImage(self, buffer_filepath, local_filepath, params, cropped_image = False):

		image = Image.open(buffer_filepath)

		width, height = image.size
		imgData = {
			"width" : width,
			"height": height
		}

		need_resize = False

		createSmallItemSpell = False
		if "type_of_form" in params and params['type_of_form'] == "create_artwork":
			checkWidth = self.core.MAX_ARTWORK_WIDTH
			checkHeight = self.core.MAX_ARTWORK_HEIGHT

		elif "type_of_form" in params and (params['type_of_form'] == "create_item" or params['type_of_form'] == "create_spell"):
			checkWidth = self.core.MAX_ITEM_SPELL_WIDTH
			checkHeight = self.core.MAX_ITEM_SPELL_HEIGHT
			createSmallItemSpell = True
		else:
			checkWidth = self.core.MAX_AVA_WIDTH
			checkHeight = self.core.MAX_AVA_HEIGHT

		if width > checkWidth:
			width = checkWidth
			need_resize = True

		if height > checkHeight:
			height = checkHeight
			need_resize = True

		#need_resize = False

		if need_resize:
			if params['type_of_form'] == "create_artwork":
				thumb = ImageOps.fit(cropped_image, (self.core.THUMB_ARTWORK_WIDTH, self.core.THUMB_ARTWORK_HEIGHT), Image.ANTIALIAS)
			else:
				thumb = ImageOps.fit(cropped_image, (width,height), Image.ANTIALIAS)
			thumb.save(local_filepath+"_fit.png", "PNG")
		elif params['type_of_form'] == "create_artwork":
			thumb = ImageOps.fit(cropped_image, (self.core.THUMB_ARTWORK_WIDTH, self.core.THUMB_ARTWORK_HEIGHT), Image.ANTIALIAS)
			thumb.save(local_filepath+"_fit.png", "PNG")
		else:
			image.save(local_filepath+"_fit.png", "PNG")


		if createSmallItemSpell:
			thumb = ImageOps.fit(cropped_image, (self.core.THUMB_ITEM_SPELL_WIDTH, self.core.THUMB_ITEM_SPELL_HEIGHT), Image.ANTIALIAS)
			thumb_local_filpath = local_filepath+"_thumb.png"
			thumb.save(thumb_local_filpath,"PNG")
		return imgData

	def prepareImage(self,params):
		self.tmpVar = self.uploadImage(params["img"], params)

	def uploadImage(self, image, params, just_return_str = True):
		if image.filename == '':
			#error = 'img.not_a_file'
			return {'not_uploaded': True}
		else:
			result = re.search('(.*)\.(png|gif|jpg|jpeg)$',image.filename,re.I)
			if result:

				#print "PARAMS AS 107", params

				size = int(cherrypy.request.headers['content-length'])
				checkSize = self.sbuilder.core_settings.MAX_UPLOAD_FILE_SIZE

				if "type_of_form" in params and params['type_of_form'] == "create_artwork":
					checkSize = self.sbuilder.core_settings.MAX_ARTWORK_UPLOAD_FILE_SIZE

				if size < checkSize:

					data = image.file.read()
					fileExt = result.group(2).lower()
					timeStr = str(int(time.time()))
					#fileName = self.cur_player['login_name']+"_"+timeStr+"_"+result.group(1)
					fileName = md5.new(self.cur_player['login_name']+"_"+timeStr+"_"+result.group(1)).hexdigest()

					local_buffer_filepath = self.sbuilder.core_settings.TEMPLATES_FOLDER+self.sbuilder.core_settings.IMAGE_BUFFER_FOLDER+fileName+'.png'

					# local_filepath = self.sbuilder.core_settings.APP_DIR+self.sbuilder.core_settings.TMP_IMG_PATH+fileName+'.png'


					fp = open(local_buffer_filepath,'w')
					fp.write(data)
					fp.close()

					#imgData = resizeImage(local_buffer_filepath, local_filepath, params)
					image = Image.open(local_buffer_filepath)

					width, height = image.size
					imgData = {}

					imgData.update({
						"width": width,
					    "height" : height,
						"src": self.sbuilder.core_settings.IMAGE_BUFFER_FOLDER+fileName+".png"
					})
					print "----------- IMG DATA ----------------", imgData
					return json.dumps(imgData)

				else:
					error = "img.big_size"
					code = 1
			else:
				error = "img.incorrect_extention"
				code = 2
		try:
			return {"error": error, "code":code}
		except:
			pass

data = {
	'class': ajaxController,
	'type': ['u'],
	'urls': ['ajax']
}
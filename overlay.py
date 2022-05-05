#!/usr/bin/python3.5

#  ffmpeg -y -i /mnt/share/39290\ Стихия\ вооружений\ Воздух.mpg -vcodec hevc_nvenc -c:s copy -vf "movie=/mnt/share/over.mov,scale=720:576,setpts=PTS-STARTPTS+5/TB [inner]; [in][inner] overlay [out]" -b:v 8M -b:a 400k /mnt/share/39290\ Стихия\ вооружений\ Воздух.mp4

import os
import subprocess
import time
import logging
import xlrd

def getRes(filename):
	cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', '-i', filename.encode('utf-8')]
	result = subprocess.run(cmd, stdout=subprocess.PIPE)
	return str(result.stdout).split("'")[1].replace('\\n', '').split('x')

#------------------------------------------------------------------------------------------------------------------------------

def getDuration(filename):
	cmd = ['ffprobe', '-i', filename]
	result = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
	return str([x for x in result.stdout.readlines() if "Duration" in str(x)][-1].strip()).split(' ')[1].split(',')[0]

#------------------------------------------------------------------------------------------------------------------------------

def overlay(filename, zip, outfilename):
	resolution = getRes(filename)

	overfile = ZIPFOLDER + zip +'.mov'
	#cmd = 'ffmpeg -y -i "' + filename + '" -vcodec hevc_nvenc -c:s copy -vf "movie=' + overfile
	cmd = 'ffmpeg -y -i "' + filename + '" -vcodec h264_nvenc -c:s copy -vf "movie=' + overfile

	if ['1280', '720'] == resolution:
		cmd += ',setpts=PTS-STARTPTS+5/TB [inner]; [in][inner] overlay [out]" -b:v 8M -b:a 400k ' + outfilename

	elif ['720', '576'] == resolution:
		cmd += ',scale=720:576,setpts=PTS-STARTPTS+5/TB [inner]; [in][inner] overlay [out]" -b:v 8M -b:a 400k ' + outfilename
		
	elif ['1920', '1080'] == resolution:
		cmd += ',setpts=PTS-STARTPTS+5/TB [inner]; [0:v]scale=1280:720[in]; [in][inner] overlay [out]" -b:v 8M -b:a 400k ' + outfilename

	proc = subprocess.call(cmd, shell=True)

#------------------------------------------------------------------------------------------------------------------------------

def listAllFiles(folder):
	allfiles = []

	if os.path.exists(folder):
		for root, dirs, files in os.walk(folder):
			for file in files:
				allfiles.append(os.path.join(root,file))

	return allfiles

#------------------------------------------------------------------------------------------------------------------------------

def listAllFilesExt(folder, ext):
	allfiles = []

	if os.path.exists(folder):
		for root, dirs, files in os.walk(folder):
			for file in files:
				if os.path.splitext(file)[1] == ext:
					allfiles.append(os.path.join(root, file))

	return allfiles

#------------------------------------------------------------------------------------------------------------------------------

def listToEncode(srcfolder, dstfolder):
	return [f for f in listAllFilesExt(srcfolder, '.mpg') if not os.path.exists(os.path.join(dstfolder, os.path.splitext(f)[0].split('/')[-1] + '.mp4'))]
	
	
#------------------------------------------------------------------------------------------------------------------------------

def readconfig(configfile):
	if os.path.exists(configfile):
		try:
			watchfile = open(configfile)
			watch = watchfile.readlines()
			watchfile.close()
			watch = [w.rstrip() for w in watch]
			return watch   

		except:
			print('something wrong with', configfile)
			
	else:
		print(configfile, 'not found')
		return ''

#------------------------------------------------------------------------------------------------------------------------------

def getZIPS(filename):
	if os.path.exists(filename):
		try:
			data = xlrd.open_workbook(filename)
			#sheet = data.sheet_by_name('октябрь 2')
			sheet = data.sheet_by_name(data.sheet_names()[-1])
			vals = [[sheet.row_values(rownum)[0], sheet.row_values(rownum)[1], sheet.row_values(rownum)[2]] for rownum in range(sheet.nrows)]
			return vals
			
		except:
			return ''
			
	else:
		return ''
	
#------------------------------------------------------------------------------------------------------------------------------

WATCHFOLDERS = "/mnt/scripts/overlay/folders.conf"
DSTFOLDER = "/mnt/scripts/overlay/dest.conf"
ZIPFOLDER = "/mnt/scripts/overlay/zip/"
LOG = "/mnt/scripts/overlay/log.txt"
ZIPS = "/mnt/share/ЗИПЫ.xlsx"

logging.basicConfig(filename=LOG, level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')

#------------------------------------------------------------------------------------------------------------------------------

start_time = time.time()

for item in getZIPS(ZIPS):
	filesrc = os.path.join(readconfig(WATCHFOLDERS)[0], item[0])
	fileext = os.path.splitext(item[0])[1]
	filedst = os.path.join(readconfig(DSTFOLDER)[0], item[0].replace(fileext, ' ' + item[1].replace(' ', '') + '.mp4'))

	if os.path.exists(filesrc) and not os.path.exists(filedst):
		if item[2]:
			item_start_time = time.time()
			overlay(filesrc, item[1].replace(' ', '') + 'smoke', '"' + filedst + '"')
			logging.info(item[0] + ' ' + getDuration(filesrc)  + ' ЗИП: ' + item[1].replace(' ', '') + item[2] + ' encoded in {0}'.format(time.time() - item_start_time) + ' seconds\n')
			
		else:
			item_start_time = time.time()
			overlay(filesrc, item[1].replace(' ', ''), '"' + filedst + '"')
			logging.info(item[0] + ' ' + getDuration(filesrc) + ' ЗИП: ' + item[1].replace(' ', '') + ' encoded in {0}'.format(time.time() - item_start_time) + ' seconds\n')

# print("--- %s seconds ---" % (time.time() - start_time))
logging.info("finally {0}\n".format(time.time() - start_time))

import csv 			#save data
import os			#file
import requests		#HTTP requests
import psutil		#kill process



#session = requests.session()
#return file_name_downloaded
def download_file(url, fileName='', session=''):
	local_filename = fileName if fileName else url.split('/')[-1]
	# NOTE the stream=True parameter
	
	r = session.get(url, stream=True) if session else requests.get(url, stream=True)

	try:
		with open(local_filename, 'wb') as f:
			for chunk in r.iter_content(chunk_size=1024): 
				if chunk: # filter out keep-alive new chunks
					f.write(chunk)
					#f.flush() commented by recommendation from J.F.Sebastian
		return local_filename
	except IOError as err:
		print format(err)
		return ''
# multi_kill: kill all processName
def kill_process(processName,multi_kill=True):
	for proc in psutil.process_iter():
	    if proc.name() == processName:
	        proc.kill()
	        if not multi_kill:
	        	return

#try to remove file
def remove(path):
	try:
		os.remove(path)
	except OSError as err:
		print format(err)

#try to show with no error
def show_image(path):
	try:
		from PIL import Image
		img = Image.open(path)
		img.show() 
		return 1
	except ImportError:
		import webbrowser
		webbrowser.open(path)
		return -1



#save as csv
#overwrite file
def write_file_csv(data, fileName):
	with open(fileName, 'wb') as csvfile:
		csvWriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		for row in data:
			csvWriter.writerow(row)


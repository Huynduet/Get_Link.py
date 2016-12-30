import requests
import csv 		#save data
#session = requests.session()
def download_file(url, fileName='', session=''):
	local_filename = fileName
	if not local_filename: 
		local_filename = url.split('/')[-1]
	# NOTE the stream=True parameter
	if session:
		r = session.get(url, stream=True)
	else:
		r = requests.get(url, stream=True)
	with open(local_filename, 'wb') as f:
		for chunk in r.iter_content(chunk_size=1024): 
			if chunk: # filter out keep-alive new chunks
				f.write(chunk)
				#f.flush() commented by recommendation from J.F.Sebastian
	return local_filename


#save as csv
#overwrite file
def write_file_csv(data, fileName):
	with open(fileName, 'wb') as csvfile:
		csvWriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		for row in data:
			csvWriter.writerow(row)

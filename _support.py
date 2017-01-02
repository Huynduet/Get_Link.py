import csv 			#save data
import os			#file
import re 			#regex
import requests		#HTTP requests
import psutil		#kill process
import base64, md5
from Crypto.Cipher import AES

def main():
	# a = [{"resolution":360,"type":"mp4","width":640,"height":360,"url":"url360"},{"resolution":480,"type":"mp4","width":854,"height":480,"url":"url480"}]
	# print get_url(a, keyQuality='resolution', keyUrl='url', quality=-1)

	passwd = "PhimMoi.Net://109892"
	string = open('str').read()
	# string = 'U2FsdGVkX1+\/Q3KwuDkL4ZvuvF6xdaHmS97sbgXEzxu\/9BEKCNQHqUHt\/HLZJIJYJvdCSWpHYkHSf5xgLFefeECdqDRaV77ucj5yySr0cMcoNSj2\/IbY+ja5+V\/xmlQBDd7Hk2GHkokxxa\/7pal+THkJejdBTXcDolu7YV\/yNw6hMyOr+eGqPg2rKXFceAOUGdvrIJFxTUmDkxl\/QYSYvfXmKmPRf9IhbDWJaB\/1\/LYtdyP8IXhXDtiXJskcYyz60bAbF\/aNfBz2LqTmyOvmiS8U2MqZO\/h9yuruIwinnNwKPjrMufG1qj\/mWdW7tbb7VpQBtn5nl\/MZD4INI4utYX8mkM8Y750gpGH4QNei2PgDTq4alD8NMmuEplnj9XfGyVINRlFgpIxUoqjqQC+wHbLSdSxiMGY0tqsNiW0I7vOT9n8RGRwCPPm6TmuDswATcgz2SVP558xdPuOpLhkgQazNR1LQUEzUHuN29TN1mmVP7X5WW11LnYRG4KhkgYCkXcTYJAVyzqwq5KF2VHr08hLw4L4jzL7rdXvSKBsC9fHsHWPxRazqVeUX07+NlhjX9+6T1maaUga0lkjAThHes\/puNzeSEmgeLpQC82zSKOUl4AZQVVhQQnqpVghSpB8Bde0NWfugDMQPbvYDgYvVpbSB1lurP1\/d9dmfNl2LjzI='

	print aes_decrypt(string, passwd)

def aes_cbc_decrypt(string, passwd):
	#declaire
	keySize = 256
	keyLen = int(keySize / 8)
	blockLen = 16

	#get str, key, iv for aes
	data = base64.b64decode(string)
	salt = data[8:16]
	encypted = data[16:]

	rounds = 3
	if 128 == keySize:
		rounds = 2
	tmpHash = str(passwd) + str(salt)
	md5_hash = [''] * rounds

	for i in xrange(0,len(md5_hash)):
		md5_hash[i] = md5.new(md5_hash[i-1] + tmpHash).digest()
		# print ''.join(md5_hash)

	hashResult = ''.join(md5_hash)
	key = hashResult[0: keyLen]
	iv = hashResult[keyLen: keyLen + blockLen]

	return AES.new(key, AES.MODE_CBC, iv).decrypt(encypted)


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
#jsonData must be dict
#return url by quality (<=0:'highest' - x - esle; dict{quality:url})
def get_url(jsonData, keyQuality, keyUrl, quality='all'):
	if not isinstance(jsonData, list) and not isinstance(jsonData, tuple):
		return ''

	ret = {}
	for item in jsonData:
		if isinstance(item, dict) and keyQuality in item and keyUrl in item:
			q = item[keyQuality]
			if isinstance(q, str) and re.search('\d+', q):
				q = re.search('\d+', q).group(0)

			ret[int(q)] = item[keyUrl]
	if not ret:
		return ''

		
	if isinstance(quality, int):
		if quality <= 0:
			return ret[max(ret.keys())]
		elif quality in ret:
			return ret[quality]
		else:
			return ret[min(ret.keys())]

	return ret
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


def show_error(errorLog):
	print errorLog
	return ''
#try to show with no error
def show_image(path):
	try:
		from PIL import Image
		img = Image.open(path).show()
	except ImportError:
		import webbrowser
		webbrowser.open(path)


#save as csv
#overwrite file
def write_file_csv(data, fileName):
	with open(fileName, 'wb') as csvfile:
		csvWriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		for row in data:
			csvWriter.writerow(row)

if __name__ == '__main__':
    main()
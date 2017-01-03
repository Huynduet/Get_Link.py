import ast 			#convert response string to dict
import re 			#regex
import requests		#requests.Session - cookie - get - post
import time			#sleep
import threading 	#multithread

import _support	#my function


__maxThread = 50 		#for multithread


def main():
	print get_list_anime47('http://anime47.com/xem-phim-ngoan-tay-du-ep-01/140640.html')
	# if l:
	# 	for link in l[0]:
	# 		print get_link_anime47(link,-1)
	# print get_list_phimmoi("http://www.phimmoi.net/phim/phi-dao-huu-kien-phi-dao-4620/xem-phim.html")


# auto detect host
# if 0<= startEp <= endEp: return array list
def get_links(url, quality='all', startEp=1, endEp = 0):
	match = re.search('://(www\.)?(.+)\..*?/', url)
	if not match:
		return _support.show_error('URL wrong!!')

	match = re.findall('(\w)', match.group(2))
	funcGetLink = 'get_link_' + ''.join(match)
	funcGetList = 'get_list_' + ''.join(match)

	if not funcGetLink in globals() or not funcGetList in globals():
		print funcGetLink, funcGetList
		return _support.show_error('Unknow domain!')

	#check get list
	if isinstance(startEp, int) and isinstance(endEp, int) and 0<= startEp <= endEp:
		listsFilms = eval(funcGetList)(url)
		ret = []
		for filmInfo in listsFilms:
			if not isinstance(filmInfo, dict):
				continue
			key = filmInfo.keys()[0]
			Ep = re.search('(\d+)', key)
			if Ep and int(Ep.group(1)) in xrange(startEp, endEp + 1):
				url = filmInfo[key]
				ret.append(eval(funcGetLink)(url, quality))

		return ret
	return eval(funcGetLink)(url, quality)


def get_link_anime47(url, quality='all'):
	if not 'anime47.com/xem-phim' in url:
		print 'get_link_anime47: URL ERROR!'
		return ''
	session = requests.session()

	source = session.get(url).text

	match = re.search('\{link:"https://drive.google.com/(.*?)"', source)
	if not match:
		print 'get_link_anime47: Get info ERROR'
		return ''
	data = {'link' : 'https://drive.google.com/' + match.group(1) }

	response = session.post('http://anime47.com/player/gkphp/plugins/gkpluginsphp.php', data=data).text
	if '"link":"https' in response:
		# print response
		response = response.replace('\\','').replace('true','True')
		links = ast.literal_eval(response)['link']
		return _support.get_url(links, keyQuality='label', keyUrl='link', quality=quality)

	
def get_list_anime47(url):
	if not 'anime47.com/' in url:
		print 'get_link_anime47: URL ERROR!'
		return ''
	if not 'anime47.com/xem-phim' in url:
		source = requests.get(url).text
		match = re.search('a class="play_info" href="(.*?)"> XEM ANIME', source)
		if not match:
			print 'get_link_anime47: Get info ERROR'
			return ''
		url =  match.group(1)

	source = requests.get(url).text
	if not '<div id="servers" class="serverlist">' in source:
		print 'get_link_anime47: No list exists!'
		return ''

	match = re.search('<div id="servers" class="serverlist">(.*?)<\/div',source)
	servers = match.group(1).split('span class="server')

	ret = []
	for x in xrange(1,len(servers)):
		match = re.findall('data-episode-tap="(.*?)".*?href="(.*?)">', servers[x])
		for pair in match:
			ret.append({pair[0] : pair[1]})


	return ret





def get_link_phimmoi(urls, quality='all'):
	#valid url
	if not re.search('phimmoi\.net/phim/(.+)-\d+(/.*?$)', url):
		print 'get_link_phimmoi: URL wrong!'
		return ''

	session = requests.session()
	source = session.get(url).text
	match = re.search('episodeinfo-v1\.1\.php.*?episodeid=(.*?)\&.*?"', source)
	if not match:
		print 'get_link_phimmoi: URL wrong!'
		return ''

	urlStream = 'http://www.phimmoi.net/' + match.group(0)
	aesKey = 'PhimMoi.Net://' + match.group(1)
	source = session.get(urlStream).text

	match = re.search('"medias":\[(.*?)\]', source)
	if not match:
		print 'get_link_phimmoi: Get Data ERROR!'
		return ''

	links = ast.literal_eval(match.group(1))
	urls = _support.get_url(links, keyQuality='resolution', keyUrl='url', quality=quality)

	if (isinstance(urls, dict)):
		ret = {}
		for key in urls:
			ret[key] = _support.aes_cbc_decrypt(urls[key], aesKey)
		return ret
	return _support.aes_cbc_decrypt(urls, aesKey)


def get_list_phimmoi(url):
	
	if not re.search('phimmoi\.net/phim/(.+)-\d+(/.*?$)', url):
		print 'get_link_phimmoi: URL wrong!'
		return ''
	if url[-1] == '/':
		url += 'xem-phim.html'

	source = requests.get(url).text

	match = re.findall('<li class="episode"><a(.*)>', source)
	if not match:
		return _support.show_error('get_link_phimmoi: Cant get list films')

	isPhimBo = '<ul class="server-list">' in source

	ret = []

	for anchor in match:
		key = re.search('backuporder="(.*?)"', anchor).group(1) if isPhimBo else re.search('number="(.*?)"', anchor).group(1)
		ret.append({key : 'http://www.phimmoi.net/' + re.search('href="(.*?)"', anchor).group(1) })

	return ret





















class Phimmoi(object):
	"""docstring for Phimmoi"""
	__maxThread = 50
	
	def __init__(self, url):
		match = re.search('phimmoi\.net/phim/(.+)-\d+(/.*?$)', url)
		if not match:
			print 'get_link_phimmoi: URL wrong!'
			return

		self.name = match.group(1).replace('-', '_')

		self.__url = url
		self.__listsFilms = []
		self.__result = []
		self.__cookies = {}
		self.__countThread = 0

	#error : return ''
	#mode = 'highest': return LinkHighestResolution
	#mode = 360/480/720/1080 return Link_Mode_Resolution (Mode <= mode)
	#mode = else: return array [Episode, Language, Link360p, Link480p, Link720p, Link1080p, LinkHighestResolution]
	def get_link(self, id, mode=''):
		if not self.__listsFilms:
			if not self.getlist_films():
				return ''

		if isinstance(id, int):
			if 0 <= id < len(self.__listsFilms):
				url = self.__listsFilms[id]
			else:
				print 'get_link_phimmoi: index out of range (', id , ')'
				return ''
		elif 'phimmoi.net/phim/' in id:
			url = id 
		else:
			print 'get_link_phimmoi: URL wrong!'
			return ''
	

		cookies = self.__cookies
		subSrc = requests.get(url, cookies=cookies).text
		matchInfo = re.findall("var get_linkToken='(.+)';\nvar fileId='(.+)';\nvar fileName='(.+)';", subSrc)
		
		if not matchInfo:
			print 'get_link_phimmoi: This url has been expired, Invalid or private!'
			return ''

		time.sleep(5)
		data = {'fileId': matchInfo[0][1], 'fileName': matchInfo[0][2], 'get_linkToken': matchInfo[0][0] }
		response = requests.post('http://www.phimmoi.net/download.php', data=data, cookies=cookies).text
		
		#check status
		if not '"videoStatus":"ok"' in response:
			print 'get_link_phimmoi: Something Wrong!\r\nFileName:', matchInfo[0][2], '\r\nURL:', url, '\r\nResponse:', response, '\r\n'
			return ''

		links = ast.literal_eval(response.replace('\\', ''))['links']

		if mode == 'highest':
			ret = links[-1]['url']
		elif isinstance(mode, int) and mode >= 360:
			for link in reversed(links):
				if link['resolution'] <= mode:
					ret = link['url']
					break
		else:
			#else, return array
			ret = [''] * 7
			match = re.search('PhimMoi.Net---Tap\.(.*?)-',response)
			if match:
				ret[0] = match.group(1) 
			ret[1] = 'Vietsub' if '-Vietsub-' in response else 'ThuyetMinh'

			for link in links:
				resolution = link['resolution']
				url = link['url']

				index = 2
				if resolution >= 1080:
					index = 5
				elif resolution >= 720:
					index = 4
				elif resolution >= 480:
					index = 3		

				ret[index] = url
				#highest resolution
				ret[6] = url
		threadName = threading.currentThread().name
		#getall_links: multithread
		# if threadName != 'MainThread':	
		# 	try:		
		# 		index = int(threadName)
		# 	except:
		# 		pass
		# 	else:
		# 		if 0 <= index < len(self.__result):
		# 			self.__result[index] = ret

		return ret

	#mode: see get_link
	def getall_links(self, mode='arrar'):
		if not self.__listsFilms:
			if not self.getlist_films():
				return ''

		episodes = self.__listsFilms if self.__listsFilms else self.getlist_films()
		if not episodes:
			return ''

		self.__result = [''] * ( len(episodes) + 1 )
		if not mode == 'highest' and not isinstance(mode, int):
			self.__result[0] = [''] * 7
			# self.__result[0][0] = 'Server' if '<th>Server<' in source else 'Episode'
			self.__result[0][0] = 'Episode'
			self.__result[0][1] = 'Language'
			self.__result[0][2] = '360'
			self.__result[0][3] = '480'
			self.__result[0][4] = '720'
			self.__result[0][5] = '1080'		
		
		for x in xrange(0,len(episodes)):
			#check max thread
			while threading.activeCount() >= self.__maxThread:
				time.sleep(0.1)

			threading.Thread(target=self.get_link, name=x+1, args=(episodes[x],mode,)).start()

		return self.__result
	#return and set self.__listsFilms = list all film in page download	
	def getlist_films(self):
		session = requests.session()

		match = re.search('phimmoi\.net/phim/(.+)(/.*?$)', self.__url)
		if not match:
			print 'get_link_phimmoi: URL wrong!'
			return ''
		urlDownloadList = 'http://www.phimmoi.net/phim/' + match.group(1) + '/download.html'
		source = session.get(urlDownloadList).text
		session.headers.update({'referer': urlDownloadList})

		#get token
		match = re.search("fx.token='(.*?)'",source)
		if not match:
			print 'get_link_phimmoi: URL ERROR!'
			return ''
		token = match.group(1)

		#get capchar
		match = re.search('verify-image.php\?verifyId=download&d=(.*?)"',source)
		if not match:
			print 'get_link_phimmoi: URL Capchar ERROR!'
			return ''
		capcharURL = 'http://www.phimmoi.net/' + match.group(0)
		
		capcharPath = 'capchar.jpeg'
		while 1:
			capcharPath = _support.download_file(capcharURL, capcharPath, session)
			if not capcharPath:
				print 'get_link_phimmoi: Download image capchar ERROR'
				return ''

			#show capchar
			_support.show_image(capcharPath)
			capchar = raw_input('Enter capchar: ')	

			#close image show window
			_support.kill_process('display')
			
			#get list
			urlDownloadList += '?_fxAjax=1&_fxResponseType=JSON&_fxToken=' + token

			data = {'download[verify]=':str(capchar)}
			source = session.post(urlDownloadList, data=data).text
			episodes = re.findall('href=."(.*?)" rel=', source)
			if not episodes:
				print 'get_link_phimmoi: Capchar Wrong!'
			else:
				for x in xrange(0,len(episodes)):
				 	episodes[x] = 'http://www.phimmoi.net/' + episodes[x].replace('\\', '')

				_support.remove(capcharPath)
			
				self.__cookies = session.cookies
				self.__listsFilms = episodes
				return episodes

	
if __name__ == '__main__':
    main()

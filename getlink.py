from PIL import Image                   
import thread 	#multithread
import requests	#requests.Session - cookie - get - post
import re 		#regex
import time		#sleep
import psutil	#kill process
import ast 		#convert response string to dict
import os		#remove file

import _support	#my function
class Phimmoi(object):
	"""docstring for Phimmoi"""
	maxThread = 30
	
	def __init__(self, url):
		match = re.search('phimmoi\.net/phim/(.+)-\d+(/.*?$)', url)
		if not match:
			print 'get_link_phimmoi: URL wrong!'
			return

		self.name = match.group(1).replace('-', '_')

		self.__url = url
		self.__listsFilms = []
		self.__cookies = ''
		self.__countThread = 0

	#error : return ''
	#mode = 'highest': return LinkHighestResolution
	#mode = 360/480/720/1080 return Link_Mode_Resolution (Mode <= mode)
	#mode = else: return array [Episode, Language, Link360p, Link480p, Link720p, Link1080p, LinkHighestResolution]
	def get_link(self, id, mode=''):
		if not self.__listsFilms:
			if not self.get_list_films():
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
		matchInfo = re.findall("var getLinkToken='(.+)';\nvar fileId='(.+)';\nvar fileName='(.+)';", subSrc)
		
		if not matchInfo:
			print 'get_link_phimmoi: This url has been expired, Invalid or private!'
			return ''

		time.sleep(5)
		data = {'fileId': matchInfo[0][1], 'fileName': matchInfo[0][2], 'getLinkToken': matchInfo[0][0] }
		response = requests.post('http://www.phimmoi.net/download.php', data=data, cookies=cookies).text
		
		#check status
		if not '"videoStatus":"ok"' in response:
			print 'get_link_phimmoi: Something Wrong!\r\nFileName:', matchInfo[0][2], '\r\nURL:', url, '\r\nResponse:', response, '\r\n'
			return ''

		links = ast.literal_eval(response)['links']

		if mode == 'highest':
			return links[-1]['url'].replace('\\', '')
		if isinstance(mode, int) and mode >= 360:
			for link in reversed(links):
				if link['resolution'] <= mode:
					return link['url'].replace('\\', '')

		#else, return array
		ret = [''] * 7
		match = re.search('PhimMoi.Net---Tap\.(.*?)-',response)
		if match:
			ret[0] = match.group(1) 
		ret[1] = 'Vietsub' if '-Vietsub-' in response else 'ThuyetMinh'

		for link in links:
			resolution = link['resolution']
			url = link['url'].replace('\\', '')

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

		return ret
	def get_list_films(self):
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
		
		
		while 1:
			_support.download_file(capcharURL, 'capchar', session)
			#show capchar
			img = Image.open('capchar')
			img.show() 

			capchar = raw_input('Enter capchar: ')	

			#close image show window
			for proc in psutil.process_iter():
			    if proc.name() == "display":
			        proc.kill()
			        # os.remove('capchar')

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

				os.remove('capchar')
				self.__cookies = session.cookies
				self.__listsFilms = episodes
				return episodes


	def get_all_links(self):

		episodes = self.__listsFilms if self.__listsFilms else self.get_list_films()
		# for episode in episodes:
		self.__result = [''] * ( len(episodes) + 1 )
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
			#while self.__countThread >= self.maxThread:
			# 	time.sleep(0.2)

			thread.start_new_thread(self.thread_get_raw_link, (episodes[x],x+1,))
			time.sleep(0.1)

		#wait for done
		while self.__countThread:
			time.sleep(1)

		return self.__result

	def thread_get_raw_link(self, url, episode):
		self.__countThread += 1

		self.__result[episode] = self.get_link(url)
		self.__countThread -= 1

# download_file('http://effbot.org/zone/thread-synchronization.htm','aa','a:a')
Phim = Phimmoi('http://www.phimmoi.net/phim/dao-hai-tac-665/')
# Phim.get_list_films()
data = Phim.get_all_links()
_support.write_file_csv(data, Phim.name)
# write_file_csv(data, 'data.csv')


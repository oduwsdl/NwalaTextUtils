import os
import requests
import sys
import time

from boilerpipe.extract import Extractor
from bs4 import BeautifulSoup
from multiprocessing import Pool

logger = logging.getLogger('NwalaTextUtils.textutils')

def genericErrorInfo():
	exc_type, exc_obj, exc_tb = sys.exc_info()
	fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	
	errorMessage = fname + ', ' + str(exc_tb.tb_lineno)  + ', ' + str(sys.exc_info())
	print('\tERROR:', errorMessage)

	return  sys.exc_info()

#html proc - start
def getCustomHeaderDict():

	headers = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Language': 'en-US,en;q=0.5',
		'Accept-Encoding': 'gzip, deflate',
		'Connnection': 'keep-alive',
		'Cache-Control':'max-age=0'	
		}

	return headers

def isSizeLimitExceed(responseHeaders, sizeRestrict):

	if( 'Content-Length' in responseHeaders ):
		if( int(responseHeaders['Content-Length']) > sizeRestrict ):
			return True

	return False

def downloadSave(response, outfile):
	
	try:
		with open(outfile, 'wb') as dfile:
			for chunk in response.iter_content(chunk_size=1024): 
				# writing one chunk at a time to pdf file 
				if(chunk):
					dfile.write(chunk) 
	except:
		genericErrorInfo()

def mimicBrowser(uri, getRequestFlag=True, extraParams=None):
	
	uri = uri.strip()
	if( len(uri) == 0 ):
		return ''

	if( extraParams is None ):
		extraParams = {}

	extraParams.setdefault('timeout', 10)
	extraParams.setdefault('sizeRestrict', -1)
	extraParams.setdefault('headers', getCustomHeaderDict())
	extraParams.setdefault('addResponseHeader', False)


	try:
		response = ''
		reponseText = ''
		if( getRequestFlag ):

			if( 'saveFilePath' in extraParams ):
				response = requests.get(uri, headers=extraParams['headers'], timeout=extraParams['timeout'], stream=True)#, verify=False
			else:
				response = requests.get(uri, headers=extraParams['headers'], timeout=extraParams['timeout'])#, verify=False
			
			if( extraParams['sizeRestrict'] != -1 ):
				if( isSizeLimitExceed(response.headers, extraParams['sizeRestrict']) ):
					return 'Error: Exceeded size restriction: ' + str(extraParams['sizeRestrict'])

			
			if( 'saveFilePath' in extraParams ):
				downloadSave(response, extraParams['saveFilePath'])
			else:
				reponseText = response.text

			if( extraParams['addResponseHeader'] ):
				return	{'responseHeader': response.headers, 'text': reponseText}

			return reponseText
		else:
			response = requests.head(uri, headers=extraParams['headers'], timeout=extraParams['timeout'])#, verify=False
			response.headers['status-code'] = response.status_code
			return response.headers
	except:

		genericErrorInfo()
		print('\tquery is: ', uri)
		if( getRequestFlag == False ):
			return {}
	
	return ''

def dereferenceURI(URI, maxSleepInSeconds=5, extraParams=None):
	
	URI = URI.strip()
	if( len(URI) == 0 ):
		return ''

	if( extraParams is None ):
		extraParams = {}
	
	htmlPage = ''
	try:
		
		if( maxSleepInSeconds > 0 ):
			print('\tderef.URI(), sleep:', maxSleepInSeconds)
			time.sleep(maxSleepInSeconds)

		extraParams.setdefault('sizeRestrict', 4000000)
		htmlPage = mimicBrowser(URI, extraParams=extraParams)
	except:
		genericErrorInfo()
	
	return htmlPage

def extractPageTitleFromHTML(html):

	title = ''
	try:
		soup = BeautifulSoup(html, 'html.parser')
		title = soup.find('title')

		if( title is None ):
			title = ''
		else:
			title = title.text.strip()
	except:
		genericErrorInfo()

	return title

def cleanHtml(html, method='python-boilerpipe'):
	
	if( len(html) == 0 ):
		return ''

	#experience problem of parallelizing, maybe due to: https://stackoverflow.com/questions/8804830/python-multiprocessing-pickling-error
	if( method == 'python-boilerpipe' ):
		try:
			extractor = Extractor(extractor='ArticleExtractor', html=html)
			return extractor.getText()
		except:
			genericErrorInfo()
	elif( method == 'nltk' ):
		"""
		Copied from NLTK package.
		Remove HTML markup from the given string.

		:param html: the HTML string to be cleaned
		:type html: str
		:rtype: str
		"""

		# First we remove inline JavaScript/CSS:
		cleaned = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", html.strip())
		# Then we remove html comments. This has to be done before removing regular
		# tags since comments can contain '>' characters.
		cleaned = re.sub(r"(?s)<!--(.*?)-->[\n]?", "", cleaned)
		# Next we can remove the remaining tags:
		cleaned = re.sub(r"(?s)<.*?>", " ", cleaned)
		# Finally, we deal with whitespace
		cleaned = re.sub(r"&nbsp;", " ", cleaned)
		cleaned = re.sub(r"  ", " ", cleaned)
		cleaned = re.sub(r"  ", " ", cleaned)

		#my addition to remove blank lines
		cleaned = re.sub("\n\s*\n*", "\n", cleaned)

		return cleaned.strip()

	return ''

def prlGetTxtFrmURIs(urisLst):

	size = len(urisLst)
	if( size == 0 ):
		return []

	docsLst = []
	jobsLst = []
	for i in range(size):

		printMsg = ''

		if( i % 10 == 0 ):
			printMsg = '\tderef uri i: ' + str(i) + ' of ' + str(size)

		keywords = {
			'URI': urisLst[i],
			'maxSleepInSeconds': 0
		}

		jobsLst.append( {
			'func': dereferenceURI, 
			'args': keywords, 
			'misc': False, 
			'print': printMsg
		})


	resLst = parallelTask(jobsLst)
	for res in resLst:
		
		text = cleanHtml( res['output'] )
		
		docsLst.append({
			'text': text,
			'id': urisLst[i],
			'title': extractPageTitleFromHTML( res['output'] ),
			'uri': res['input']['args']['URI']
		})

	return docsLst
#html proc - end

#parallel proc - start
def parallelProxy(job):
	
	output = job['func'](**job['args'])

	if( 'print' in job ):
		if( len(job['print']) != 0 ):
			print(job['print'])

	return {'input': job, 'output': output, 'misc': job['misc']}

def parallelTask(jobsLst, threadCount=5):

	if( len(jobsLst) == 0 ):
		return []

	if( threadCount < 2 ):
		threadCount = 2

	try:
		workers = Pool(threadCount)
		resLst = workers.map(parallelProxy, jobsLst)

		workers.close()
		workers.join()
	except:
		genericErrorInfo()
		return []

	return resLst
#parallel proc - end

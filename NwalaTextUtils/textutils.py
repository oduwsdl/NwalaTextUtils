import os
import logging
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
	
	errMsg = fname + ', ' + str(exc_tb.tb_lineno)  + ', ' + str(sys.exc_info())
	return errMsg

def readTextFromFile(infilename):

	text = ''

	try:
		with open(infilename, 'r') as infile:
			text = infile.read()
	except:
		logger.error( genericErrorInfo() + ', filename: ' + infilename )
	
	return text

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
		logger.error( genericErrorInfo() )

def mimicBrowser(uri, getRequestFlag=True, timeout=10, sizeRestrict=-1, addResponseHeader=False, saveFilePath=None, headers={}):
	
	uri = uri.strip()
	if( uri == '' ):
		return ''

	if headers == {}:
		headers = getCustomHeaderDict()

	try:
		response = ''
		reponseText = ''
		if( getRequestFlag is True ):

			if( saveFilePath is None ):
				response = requests.get(uri, headers=headers, timeout=timeout)
			else:
				response = requests.get(uri, headers=headers, timeout=timeout, stream=True)
				
			
			if( sizeRestrict != -1 ):
				if( isSizeLimitExceed(response.headers, sizeRestrict) ):
					return 'Error: Exceeded size restriction: ' + sizeRestrict

			
			if( saveFilePath is None ):
				reponseText = response.text
			else:
				downloadSave(response, saveFilePath)
				

			if( addResponseHeader is True ):
				return	{'response_header': response.headers, 'text': reponseText}

			return reponseText
		else:
			response = requests.head(uri, headers=headers, timeout=timeout)
			response.headers['status_code'] = response.status_code
			return response.headers
	except:
		logger.error(genericErrorInfo() + ', uri:' + uri)

		if( getRequestFlag is False ):
			return {}
	
	return ''

def derefURI(uri, sleepSec=0, timeout=10, sizeRestrict=4000000, headers={}):
	
	uri = uri.strip()
	if( uri == '' ):
		return ''

	htmlPage = ''
	try:
		
		if( sleepSec > 0 ):
			logger.info( 'derefURI(), sleep:' + str(sleepSec) )
			time.sleep(sleepSec)

		htmlPage = mimicBrowser(uri, sizeRestrict=sizeRestrict, headers=headers, timeout=timeout)
	except:
		err = genericErrorInfo()
		logger.error( err )
	
	return htmlPage

def getPgTitleFrmHTML(html):

	title = ''
	try:
		soup = BeautifulSoup(html, 'html.parser')
		title = soup.find('title')

		if( title is None ):
			title = ''
		else:
			title = title.text.strip()
	except:
		err = genericErrorInfo()
		logger.error( err )

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
			logger.error( genericErrorInfo() )
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

def parallelGetTxtFrmURIs(urisLst, updateRate=10):

	size = len(urisLst)
	if( size == 0 ):
		return []

	docsLst = []
	jobsLst = []
	for i in range(size):

		printMsg = ''

		if( i % updateRate == 0 ):
			printMsg = 'dereferencing uri ' + str(i) + ' of ' + str(size)

		keywords = {
			'uri': urisLst[i],
			'sleepSec': 0
		}

		jobsLst.append( {
			'func': derefURI, 
			'args': keywords, 
			'misc': False, 
			'print': printMsg
		})


	resLst = parallelTask(jobsLst)
	for res in resLst:
		
		text = cleanHtml( res['output'] )
		
		docsLst.append({
			'text': text,
			'title': getPgTitleFrmHTML( res['output'] ),
			'uri': res['input']['args']['uri']
		})

	return docsLst
#html proc - end

def parallelGetTxtFrmFiles(folder, rmHtml=False):
	
	folder = folder.strip()
	if( folder == '' ):
		return []

	if( folder[-1] != '/' ):
		folder = folder + '/'
	
	jobsLst = []
	files = os.listdir(folder)
	for i in range(len(files)):
		
		f = files[i].strip()
		if( f.startswith('.') ):
			continue

		keywords = {'infilename': folder + f}
		jobsLst.append( {'func': readTextFromFile, 'args': keywords, 'misc': False} )
	
	resLst = parallelTask(jobsLst)
	for res in resLst:
		
		res['text'] = res.pop('output')
		if( rmHtml ):
			res['text'] = cleanHtml( res['text'] )

		res['input']['filename'] = res['input']['args']['infilename']

		del res['input']['args']
		del res['input']['misc']
		del res['input']['func']
		del res['misc']

	return resLst


#parallel proc - start
def parallelProxy(job):
	
	output = job['func'](**job['args'])

	if( 'print' in job ):
		if( len(job['print']) != 0 ):
			
			logger.info( job['print'] )

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
		logger.error( genericErrorInfo() )
		return []

	return resLst
#parallel proc - end

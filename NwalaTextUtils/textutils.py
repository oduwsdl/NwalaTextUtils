import os
import logging
import requests
import sys
import time

from boilerpy3 import extractors
from bs4 import BeautifulSoup
from tldextract import extract
from multiprocessing import Pool

from subprocess import check_output
from urllib.parse import urlparse

logger = logging.getLogger('NwalaTextUtils.textutils')

def genericErrorInfo(slug=''):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    
    errMsg = fname + ', ' + str(exc_tb.tb_lineno)  + ', ' + str(sys.exc_info())
    logger.error(errMsg + slug)

    return errMsg

def readTextFromFile(infilename):

    text = ''

    try:
        with open(infilename, 'r') as infile:
            text = infile.read()
    except:
        genericErrorInfo( '\tfilename: ' + infilename )
    
    return text

#uri/html proc - start
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
                return    {'response_header': response.headers, 'text': reponseText}

            return reponseText
        else:
            response = requests.head(uri, headers=headers, timeout=timeout)
            response.headers['status_code'] = response.status_code
            return response.headers
    except:
        genericErrorInfo( '\turi: ' + uri )

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
        genericErrorInfo()
    
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
        genericErrorInfo()

    return title

def cleanHtml(html, method='boilerpy3'):
    
    if( len(html) == 0 ):
        return ''

    if( method == 'boilerpy3' ):
        try:
            extractor = extractors.ArticleExtractor()
            return extractor.get_content(html)
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

def naiveIsURIShort(uri):

    specialCases = ['tinyurl.com']

    try:
        scheme, netloc, path, params, query, fragment = urlparse( uri )
        if( netloc in specialCases ):
            return True

        path = path.strip()
        if( len(path) != 0 ):
            if( path[0] == '/' ):
                path = path[1:]

        path = path.split('/')
        if( len(path) > 1 ):
            #path length exceeding 1 is not considered short
            return False

        tld = extract(uri).suffix
        tld = tld.split('.')
        if( len(tld) == 1 ):
            #e.g., tld = 'com', 'ly'
            #short: http://t.co (1 dot) not news.sina.cn (2 dots)
            if( len(tld[0]) == 2 and netloc.count('.') == 1 ):
                return True
        else:
            #e.g., tld = 'co.uk'
            return False
    except:
        genericErrorInfo()

    return False

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

def expandURL(url, secondTryFlag=True, timeoutInSeconds='10'):

    timeoutInSeconds = str(timeoutInSeconds)
    '''
    Part A: Attempts to unshorten the uri until the last response returns a 200 or 
    Part B: returns the lasts good url if the last response is not a 200.
    '''
    url = url.strip()
    if( len(url) == 0 ):
        return ''

    longUrl = ''
    try:
        #Part A: Attempts to unshorten the uri until the last response returns a 200 or 
        output = check_output(['curl', '-s', '-I', '-L', '-m', '10', '-c', 'cookie.txt', url])
        output = output.decode('utf-8')
        output = output.splitlines()
        
        path = ''
        locations = []

        for line in output:
            line = line.strip()
            if( len(line) == 0 ):
                continue

            indexOfLocation = line.lower().find('location:')
            if( indexOfLocation != -1 ):
                #location: is 9
                locations.append(line[indexOfLocation + 9:].strip())

        if( len(locations) != 0 ):
            #traverse location in reverse: account for redirects to path
            #locations example: ['http://www.arsenal.com']
            #locations example: ['http://www.arsenal.com', '/home#splash']
            for url in locations[::-1]:
                
                if( url.strip().lower().find('/') == 0 and len(path) == 0 ):
                    #find path
                    path = url

                if( url.strip().lower().find('http') == 0 and len(longUrl) == 0 ):
                    #find url
                    
                    #ensure url doesn't end with / - start
                    #if( url[-1] == '/' ):
                    #   url = url[:-1]
                    #ensure url doesn't end with / - end

                    #ensure path begins with / - start
                    if( len(path) != 0 ):
                        if( path[0] != '/' ):
                            path = '/' + path
                    #ensure path begins with / - end

                    longUrl = url + path

                    #break since we are looking for the last long unshortened uri with/without a path redirect
                    break
        else:
            longUrl = url

    except Exception as e:
        #Part B: returns the lasts good url if the last response is not a 200.

        if( secondTryFlag ):
            logger.info('\texpandUrl(): second try: ' + url)
            longUrl = expandURLSecondTry(url)
        else:
            longUrl = url

    return longUrl

def expandURLSecondTry(url, curIter=0, maxIter=100):

    '''
    Attempt to get first good location. For defunct urls with previous past
    '''

    url = url.strip()
    if( len(url) == 0 ):
        return ''

    if( maxIter % 10 == 0 ):
        logger.info('\t' + str(maxIter) + ' expandURLSecondTry(): url - ' + url)

    if( curIter>maxIter ):
        return url

    try:

        # when using find, use outputLowercase
        # when indexing, use output
        
        output = check_output(['curl', '-s', '-I', '-m', '10', url])
        output = output.decode('utf-8')
        
        outputLowercase = output.lower()
        indexOfLocation = outputLowercase.rfind('\nlocation:')

        if( indexOfLocation != -1 ):
            # indexOfLocation + 1: skip initial newline preceding location:
            indexOfNewLineAfterLocation = outputLowercase.find('\n', indexOfLocation + 1)
            redirectUrl = output[indexOfLocation:indexOfNewLineAfterLocation]
            redirectUrl = redirectUrl.split(' ')[1]

            return expandURLSecondTry(redirectUrl, curIter+1, maxIter)
        else:
            return url

    except:
        genericErrorInfo( '\n\terror url: ' + url )
    
    return url

def expandURLs(urisLstDct, uriKey='url', **kwargs):
    
    kwargs.setdefault('shortURLTest', True)
    kwargs.setdefault('verbose', False)

    if( kwargs['verbose'] is True ):
        logger.info('\nexpandURLs():, shortURLTest:', kwargs['shortURLTest'])

    if( len(urisLstDct) == 0 ):
        return []

    uriMap = {}
    urisLst = []

    if( isinstance(urisLstDct[0], dict) ):
        isDict = True
    else:
        isDict = False

    for i in range(len(urisLstDct)):

        if( isDict ):
            uri = urisLstDct[i][uriKey]
        else:
            uri = urisLstDct[i]
        
        if( kwargs['shortURLTest'] is True ):
            if( naiveIsURIShort(uri) is False ):
                continue

        uriMap[uri] = i 
        urisLst.append(uri)

    
    expandedURIs = expandURLsWorker(urisLst, kwargs=kwargs)
    for i in range(len(expandedURIs)):
        
        #entries in urisLst and expandedURIs are pairs, so
        #get location of original short uri 
        originalURI = urisLst[i]
        indx = uriMap[originalURI]

        if( isDict ):
            urisLstDct[indx]['long_url'] = expandedURIs[i]
        else:
            urisLstDct[indx] = expandedURIs[i]

    return urisLstDct

def expandURLsWorker(urisLst, **kwargs):

    kwargs.setdefault('printMod', 10)

    if( len(urisLst) == 0 ):
        return []

    jobsLst = []
    size = str(len(urisLst))
    for i in range(int(size)):

        printMsg = ''
        if( i % kwargs['printMod'] == 0 ):
            printMsg = '\n\texpandURLs(): ' + str(i) + ' of ' + size + ': ' + urisLst[i]
        
        jobsLst.append( {
            'func': expandURL, 
            'args': {'url': urisLst[i]}, 
            'misc': False, 
            'print': printMsg
        })

    resLst = parallelTask(jobsLst)
    expandedURIs = []
    
    for res in resLst:
        expandedURIs.append(res['output'])

    return  expandedURIs
#uri/html proc - end

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
        genericErrorInfo()
        return []

    return resLst
#parallel proc - end

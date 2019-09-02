# NwalaTextUtils

Collection of text processing Python functions.
## Dependency & Installation Options
### Dependency

* [misja python-boilerpipe](https://github.com/misja/python-boilerpipe/) OR
* [boilerpipe3](https://github.com/slaveofcode/boilerpipe3)

### Installation after installing boilerpipe dependency
```
$ pip install NwalaTextUtils
```
OR
```
$ git clone https://github.com/oduwsdl/NwalaTextUtils.git
$ cd NwalaTextUtils/; pip install .; cd ..; rm -rf NwalaTextUtils;
```
### Installation within Python virtual environment within Docker container
```
$ docker run -it --rm -v "$PWD":/usr/src/myapp -w /usr/src/myapp openkbs/jdk-mvn-py3 bash
$ virtualenv -p python3 penv
$ source penv/bin/activate
$ pip install boilerpipe3
$ pip install NwalaTextUtils
```

## Function Documentation and Usage Examples

### Dereference URI with `derefURI(uri, sleepSec=0, params=None)`: 
Returns HTML text from `uri`. Set `sleepSec` (sleep seconds) > 0 to throttle (sleep) request.
Dictionary `params` options:

* (bool) `addResponseHeader`: Default = False. False - returns only HTML text payload. True - returns dict containing HTML text and Server response headers.

* (dict) `headers`: Default = [getCustomHeaderDict()](https://github.com/oduwsdl/NwalaTextUtils/blob/logfixes/NwalaTextUtils/textutils.py#L69). User-supplied HTTP Request headers.

* (dict) `loggerDets`: Default = {}. Specifies log options. To switch on console logs, set `params['loggerDets']` as follows
	```
	params = {
		'loggerDets':{		
			'level': logging.INFO,
		}
	}
	```

	To write log to file, set `params['loggerDets']['file']`, e.g.,
	```
	params['loggerDets']['file'] = '/path/to/logs.log'
	```

	To use custom log format set `params['loggerDets']['format']`, e.g.,
	```
	params['loggerDets']['format'] = '%(asctime)s * %(name)s * %(levelname)s * %(message)s'
	```
* (int)  `sizeRestrict`: Default = 4,000,000 (~4 MB). Maximum size of HTML payload. If Content-Length exceeds this size, content would be discarded.

* (int)  `timeout`: Default = 10, Argument passed to [timeout to requests.get](https://2.python-requests.org/en/master/user/quickstart/#timeouts)

### Remove boilerplate from HTML with `cleanHtml(html, method='python-boilerpipe')`:
Returns plaintext after removing HTML boilerplate from `html` using either the default [recommended](https://ws-dl.blogspot.com/2017/03/2017-03-20-survey-of-5-boilerplate.html) boilerplate removal method, `python-boilerpipe` or [NLTK's regex method](https://github.com/nltk/nltk/commit/39a303e5ddc4cdb1a0b00a3be426239b1c24c8bb).

### Extract HTML Page title with `getPgTitleFrmHTML(html)`:
Returns text from within HTML title tag.

### Usage example of `derefURI()`, `cleanHtml()`, and `getPgTitleFrmHTML()`:
```
from NwalaTextUtils.textutils import derefURI
from NwalaTextUtils.textutils import cleanHtml
from NwalaTextUtils.textutils import getPgTitleFrmHTML

uri = 'https://time.com/3505982/ebola-new-cases-world-health-organization/'

html = derefURI(uri, 0)
plaintext = cleanHtml(html)
title = getPgTitleFrmHTML(html)

print('title:\n', title.strip(), '\n')
print('html prefix:\n', html[:100].strip(), '\n')
print('plaintext prefix:\n', plaintext[:100].strip(), '\n')
```

### Dereference and Remove Boilerplate from URIs with `prlGetTxtFrmURIs(urisLst, params=None)`:
Dereference and remove boilerplate from URIs (within `urisLst`) in parallel. `params` activates more functionalities such a activating and controlling the console logging details (see [`loggerDets`](#dereference-uri-with-derefuriuri-sleepsec0-paramsnone) above). You might need status updates (instead of the default silence) when dereferencing a large list of URIs. To control how often the log is printed, set `params['loggerDets']['updateRate']`, e.g.,

```
params['loggerDets']['updateRate'] = 10 #print 1 message per 10 log status updates
```

Usage example:
```
import json
import logging
from NwalaTextUtils.textutils import prlGetTxtFrmURIs

uris_lst = [
    'http://www.euro.who.int/en/health-topics/emergencies/pages/news/news/2015/03/united-kingdom-is-declared-free-of-ebola-virus-disease',
    'https://time.com/3505982/ebola-new-cases-world-health-organization/',
    'https://www.scientificamerican.com/article/why-ebola-survivors-struggle-with-new-symptoms/'
  ]

params = {}
'''
#To print console logs, set params accordingly:
params = { 
	'loggerDets': {'level': logging.INFO} 
}
'''

doc_lst = prlGetTxtFrmURIs(uris_lst, params=params)
with open('doc_lst.json', 'w') as outfile:
    json.dump(doc_lst, outfile)
```

Sample output of `prlGetTxtFrmURIs()`:
```
{
	'text': 'WHO commends the United Kingdom of Great Britain and Northern...',
	'title': 'United Kingdom is declared free of Ebola virus disease',
	'uri': 'http://www.euro.who.int/en/health-topics/emergencies/pages/news/news/2015/03/united-kingdom-is-declared-free-of-ebola-virus-disease'
}
```

### Dereference and remove Boilerplate from files with `prlGetTxtFrmFiles(folder, rmHtml=False)`:
This function is similar to `prlGetTxtFrmURIs()`, but instead of dereferencing and removing boilerplate from a list of URIs like `prlGetTxtFrmURIs()` does, `prlGetTxtFrmFiles()` processes a `folder` containing HTML or plaintext files. Since `rmHtml = False` by default, the function simple reads and returns plaintext files. If `rmHtml = True`, `prlGetTxtFrmFiles()` removes boilerplate (via `cleanHtml()`) from the HTML files. In summary, if the `folder` contains HTML files, set `rmHtml = True`, if `folder` contains plaintext, set `rmHtml = False`.

### Parallelize function with `parallelTask(jobsLst, threadCount=5)`:
Given a list of jobs and data specified by `jobsLst`, this function executes jobs in parallel using `threadCount` threads. For example `prlGetTxtFrmURIs()` used `parallelTask()` to parallelize dereferencing URIs (`derefURI()`). Here's a snippet from `prlGetTxtFrmURIs()` with associated inline explanation.

```
docsLst = []
size = len(urisLst)

#<BLOCKS OF CODE NOT PERTINENT TO THE EXPLANATION OF parallelTask() HAVE BEEN DELETED FOR BREVITY>

#list containing function to be parallelized and arguments to be passed to function
jobsLst = []

for i in range(size):

	printMsg = ''

	if( i % 10 == 0 ):
		printMsg = 'dereferencing uri i: ' + str(i) + ' of ' + str(size)

	#keywords is a dictionary specifying arguments to be passed to derefURI()
	#the keys of keywords (uri & sleepSec) match the parameter signature of derefURI(uri, sleepSec)
	keywords = {
		'uri': urisLst[i],
		'sleepSec': 0
	}

	#jobsLst contains pool of data to be processed in parallel by func (derefURI())
	jobsLst.append({
		'func': derefURI, # function to be parallelized
		'args': keywords, # arguments to pass to function
		'misc': False,    # data to send back after processing this keywords input
		'print': printMsg # optional message to print when processing this request, set blank if print not required
	})

#Function call to start parallel processing, resLst contains data 
#returned by func (derefURI) after processing each argument, len(resLst) = len(jobsLst)
resLst = parallelTask(jobsLst)

for res in resLst:
	
	res['input'] 	# input data send to func (derefURI())
	res['output']	# output (HTML text) returned by func (derefURI()) after processing input, None if func does not return
	res['misc']  	# echo-back data by user

	docsLst.append({
		'text': cleanHTML( res['output'] ),
		'title': getPgTitleFrmHTML( res['output'] ),
		'uri': res['input']['args']['uri']
	})

return docsLst
```
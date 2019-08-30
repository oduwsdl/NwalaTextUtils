# NwalaTextUtils

Collection of text processing Python functions.
## Dependency & Installation
### Dependency

* [misja python-boilerpipe](https://github.com/misja/python-boilerpipe/) OR
* [boilerpipe3](https://github.com/slaveofcode/boilerpipe3)

### Installation (After installing dependency)
```
$ pip install NwalaTextUtils
```
OR
```
$ git clone https://github.com/oduwsdl/NwalaTextUtils.git
$ cd NwalaTextUtils/; pip install .; cd ..; rm -rf NwalaTextUtils;
```
### Installation inside Docker container
```
$ docker run -it --rm -v "$PWD":/usr/src/myapp -w /usr/src/myapp openkbs/jdk-mvn-py3 bash
$ virtualenv -p python3 penv
$ source penv/bin/activate
$ pip install boilerpipe3
$ pip install NwalaTextUtils
```

## Usage Examples
### Dereference and Remove Boilerplate from URIs:
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
	#to switch on console logs, set params['loggerDets'] as follows
	params = {
		'loggerDets':{		
			'level': logging.INFO,
		}
	}

	#to write log to file, set params['loggerDets']['file'], e.g.,
	params['loggerDets']['file'] = '/path/to/logs.log'

	#to use custom log format set params['loggerDets']['format'], e.g.,
	params['loggerDets']['format'] = '%(asctime)s * %(name)s * %(levelname)s * %(message)s'
'''

doc_lst = prlGetTxtFrmURIs(uris_lst, params=params)
with open('doc_lst.json', 'w') as outfile:
    json.dump(doc_lst, outfile)
```
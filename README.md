# NwalaTextUtils

Collection of text processing Python functions.
## Installation
### Stable
```
$ pip install NwalaTextUtils
```
### Dev.
```
$ git clone https://github.com/oduwsdl/NwalaTextUtils.git
$ cd NwalaTextUtils/
$ pip install .
```

## Usage Examples
### Dereference and Remove Boilerplate from URIs:
```
import json
from NwalaTextUtils.textutils import prlGetTxtFrmURIs

uris_lst = [
    'http://www.euro.who.int/en/health-topics/emergencies/pages/news/news/2015/03/united-kingdom-is-declared-free-of-ebola-virus-disease',
    'https://time.com/3505982/ebola-new-cases-world-health-organization/',
    'https://www.scientificamerican.com/article/why-ebola-survivors-struggle-with-new-symptoms/'
  ]

doc_lst = prlGetTxtFrmURIs(uris_lst)
with open('doc_lst.json', 'w') as outfile:
    json.dump(doc_lst, outfile)
```
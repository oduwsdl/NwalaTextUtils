import unittest

from NwalaTextUtils.textutils import cleanHtml
from NwalaTextUtils.textutils import derefURI
from NwalaTextUtils.textutils import expandURL
from NwalaTextUtils.textutils import expandURLs
from NwalaTextUtils.textutils import getPgTitleFrmHTML
from NwalaTextUtils.textutils import parallelGetTxtFrmURIs

class TestTextutils(unittest.TestCase):
    
    def test_deref_boilrm_title(self):

        uri = 'https://time.com/3505982/ebola-new-cases-world-health-organization/'

        html = derefURI(uri, 0)
        plaintext = cleanHtml(html)
        title = getPgTitleFrmHTML(html)

        self.assertGreater( len(html), 1000, "html.len < 1000" )
        self.assertGreater( len(plaintext), 1000, "plaintext.len < 1000" )
        self.assertGreater( len(title), 10, "title.len < 10" )

        '''
            print( 'title:', title.strip() )
            print( 'html prefix (' + str(len(html)) + ' chars):', html[:11].strip() )
            print( 'plaintext prefix (' + str(len(plaintext)) + ' chars)', plaintext[:21].strip() )
        '''

    def test_deref_boilrm_title_prl(self):

        uris_lst = [
            'http://www.euro.who.int/en/health-topics/emergencies/pages/news/news/2015/03/united-kingdom-is-declared-free-of-ebola-virus-disease',
            'https://time.com/3505982/ebola-new-cases-world-health-organization/',
            'https://www.scientificamerican.com/article/why-ebola-survivors-struggle-with-new-symptoms/'
        ]

        doc_lst = parallelGetTxtFrmURIs(uris_lst)
        self.assertEqual( len(doc_lst), 3, "doc_lst.len != 3" )

        for d in doc_lst:
            self.assertGreater( len(d['text']), 1000, "text.len < 1000" )
            self.assertGreater( len(d['uri']), 10, "uri.len < 1000" )
            self.assertGreater( len(d['title']), 10, "title.len < 10" )

    def test_expand_url_single(self):

        short_u = 'https://t.co/OfAQRC1Opd?amp=1'
        long_u = expandURL(short_u)
        key = 'https://towardsdatascience.com/how-you-should-read-research-papers-according-to-andrew-ng-stanford-deep-learning-lectures-98ecbd3ccfb3'

        self.assertEqual( long_u, key, "long_u != key" )

    def test_expand_url_multiple(self):

        uris_lst = [
            'https://t.co/OfAQRC1Opd?amp=1',
            'https://t.co/uqJhpqpUcl?amp=1'
        ]

        url_keys = [
            'https://towardsdatascience.com/how-you-should-read-research-papers-according-to-andrew-ng-stanford-deep-learning-lectures-98ecbd3ccfb3',
            'https://www.theguardian.com/us-news/2015/dec/15/michigan-mayor-declares-manmade-disaster-lead-tainted-water-supply'
        ]

        res = expandURLs(uris_lst)
        for i in range( len(res) ):
            long_u = res[i]
            self.assertEqual( long_u, url_keys[i], "long_u != key" )



        uris_lst = [
            {'url': 'https://t.co/OfAQRC1Opd?amp=1'},
            {'url': 'https://t.co/uqJhpqpUcl?amp=1'}
        ]

        res = expandURLs(uris_lst)
        for i in range( len(res) ):
            
            long_u = res[i]['long_url']
            self.assertEqual( long_u, url_keys[i], "long_u != key" )

if __name__ == '__main__':
    unittest.main()
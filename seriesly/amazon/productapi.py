# Copyright (C) 2009 Sebastian Rahlf <basti at redtoad dot de>
#
# This program is release under the BSD License. You can find the full text of
# the license in the LICENSE file.
# Adapted by Stefan Wehrmeyer to fit my and GAE's needs

"""
Amazon Product Advertising API
==============================

    The Product Advertising API provides programmatic access to Amazon's
    product selection and discovery functionality so that developers like you
    can advertise Amazon products to monetize your website.
    
    The Product Advertising API helps you advertise Amazon products using
    product search and look up capability, product information and features
    such as Customer Reviews, Similar Products, Wish Lists and New and Used
    listings. You can make money using the Product Advertising API to advertise
    Amazon products in conjunction with the Amazon Associates program. Be sure
    to join the Amazon Associates program to earn up to 15% in referral fees
    when the users you refer to Amazon sites buy qualifying products.  

More info can be found at
https://affiliate-program.amazon.com/gp/advertising/api/detail/main.html

Requirements
------------

You need an Amazon Webservice account which comes with an access key and a 
secret key.

You'll also need the python module lxml (>=2.1.5) and, if you're using python 
2.4, also pycrypto.

License
-------

This program is release under the BSD License. You can find the full text of
the license in the LICENSE file.

"""

__version__ = '0.2.4.1'
__docformat__ = "restructuredtext en"

from base64 import b64encode
from datetime import datetime, timedelta

try: # make it python2.4 compatible!
    from hashlib import sha256
except ImportError: # pragma: no cover
    from Crypto.Hash import SHA256 as sha256
    
import hmac
import logging
import re
from time import strftime, gmtime
import urlparse
import urllib2
from xml.dom.minidom import parseString

from helper.http import get as http_get

LOCALES = {
    'ca' : 'http://ecs.amazonaws.ca/onca/xml', 
    'de' : 'http://ecs.amazonaws.de/onca/xml', 
    'fr' : 'http://ecs.amazonaws.fr/onca/xml', 
    'jp' : 'http://ecs.amazonaws.jp/onca/xml', 
    'uk' : 'http://ecs.amazonaws.co.uk/onca/xml', 
    'us' : 'http://ecs.amazonaws.com/onca/xml', 
}

class UnknownLocale (Exception):
    """
    Raised when unknown locale is specified.
    """
    
class AWSError (Exception):
    """
    Generic AWS error message.
    """
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
    def __str__(self): # pragma: no cover
        return '%(code)s: %(msg)s' % self.__dict__
    
class InvalidSearchIndex (Exception):
    """
    The value specified for SearchIndex is invalid. Valid values include:

    All, Apparel, Automotive, Baby, Beauty, Blended, Books, Classical, DVD,
    Electronics, ForeignBooks, HealthPersonalCare, HomeGarden, HomeImprovement,
    Jewelry, Kitchen, Magazines, MP3Downloads, Music, MusicTracks,
    OfficeProducts, OutdoorLiving, PCHardware, Photo, Shoes, Software,
    SoftwareVideoGames, SportingGoods, Tools, Toys, VHS, Video, VideoGames,
    Watches
    """
    
class InvalidResponseGroup (Exception):
    """
    The specified ResponseGroup parameter is invalid. Valid response groups for
    ItemLookup requests include:

    Accessories, AlternateVersions, BrowseNodes, Collections, EditorialReview,
    Images, ItemAttributes, ItemIds, Large, ListmaniaLists, Medium,
    MerchantItemAttributes, OfferFull, OfferListings, OfferSummary, Offers,
    PromotionDetails, PromotionSummary, PromotionalTag, RelatedItems, Request,
    Reviews, SalesRank, SearchBins, SearchInside, ShippingCharges,
    Similarities, Small, Subjects, Tags, TagsSummary, Tracks, VariationImages,
    VariationMatrix, VariationMinimum, VariationOffers, VariationSummary,
    Variations.
    """

class InvalidParameterValue (Exception):
    """
    The specified ItemId parameter is invalid. Please change this value and 
    retry your request.
    """

class InvalidListType (Exception):
    """
    The value you specified for ListType is invalid. Valid values include: 
    BabyRegistry, Listmania, WeddingRegistry, WishList.
    """
    
class NoSimilarityForASIN (Exception):
    """
    When you specify multiple items, it is possible for there to be no 
    intersection of similar items.
    """
    
class NoExactMatchesFound (Exception):
    """
    We did not find any matches for your request.
    """
    
class TooManyRequests (Exception):
    """
    You are submitting requests too quickly and your requests are being 
    throttled. If this is the case, you need to slow your request rate to one 
    request per second.
    """
    
class NotEnoughParameters (Exception):
    """
    Your request should have at least one parameter which you did not submit.
    """

class InvalidParameterCombination (Exception):
    """
    Your request contained a restricted parameter combination.
    """

DEFAULT_ERROR_REGS = {
    'invalid-value' : re.compile(
        'The value you specified for (?P<parameter>\w+) is invalid.'),

    'invalid-parameter-value' : re.compile(
        '(?P<value>.+?) is not a valid value for (?P<parameter>\w+). Please '
        'change this value and retry your request.'),

    'no-similarities' : re.compile(
        'There are no similar items for this ASIN: (?P<ASIN>\w+).'),

    'not-enough-parameters' : re.compile(
        'Your request should have atleast (?P<number>\d+) of the following '
        'parameters: (?P<parameters>[\w ,]+).'),

    'invalid-parameter-combination' : re.compile(
         'Your request contained a restricted parameter combination.'
         '\s*(?P<message>\w.*)$') # only the last bit is of interest here
}

JAPANESE_ERROR_REGS = {
    'invalid-value' : re.compile(
        u'(?P<parameter>\w+)\u306b\u6307\u5b9a\u3057\u305f\u5024\u306f\u7121'
        u'\u52b9\u3067\u3059\u3002'),

    'invalid-parameter-value' : re.compile(
        u'(?P<value>.+?)\u306f\u3001(?P<parameter>\w+)\u306e\u5024\u3068\u3057'
        u'\u3066\u7121\u52b9\u3067\u3059\u3002\u5024\u3092\u5909\u66f4\u3057'
        u'\u3066\u304b\u3089\u3001\u518d\u5ea6\u30ea\u30af\u30a8\u30b9\u30c8'
        u'\u3092\u5b9f\u884c\u3057\u3066\u304f\u3060\u3055\u3044\u3002'),

    'no-similarities' : re.compile(
        'There are no similar items for this ASIN: (?P<ASIN>\w+).'),

    'not-enough-parameters' : re.compile(
        u'\u6b21\u306e\u30d1\u30e9\u30e1\u30fc\u30bf\u306e\u3046\u3061\u3001'
        u'\u6700\u4f4e1\u500b\u304c\u30ea\u30af\u30a8\u30b9\u30c8\u306b\u542b'
        u'\u307e\u308c\u3066\u3044\u308b\u5fc5\u8981\u304c\u3042\u308a\u307e'
        u'\u3059\uff1a(?P<parameters>.+)$'),

    'invalid-parameter-combination' : re.compile('^(?P<message>.*)$'),
}

class API(object):
    
    """
    Wrapper class for the Amazon Product Advertising API. You will need both an 
    AWS access key id and the secret counterpart.
    
    Example::
    
        AWS_KEY = '...'
        SECRET_KEY = '...'
        
        api = ProductAdvertisingAPI(AWS_KEY, SECRET_KEY, 'us')
        root = api.item_lookup('9783836214063', IdType='ISBN', 
                    SearchIndex='Books', ResponseGroup='Reviews', ReviewPage=1)
        
        rating = root.Items.Item.CustomerReviews.AverageRating.pyval
        total_reviews = root.Items.Item.CustomerReviews.TotalReviews.pyval
        review_pages = root.Items.Item.CustomerReviews.TotalReviewPages.pyval
        
    It is possible to use a different module for parsing the XML response. For 
    instance, you can use ``xml.minidom`` instead of ``lxml`` by defining a
    custom result processor::
        
        def minidom_response_parser(fp):
            root = parse(fp)
            # parse errors
            for error in root.getElementsByTagName('Error'):
                code = error.getElementsByTagName('Code')[0].firstChild.nodeValue
                msg = error.getElementsByTagName('Message')[0].firstChild.nodeValue
                raise AWSError(code, msg)
            return root
        api = API(AWS_KEY, SECRET_KEY, processor=minidom_response_parser)
        root = api.item_lookup('0718155157')
        print root.toprettyxml()
        # ...
        
    Just make sure it raises an ``AWSError`` with the appropriate error code 
    and message.
    """
    
    VERSION = '2010-06-01' #: try out newest version supported Amazon API version
    REQUESTS_PER_SECOND = 1 #: max requests per second
    TIMEOUT = 5 #: timeout in seconds
    
    def __init__(self, access_key_id, secret_access_key, locale, 
                 processor=None):
        """
        :param access_key_id: AWS access key ID.
        :param secret_key_id: AWS secret key.
        :param locale: localise results by using one value from ``LOCALES``.
        :param processor: result processing function (``None`` if unsure).
        """
        self.access_key = access_key_id
        self.secret_key = secret_access_key
        
        try:
            parts = urlparse.urlsplit(LOCALES[locale])
            self.scheme, self.host, self.path = parts[:3]
            self.locale = locale
        except KeyError:
            raise UnknownLocale(locale)
        
        self.last_call = datetime(1970, 1, 1)
        self.throttle = timedelta(seconds=1)/self.REQUESTS_PER_SECOND
        self.debug = 0 # set to 1 if you want to see HTTP headers
        
        self.response_processor = processor
        self._parser = None # will be set first time _parse is run 
        
    def _build_url(self, **qargs):
        """
        Builds a signed URL for querying Amazon AWS.  This function is based
        on code by Adam Cox (found at
        http://blog.umlungu.co.uk/blog/2009/jul/12/pyaws-adding-request-authentication/)
        """
        # remove empty (=None) parameters
        for key, val in qargs.items():
            if val is None:
                del qargs[key]
        
        if 'AWSAccessKeyId' not in qargs:
            qargs['AWSAccessKeyId'] = self.access_key
            
        if 'Service' not in qargs:
            qargs['Service'] = 'AWSECommerceService'
            
        # use the version this class was build for by default
        if 'Version' not in qargs:
            qargs['Version'] = self.VERSION
            
        # add timestamp (this is required when using a signature)
        qargs['Timestamp'] = strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())
        
        # create signature
        keys = sorted(qargs.keys())
        args = '&'.join('%s=%s' % (key, urllib2.quote(str(qargs[key]))) 
                        for key in keys)
        
        msg = 'GET'
        msg += '\n' + self.host
        msg += '\n' + self.path
        msg += '\n' + args.encode('utf-8')
        
        signature = urllib2.quote(
            b64encode(hmac.new(self.secret_key, msg, sha256).digest()))
        
        url = '%s://%s%s?%s&Signature=%s' % (self.scheme, self.host, self.path, 
                                             args, signature)
        return url
    
    def _call(self, url):
        """
        Calls the Amazon Product Advertising API and objectifies the response.
        """ 
        return http_get(url)
    
    def _reg(self, key):
        """
        Returns the appropriate regular expression (compiled) to parse an error
        message depending on the current locale. 
        """
        if self.locale == 'jp':
            return JAPANESE_ERROR_REGS[key]
        return DEFAULT_ERROR_REGS[key]
    
    def _parse(self, fp):
        """
        Processes the AWS response (file like object). XML is fed in, some 
        usable output comes out. It will use a different result_processor if 
        you have defined one. 
        """
        if self.response_processor:
            return self.response_processor(fp)
        logging.warn(fp)
        dom = parseString(fp)
        items = dom.getElementsByTagName("Item")
        for item in items:
            url = item.getElementsByTagName("DetailPageURL")[0].firstChild.data
            attrs = item.getElementsByTagName("ItemAttributes")[0]
            title = attrs.getElementsByTagName("Title")[0].firstChild.data
            return url, title
        raise IOError
        
        # define custom class lookup first time this method is called which 
        # will hopefully reduce execution time (although it's lightning fast!) 
#         if self._parser is None:
#             
#             class SelectiveClassLookup(etree.CustomElementClassLookup):
#                 """
#                 Lookup mechanism for XML elements to ensure that ItemIds (such 
#                 as ASINs) are always StringElements and evaluated as such. 
#                 Thanks to Brian Browning for pointing this out.
#                 """
#                 def lookup(self, node_type, document, namespace, name):
#                     if name in ('ItemId', 'ASIN'):
#                         return objectify.StringElement
#                     
#             self._parser = etree.XMLParser()
#             lookup = SelectiveClassLookup()
#             lookup.set_fallback(objectify.ObjectifyElementClassLookup())
# #            lookup.set_fallback(etree.ElementNamespaceClassLookup(
# #                                    objectify.ObjectifyElementClassLookup()))
#             self._parser.set_element_class_lookup(lookup)
#         
#         tree = objectify.parse(fp, self._parser)
#         root = tree.getroot()
#         
#         #~ from lxml import etree
#         #~ print etree.tostring(tree, pretty_print=True)
#         
#         nspace = root.nsmap.get(None, '')
#         errors = root.xpath('//aws:Request/aws:Errors/aws:Error', 
#                          namespaces={'aws' : nspace})
#         
#         for error in errors:
#             
#             code = error.Code.text
#             msg = error.Message.text
#             
#             if code == 'AWS.ECommerceService.NoExactMatches':
#                 raise NoExactMatchesFound
#             
#             if code == 'AWS.InvalidParameterValue':
#                 m = self._reg('invalid-parameter-value').search(msg)
#                 raise InvalidParameterValue(m.group('parameter'), m.group('value'))
#             
#             if code == 'AWS.RestrictedParameterValueCombination':
#                 m = self._reg('invalid-parameter-combination').search(msg)
#                 raise InvalidParameterCombination(m.group('message'))
#             
#             raise AWSError(code, msg)
#         
#         #~ from lxml import etree
#         #~ print etree.tostring(root, pretty_print=True)
#         return root
    
    def item_lookup(self, id, **params):
        """
        Given an Item identifier, the ``ItemLookup`` operation returns some or
        all of the item attributes, depending on the response group specified
        in the request. By default, ``ItemLookup`` returns an item's ``ASIN``,
        ``DetailPageURL``, ``Manufacturer``, ``ProductGroup``, and ``Title`` of
        the item.
        
        ``ItemLookup`` supports many response groups, so you can retrieve many
        different kinds of product information, called item attributes,
        including product reviews, variations, similar products, pricing,
        availability, images of products, accessories, and other information.
        
        To look up more than one item at a time, separate the item identifiers
        by commas. 
        """
        try:
            url = self._build_url(Operation='ItemLookup', ItemId=id, **params)
            fp = self._call(url)
            return self._parse(fp)
        except AWSError, e:
            
            if (e.code=='AWS.InvalidEnumeratedParameter' 
            and self._reg('invalid-value').search(e.msg).group('parameter')=='SearchIndex'):
                raise InvalidSearchIndex(params.get('SearchIndex'))
            
            if e.code=='AWS.InvalidResponseGroup': 
                raise InvalidResponseGroup(params.get('ResponseGroup'))
            
            # otherwise re-raise exception
            raise # pragma: no cover
        
    def item_search(self, search_index, **params):
        """
        The ``ItemSearch`` operation returns items that satisfy the search
        criteria, including one or more search indices.

        ``ItemSearch`` returns up to ten search results at a time. When
        ``condition`` equals "All," ``ItemSearch`` returns up to three offers
        per condition (if they exist), for example, three new, three used,
        three refurbished, and three collectible items. Or, for example, if
        there are no collectible or refurbished offers, ``ItemSearch`` returns
        three new and three used offers.

        Because there are thousands of items in each search index,
        ``ItemSearch`` requires that you specify the value for at least one
        parameter in addition to a search index. The additional parameter value
        must reference items within the specified search index. For example,
        you might specify a browse node (BrowseNode is an ``ItemSearch``
        parameter), Harry Potter Books, within the Books product category. You
        would not get results, for example, if you specified the search index
        to be Automotive and the browse node to be Harry Potter Books. In this
        case, the parameter value is not associated with the search index
        value.

        The ``ItemPage`` parameter enables you to return a specified page of
        results. The maximum ``ItemPage`` number that can be returned is 400.
        An error is returned if you try to access higher numbered pages. If you
        do not include ``ItemPage`` in your request, the first page will be
        returned by default. There can be up to ten items per page.

        ``ItemSearch`` is the operation that is used most often in requests. In
        general, when trying to find an item for sale, you use this operation.
        """
        try:
            url = self._build_url(Operation='ItemSearch', 
                                  SearchIndex=search_index, **params)
            fp = self._call(url)
            return self._parse(fp)
        except AWSError, e:
            
            if (e.code=='AWS.InvalidEnumeratedParameter' 
            and self._reg('invalid-value').search(e.msg)):
                raise InvalidSearchIndex(search_index)
            
            if e.code=='AWS.InvalidResponseGroup': 
                raise InvalidResponseGroup(params.get('ResponseGroup'))
            
            # otherwise re-raise exception
            raise # pragma: no cover
        
    def similarity_lookup(self, *ids, **params):
        """
        The ``SimilarityLookup`` operation returns up to ten products per page
        that are similar to one or more items specified in the request. This
        operation is typically used to pique a customer's interest in buying
        something similar to what they've already ordered.

        If you specify more than one item, ``SimilarityLookup`` returns the
        intersection of similar items each item would return separately.
        Alternatively, you can use the ``SimilarityType`` parameter to return
        the union of items that are similar to any of the specified items. A
        maximum of ten similar items are returned; the operation does not
        return additional pages of similar items. If there are more than ten
        similar items, running the same request can result in different answers
        because the ten that are included in the response are picked randomly.
        The results are picked randomly only when you specify multiple items
        and the results include more than ten similar items. 
        """
        item_id = ','.join(ids)
        try:
            url = self._build_url(Operation='SimilarityLookup', 
                                  ItemId=item_id, **params)
            fp = self._call(url)
            return self._parse(fp)
        except AWSError, e:
            
            if e.code=='AWS.ECommerceService.NoSimilarities':
                asin = self._reg('no-similarities').search(e.msg).group('ASIN')
                raise NoSimilarityForASIN(asin)
            
    def list_lookup(self, list_id, list_type, **params):
        """
        The ListLookup operation returns, by default, summary information about
        a list that you specify in the request. The summary information
        includes the:

        - Creation date of the list
        - Name of the list's creator 
        
        The operation returns up to ten sets of summary information per page.

        Lists are specified by list type and list ID, which can be found using
        ListSearch.

        You cannot lookup more than one list at a time in a single request. You
        can, however, make a batch request to look for more than one list
        simultaneously. 

        The operation supports the following list types:

        - ``BabyRegistry`` - Baby registries contain items that expectant
          parents want. Gift givers can find baby registries created on Amazon
          or in Babies "R" Us or Toys "R" Us stores.
        - ``Listmania`` - Customers can create random groups of items, called
          Listmania lists. Listmania lists can be as specific ("Dorm Room
          Essentials for Every Freshman") or as general ("The Best Novels of
          2005") as customers choose.
        - ``WeddingRegistry`` - Wedding registries contain items that a wedding
          couple wants.
        - ``WishList`` - Wish lists contain items for birthdays, anniversaries
          or any other special day. These lists help others know what gifts the
          wishlist creator wants.  
        """
        try:
            url = self._build_url(Operation='ListLookup', ListId=list_id,
                                  ListType=list_type, **params)
            fp = self._call(url)
            return self._parse(fp)
        except AWSError, e:
            
            if (e.code=='AWS.InvalidEnumeratedParameter' 
            and self._reg('invalid-value').search(e.msg).group('parameter')=='ListType'):
                raise InvalidListType(params.get('ListType'))
            
            # otherwise re-raise exception
            raise # pragma: no cover
    
    def list_search(self, list_type, **params):
        """
        Given a customer name or e-mail address, the ``ListSearch`` operation
        returns the associated list ID(s) but not the list items. To find
        those, use the list ID returned by ``ListSearch`` with ``ListLookup``.
        
        Specifying a full name or just a first or last name in the request
        typically returns multiple lists belonging to different people. Using
        e-mail as the identifier produces more filtered results.
        
        For ``Wishlists`` and ``WeddingRegistry`` list types, you must specify 
        one or more of the following parameters:
        
        - e-mail 
        - FirstName 
        - LastName 
        - Name 
        
        For the ``BabyRegistry`` list type, you must specify one or more of the
        following parameters:
        
        - FirstName 
        - LastName 
        
        You cannot, for example, retrieve a ``BabyRegistry`` by specifying an
        e-mail address or Name. 
        """
        try:
            url = self._build_url(Operation='ListSearch', 
                                  ListType=list_type, **params)
            fp = self._call(url)
            return self._parse(fp)
        except AWSError, e:
            
            if (e.code=='AWS.InvalidEnumeratedParameter' 
            and self._reg('invalid-value').search(e.msg).group('parameter')=='ListType'):
                raise InvalidListType(list_type)
            
            if e.code=='AWS.MinimumParameterRequirement': 
                p = self._reg('not-enough-parameters').search(e.msg).group('parameters')
                raise NotEnoughParameters(p)
            
            if e.code=='AWS.ECommerceService.NoExactMatches': 
                raise NoExactMatchesFound
            
            # otherwise re-raise exception
            raise # pragma: no cover
        
    def help(self, about, help_type, response_group=None, **params):
        """
        The Help operation provides information about Product Advertising API
        operations and response groups. For operations, Help lists required
        and optional request parameters, as well as default and optional
        response groups the operation can use. For response groups, Help lists
        the operations that can use the response group as well as the response
        tags returned by the response group in the XML response.
        
        The Help operation is not often used in customer applications. It can,
        however, be used to help the developer in the following ways:
        
        * Provide contextual help in an interactive development environment
          (IDE) for developers
        * Automate documentation creation as part of a developer's toolkit.
        
        :param about: Specifies the operation or response group about which
          you want more information. All Product Advertising API operations, all
          Product Advertising API response groups
        :param help_type: Specifies whether the help topic is an operation or
          response group. HelpType and About values must both be operations or
          response groups, not a mixture of the two. 
          Valid Values: ``Operation``, ``ResponseGroup``
        :param response_group: Specifies the types of values to return. You
          can specify multiple response groups in one request by separating them
          with commas.
        """
        try:
            url = self._build_url(Operation='Help', About=about, 
                    HelpType=help_type, ResponseGroup=response_group, **params)
            fp = self._call(url)
            return self._parse(fp)
        except AWSError, e:
            
            m = self._reg('invalid-value').search(e.msg)
            if e.code=='AWS.InvalidEnumeratedParameter': 
                raise ValueError(m.group('parameter'))
                        
            # otherwise re-raise exception
            raise # pragma: no cover
        
    def browse_node_lookup(self, browse_node_id, response_group=None, **params):
        """
        Given a browse node ID, ``BrowseNodeLookup`` returns the specified
        browse node's name, children, and ancestors. The names and browse node
        IDs of the children and ancestor browse nodes are also returned.
        ``BrowseNodeLookup`` enables you to traverse the browse node hierarchy
        to find a browse node.
        
        As you traverse down the hierarchy, you refine your search and limit
        the number of items returned. For example, you might traverse the
        following hierarchy: ``DVD>Used DVDs>Kids and Family``, to select out
        of all the DVDs offered by Amazon only those that are appropriate for
        family viewing. Returning the items associated with ``Kids and Family``
        produces a much more targeted result than a search based at the level
        of ``Used DVDs``.
        
        Alternatively, by traversing up the browse node tree, you can
        determine the root category of an item. You might do that, for
        example, to return the top seller of the root product category using
        the ``TopSeller`` response group in an ``ItemSearch`` request.
        
        You can use ``BrowseNodeLookup`` iteratively to navigate through the
        browse node hierarchy to reach the node that most appropriately suits
        your search. Then you can use the browse node ID in an ItemSearch
        request. This response would be far more targeted than, for example,
        searching through all of the browse nodes in a search index.
        
        :param browse_node_id: A positive integer assigned by Amazon that 
          uniquely identifies a product category. 
          Default: None
          Valid Values: A positive integer.
        :type browse_node_id: str
        :param response_group: Specifies the types of values to return. You can 
          specify multiple response groups in one request by separating them 
          with commas.
          Default: ``BrowseNodeInfo``
          Valid Values: ``MostGifted``, ``NewReleases``, ``MostWishedFor``, 
          ``TopSellers`` 
        """
        try:
            url = self._build_url(Operation='BrowseNodeLookup', 
                    BrowseNodeId=browse_node_id, ResponseGroup=response_group, 
                    **params)
            fp = self._call(url)
            return self._parse(fp)
        except AWSError, e:
            
            if e.code=='AWS.InvalidResponseGroup':
                raise InvalidResponseGroup(params.get('ResponseGroup'))
            
            # otherwise re-raise exception
            raise # pragma: no cover
        
        
class ResultPaginator (object):
    
    """
    Wrapper class for paginated results. This class will call the passed 
    function iteratively until either the specified limit is reached or all 
    result pages are fetched.
    
    A small example fetching reviews for a book::
        
        api = API(AWS_KEY, SECRET_KEY)
        paginator = ResultPaginator('ReviewPage',
            '//aws:Items/aws:Request/aws:ItemLookupRequest/aws:ReviewPage',
            '//aws:Items/aws:Item/aws:CustomerReviews/aws:TotalReviewPages',
            '//aws:Items/aws:Item/aws:CustomerReviews/aws:TotalReviews')
        
        for root in paginator(api.item_lookup, id=isbn, IdType='ISBN', 
                             SearchIndex='Books', ResponseGroup='Reviews'):
            ...
    
    .. note: All three XPath expressions have to return integer values for the 
       pagination to work!
    """
    
    def __init__(self, counter, current_page, total_pages, total_results, 
                 limit=None, nspace=None):
        """
        :param counter: counter variable passed to AWS.
        :param current_page: XPath expression locating current paginator page.
        :param total_pages: XPath expression locating total number of pages.
        :param total_results: XPath expression locating total number of results. 
        :param limit: limit fetched pages to this amount. 
        :param nspace: used XML name space. 
        """
        self.counter = counter
        self.current_page_xpath = current_page
        self.total_pages_xpath = total_pages
        self.total_results_xpath = total_results
        
        self.limit = limit
        self.nspace = nspace
        
    def __call__(self, fun, *args, **kwargs):
        """
        Iterate over all paginated results of ``fun``.
        """
        current_page = 0
        total_pages = 1
        
        kwargs[self.counter] = kwargs.get(self.counter, 1)
        
        while (current_page < total_pages 
        and (self.limit is None or current_page < self.limit)):
            
            root = fun(*args, **kwargs)
            
            if self.nspace is None:
                self.nspace = root.nsmap.get(None, '')
            
            current_page = self._get_current_page_numer(root)
            total_results = self._get_total_results(root)
            total_pages = self._get_total_page_numer(root)
            
            yield root
            
            kwargs[self.counter] += 1
            
    def _get_total_page_numer(self, root):
        """
        Get total number of paginator pages.
        """
        try:
            node = root.xpath(self.total_pages_xpath, 
                          namespaces={'aws' : self.nspace})[0]
            return node.pyval
        except AttributeError:
            # node has no attribute pyval so it better be a number
            return int(node)
        except IndexError:
            return 0
        
    def _get_current_page_numer(self, root):
        """
        Get number of current paginator page. If it cannot be extracted, it is 
        probably the first.
        """
        try:
            node = root.xpath(self.current_page_xpath, 
                          namespaces={'aws' : self.nspace})[0]
            return node.pyval
        except AttributeError:
            # node has no attribute pyval so it better be a number
            return int(node)
        except IndexError:
            return 1
    
    def _get_total_results(self, root):
        """
        Get total number of results.
        """
        try:
            node = root.xpath(self.total_results_xpath, 
                          namespaces={'aws' : self.nspace})[0]
            return node.pyval
        except AttributeError:
            # node has no attribute pyval so it better be a number
            return int(node)
        except IndexError:
            return 0


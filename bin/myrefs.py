import re,lxml
from lxml import etree,objectify

import hubconfig
from deliverance.util.proxyrequest import Request, Response
from deliverance.exceptions import AbortProxy

def modify_blog_response(request, response, orig_base, proxied_base, proxied_url, log):
    # orig_base: the original URL base: http://localhost:8080/trac
    # proxied_base: where dest sent it to: http://localhost:10001/
    # proxied_url: the full destination, e.g.,
    #    http://localhost:10001/view/1
    # request.url: the full original URL, e.g.,
    #    http://localhost:8080/trac/view/1
    body = response.body
    body = body.replace("oldonload856330(); form856330Load();",
                                         "\noldonload856330();\n form856330Load();")
    #pat = re.compile(r'<div class="sidebar-div">.*?<img src="http://www.formspring.com/forms/.*</div>',re.S)
    #body = pat.sub(r'',body)
    body = body.replace('text_small','')
    if orig_base.endswith('/'):
        orig_base = orig_base[:-1]
    body = body.replace(orig_base,hubconfig.blog['bayarea']['rightcolum_linkbase'])
    #import pdb; pdb.set_trace()
    response.body = body
    return response 



def get_blog(src,path_name,request,orig_base,log):
    import urllib, urllib2,time
    headers = request.headers
    headers['hs-dest'] = src
    
    full_path = request.path_info #which one to use, path_info, path_qs,...?
    parts = full_path.split('/')
    subpath = '/'.join(parts[parts.index(path_name)+1:])
    
    proxybase = hubconfig.blogsproxy
    if proxybase.endswith('/'):
        proxybase = proxybase[:-1]
    
    url = proxybase+'/'+subpath

    #import pdb; pdb.set_trace()
    if request.POST.items():
        vars = request.POST.items()
        data = urllib.urlencode(vars)
        req = urllib2.Request(url, data, headers)
    else:
        url = '%s?%s' % (url,request.query_string)
        req = urllib2.Request(url,headers=headers)
    start = time.time()
    response = urllib2.urlopen(req)
    #raise "Request to %s needed %s" % (url,time.time() - start)
    localbase = orig_base + '/'.join(parts[:parts.index(path_name)+1][1:])
    body = response.read()
    body = body.replace(proxybase,localbase)
    #import pdb; pdb.set_trace()
    return (response,body)



def modify_main_response(request, response, orig_base, proxied_base, proxied_url, log):
    # orig_base: the original URL base: http://localhost:8080/trac
    # proxied_base: where dest sent it to: http://localhost:10001/
    # proxied_url: the full destination, e.g.,
    #    http://localhost:10001/view/1
    # request.url: the full original URL, e.g.,
    #    http://localhost:8080/trac/view/1


    #there could be a blog tag embedded in the page. See microSitesBlog2.kid. 
    #The tag contains the url to the blog and the path_name of the microsite
    #page, to handle subpages being requested from the blog object - without
    #that info we would not know where to start looking for subpages.

    #XXX True? If the pages are named foo__blog, its always the first part
    #of the query
    #import pdb; pdb.set_trace()
    pattern = '<blog src="([^"].*)" blog2path="([^"].*)".*>.*</blog>'
    result = re.findall(pattern,response.body)
    if result:
        #import pdb; pdb.set_trace()
        src = result[0][0]
        path_name = result[0][1]
        if src != request.url:
            #sr = subresponse
            sr,blogcontent = get_blog(src,path_name,request,orig_base,log)
            if sr.headers['Content-Type'].split('/')[0] in ['text']:
                response.body = re.sub(pattern,blogcontent,response.body)
            else:                
                response.headers = dict(sr.headers.items())
                response.body = blogcontent
    return response 


def get_blogs_destination(request, log):
    #import pdb; pdb.set_trace()
    if hasattr(request,'orig_response'):
        orig_response = request.orig_response
        body = orig_response.body
        parsed = parseBlogSource(body)
        #import pdb; pdb.set_trace()
        if parsed:
            src,path_name = parsed
            return src
        else:
            raise AbortProxy
    return hubconfig.blogdefault['rightcolumn']


def get_main_destination(request,log):
    #import pdb; pdb.set_trace()
    if request.script_name:
        raise AbortProxy
    return 'http://hubspacedev.the-hub.net'


def modify_proxy_request(request, log):
    #import pdb; pdb.set_trace()
    return request


def parseBlogSource(body):
    import re 
    pattern = '<blog src="([^"].*)" blog2path="([^"].*)".*>.*</blog>'
    result = re.findall(pattern,body)
    if result:
        src = result[0][0]
        path_name = result[0][1]
        return (src,path_name)
    else:
        return None

def modify_blog_request(request, log):
    #import pdb; pdb.set_trace()
    import re
    if request.environ.has_key('deliverance.subrequest_original_request'):
        if 1:
            orig_request = request.environ['deliverance.subrequest_original_request']
            orig_response = orig_request.orig_response
            parsed = parseBlogSource(orig_response.body)
            if parsed:
                #import pdb; pdb.set_trace()
                
                src,path_name = parsed
                full_path = orig_request.path_info #which one to use, path_info, path_qs,...?
                parts = full_path.split('/')
                subpath = '/'.join(parts[parts.index(path_name)+1:])
                #proxypath = request.
                #if proxypath.endswith('/'):
                #    proxypath = proxybase[:-1]
                #newpath = proxypath+'/'+subpath
                if subpath and not subpath.startswith('/'):
                    subpath = '/'+subpath
                env = orig_request.environ.copy()
                #env['SCRIPT_NAME']=request.environ['SCRIPT_NAME']
                env['PATH_INFO']=subpath
                request = Request(env)
                
    return request

def match_notheme(req, resp, headers, *args):
    if resp.headers['Content-Type'] in ['text/html']:
        return False
    else:
        return True

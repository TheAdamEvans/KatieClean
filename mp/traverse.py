import re
import json
import urllib2
import sys
import bs4

def parse_dest(html):

    # finds a long digit
    idRE = re.compile(r"1(\d)(\d)(\d)+")
    if idRE.search(html) != None:
        page_index = idRE.search(html).group(0)

    # finds something in between >  <
    # BAD *$&@%$*&% will breka this
    labelRE = re.compile(r">[0-9A-z \'()-/]+<")
    if labelRE.search(html) != None:
        page_label = labelRE.search(html).group(0)
        page_label = page_label[1:-1]
    
    if 'page_index' in locals() and 'page_label' in locals():
        # url = 'http://www.mountainproject.com/v/' + page_index

        # TODO package back should be JSON
        return page_index, page_label #, url
    else:
        return None

def find_dest_iter(page_id, mp_html):

    soup = bs4.BeautifulSoup(mp_html, 'html.parser')
    
    if page_id == '': # TODO move this to be the last case
        dest_iter = [str(s) for s in soup.find_all('span') if re.search("destArea",str(s)) != None]
    elif re.search("leftNavRoutes", mp_html) != None:
        t = str(soup.find(id="leftNavRoutes"))
        dest_iter = t.split("</td><td>")
    elif re.search('leftnavfilternote(.*)',mp_html) != None: # TODO Use beautiful soup
        nav_start = re.search('leftnavfilternote(.*)',mp_html).end()
        nav_end = re.search('(.*)LeftNavDynamicContent',mp_html).start()
        nav_html = mp_html[nav_start:nav_end]

        # break out location rows
        TRIM = 26
        dest_iter = nav_html[TRIM:].split('<br/>')
    else:
        dest_iter = None
    return dest_iter

def get_children(page_id):
    
    url = 'http://www.mountainproject.com/v/' + str(page_id)
    
    try:
        mp_page = urllib2.urlopen(url)
    except:
        return None
    else:
        mp_html = mp_page.read()
        soup = bs4.BeautifulSoup(mp_html, 'html.parser')
        
        website_tree = {}

        y = soup.find(id="youContainer")
        is_route = re.search('You & This Route',y.get_text()) != None

        if is_route:
            return None
        else:

            dest_iter = find_dest_iter(page_id, mp_html)
            
            if dest_iter != None:
                for dest in dest_iter:
                    features = parse_dest(dest)

                    if features != None:
                        page_index, page_label = features
                        # print page_label + " " + page_index
                        data = { 'page_id':page_index, 'label':page_label }
                        website_tree[page_index] = data
                    else: # some bullshit
                        if re.search('leftnav',dest) == None: 
                            print dest # see if labelRE is missing anything
        
            c = { 'pageID':page_id }
            c['children_info'] = website_tree
            route_list = [c['children_info'][route]['page_id'] for route in c['children_info']]
            c['children'] = route_list

            return route_list

def get_route_name(soup):

    route_name = soup.h1.get_text().replace(u'\xa0', '')
    return { 'Name': route_name }


def get_box_data(soup):
    page_table = soup.find_all('table')
    for box_html in page_table:
        if re.search("Submitted By:",box_html.encode('utf8')) != None:
            break

    # soup.find(itemprop="itemreviewed")
    # a = soup.find(id="starSummaryText").find_all('meta')

    route_info = {}
    table_row = box_html.find_all('tr')
    for r in table_row:
        morsel = r.get_text()
        morsel = morsel.replace('\n','')
        i = morsel.split(u':\xa0')

        # some rows like Forecast are bad
        permissable_datum = ['Location', 'Page Views', 'Administrators', 'Consensus', 'Submitted By', 'FA', 'Type', 'Elevation']
        if i[0].encode('utf8') in permissable_datum:

            if i[0].encode('utf8') != 'Consensus':
                if re.search('^Forecast',i[0].encode('utf8')) == None:
                    route_info[i[0].encode('utf8')] = i[1].encode('utf8')
            else:
                grade = r.get_text()[12:]
                for g in grade.split(u' '):
                    h = g.split(u':\xa0')
                    if len(h) > 1:
                        route_info['Consensus-'+str(h[0])] = str(h[1])

    return route_info

def get_route_info(page_id):
    
    url = 'http://www.mountainproject.com/v/' + str(page_id)
    
    try:
        mp_page = urllib2.urlopen(url)
    except:
        return None
    else:
        mp_html = mp_page.read()
        soup = bs4.BeautifulSoup(mp_html, 'html.parser')
        
        route_name = get_route_name(soup)

        box_data = get_box_data(soup)

        z = route_name.copy()
        z.update(box_data)

        return z

def traverse(page_id):
    children = get_children(page_id)
    print children
    for child in children:
        if get_children(child) != None:
            traverse(child) # RECURSION!!!
        else:
            for child in children:
                print get_route_info(child)
            return child

traverse(105833388)

# get_route_info(107431192)


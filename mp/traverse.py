import re
import urllib2
import sys
import bs4
import codecs
import warnings

def get_children(href):

    try:
        mp_page = urllib2.urlopen('http://www.mountainproject.com' + href)
    except:
        return None
    else:
        mp_html = mp_page.read()
        soup = bs4.BeautifulSoup(mp_html, 'html.parser')

        # every route and area page has this container
        youContainer = soup.find(id="youContainer")
        root = youContainer == None

        if root: # at /v/ or /destinations/
            # get tags for the 50 states and International
            dest_iter = soup.find_all('span', { 'class': "destArea" })

            # pull out href key
            children = get_child_href(dest_iter)

            return children
        else:
            
            is_route = re.search('You & This Route',youContainer.get_text()) != None
            is_area = re.search('You & This Area',youContainer.get_text()) != None

            if is_route:
                return None
            elif is_area:
                # get div for any area or route
                leftnavdiv = soup.find(id='viewerLeftNavColContent')
                dest_iter = leftnavdiv.find_all('a')

                # pull out href key
                children = get_child_href(dest_iter)

                return children
            else:
                warnings.warn("NEITHER ROUTE NOR AREA " + href)

def get_child_href(dest_iter):
    
    href = []
    
    for dest in dest_iter:
        if len(dest.get_text()) > 0: # children are labeled with text
            if dest.a != None: # sometimes <a> is within a <span>
                dest = dest.a
            h = dest.get('href')
            h = h.encode('utf-8', errors = 'ignore') # encoding is crucial
            href.append(h)
    
    # only routes and areas have an href containing /v/
    href = [h for h in href if '/v/' in h]
    
    return href

def get_box_data(soup):

    # find stats box in soup with regex
    page_table = soup.find_all('table')
    for box in page_table:
        if re.search("Submitted By:",box.encode('utf-8')) != None: # questionable
            break

    box_data = {}

    for tr in box.find_all('tr'):

        # encode html to scan with regex
        tr_str = tr.encode('utf-8', errors = 'ignore')

        # UTF-8 characters that separate data
        split_char = ':\xc2\xa0'

        # check if this table row one we want
        permissable_datum = ['Location', 'Page Views', 'Administrators', 'Consensus', 'Submitted By', 'FA', 'Type', 'Elevation']
        perRE = re.compile("|".join(permissable_datum))
        perMatch = perRE.search(tr_str)

        # if it is a permissable data row
        if perMatch != None:
            morsel = tr.get_text().encode('utf-8', errors = 'ignore')
            i = morsel.split(split_char)
            head = i[0].strip()
            body = i[1].strip() 
            
            # body has junk in it like "\xc2\xa0View Map\xc2\xa0\xc2\xa0Incorrect?"

            if head != 'Consensus':

                # store data in dict
                box_data[head] = body

            else:

                # grade requires two levels of parsing
                grade = tr.get_text()[12:-10] # to chop off "Consensus: ... [details]"
                grade = grade.encode('utf-8', errors = 'ignore')

                # store data in same dict as above
                for g in grade.split('  '):
                    h = g.split(split_char)
                    if len(h) > 1:
                        box_data['Consensus-'+h[0]] = h[1]

    return box_data


def get_description(soup):

    detail = {}
    for h3 in soup.find_all('h3', { 'class': "dkorange" }):

        # encode html to scan with regex
        h3_str = h3.get_text().encode('utf-8', errors = 'ignore')

        # headers of info we want
        permissable_datum = ['Description', 'Getting There', 'Protection', 'Location']

        # see which one matches
        for head in permissable_datum:
            perMatch = re.search(head, h3_str)
            if perMatch != None:

                # text is the element after the h3
                body = h3.next_sibling

                # save text
                detail_str = body.get_text().encode('utf-8', errors = 'ignore')
                detail[head] = detail_str.strip()

    return detail


def get_route_name(soup):

    route_soup = soup.h1.get_text()
    
    route_name = route_soup.encode('utf-8' ,errors = 'ignore')

    route_name = route_name.strip('\xc2\xa0 ')

    return { 'Name': route_name }


def get_star_rating(soup):
    
    star_rating = {}
    
    meta = soup.find(id="starSummaryText").find_all('meta')
    for m in meta:
        head = m['itemprop']
        head = head.encode('utf-8', errors = 'ignore')
        body = m['content']
        body = body.encode('utf-8', errors = 'ignore')
        star_rating['Star-' + head] = float(m['content'])
        
    return star_rating


def get_route_info(href):
    
    try:
        mp_page = urllib2.urlopen('http://www.mountainproject.com' + href)
    except:
        return None
    else:
        mp_html = mp_page.read()
        soup = bs4.BeautifulSoup(mp_html, 'html.parser')
        
        route_info = {}

        route_name = get_route_name(soup)
        route_info.update(route_name)

        box_data = get_box_data(soup)
        route_info.update(box_data)

        detail = get_description(soup)
        route_info.update(detail)

        star_rating = get_star_rating(soup)
        route_info.update(star_rating)

        return route_info


def print_dict(child_detail):
    for datum in child_detail:
        fd = codecs.open("data/"+datum,'a', 'utf-8')
        d = child_detail[datum].decode('utf-8', errors = 'ignore')
        fd.write(d)
        fd.close()


def traverse(href):

    children = get_children(href)
    for child in children:
        if get_children(child) != None:
#            child_detail = get_route_info(child)
#            if child_detail != None:
#                print child_detail['Name']
#                print_dict(child_detail)
            traverse(child) # RECURSION!!!
        else:
            for child in children:
                child_detail = get_route_info(child)
                if child_detail != None:
                    print child_detail['Name']
                    print_dict(child_detail)
            return child

#traverse('/v/105907743')

print get_route_info('/v/108637906')

# print "International"
# traverse(105907743)
# print "Alabama"
# traverse(105905173)
# print "Alaska"
# traverse(105909311)
# print "Arizona"
# traverse(105708962)
# print "Arkansas"
# traverse(105901027)
# print "California"
# traverse(105708959)
# print "Colorado"
# traverse(105708956)
# print "Connecticut"
# traverse(105806977)
# print "Delaware"
# traverse(106861605)
# print "Georgia"
# traverse(105897947)
# print "Hawaii"
# traverse(106316122)
# print "Idaho"
# traverse(105708958)
# print "Illinois"
# traverse(105911816)
# print "Iowa"
# traverse(106092653)
# print "Kansas"
# traverse(107235316)
# print "Kentucky"
# traverse(105868674)
# print "Maine"
# traverse(105948977)
# print "Maryland"
# traverse(106029417)
# print "Massachusetts"
# traverse(105908062)
# print "Michigan"
# traverse(106113246)
# print "Minnesota"
# traverse(105812481)
# print "Missouri"
# traverse(105899020)
# print "Montana"
# traverse(105907492)
# print "Nevada"
# traverse(105708961)
# print "New Hampshire"
# traverse(105872225)
# print "New Jersey"
# traverse(106374428)
# print "New Mexico"
# traverse(105708964)
# print "New York"
# traverse(105800424)
# print "North Carolina"
# traverse(105873282)
# print "Ohio"
# traverse(105994953)
# print "Oklahoma"
# traverse(105854466)
# print "Oregon"
# traverse(105708965)
# print "Pennsylvania"
# traverse(105913279)
# print "Rhode Island"
# traverse(106842810)
# print "South Carolina "
# traverse(107638915)
# print "South Dakota"
# traverse(105708963)
# print "Tennessee"
# traverse(105887760)
# print "Texas"
# traverse(105835804)
# print "Utah"
# traverse(105708957)
# print "Vermont"
# traverse(105891603)
# print "Virginia"
# traverse(105852400)
# print "Washington"
# traverse(105708966)
# print "West Virginia"
# traverse(105855459)
# print "Wisconsin"
# traverse(105708968)
# print "Wyoming"
# traverse(105708960)
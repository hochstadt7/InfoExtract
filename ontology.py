import requests
import lxml.html
import rdflib

PREFIX = "http://example.org"
seed_address='https://en.wikipedia.org/wiki/List_of_Academy_Award-winning_films'
relation_ontologies={}
g = rdflib.Graph()
set_of_people=set()
delete_empty_val="http://example.org/"

# add a triple to our ontology
def add_triple(ont_name,xpath_result,key):

    result=xpath_result[0]

    encoded_string = result.encode("ascii", "ignore")
    decode_string = encoded_string.decode()
    if key=='ont_occupation':
        decode_string=decode_string.lower()

        splitted=decode_string.split(',')
        for splits in splitted:
            candidate=f'{PREFIX}/{splits.strip().replace(" ","_")}'
            if not candidate == delete_empty_val:
                ont_val = rdflib.URIRef(candidate)
                g.add((ont_name, relation_ontologies[key], ont_val))
    else:
        candidate=f'{PREFIX}/{decode_string.strip().replace(" ","_")}'
        ont_val = rdflib.URIRef(candidate)
        g.add((ont_name, relation_ontologies[key], ont_val))

# extract year for born field
def extract_year(txt):

    if not txt:
        return [""]
    txt=txt[0]
    n=len(txt)
    i=j=0
    while i<n:
        if txt[i]<='9' and txt[i]>='0':
            j=j+1
        else:
            j=0
        if j==4:
            '''if i<n-1 and txt[i+1]=='/': # example format: 1976/1977
                return txt[i-3:i+6]'''
            return [txt[i-3:i+1]] # example format: 1976
        i+=1
    return [""]

# check content in the human info box
def check_human_page(ont_name,a,str1,str2):

    td = a[0].xpath("./tbody/tr[./th//text()='"+str1+"']/td")

    if td != []:
        if str1=='Born':
            bdays=td[0].xpath(".//span[contains(@class,'bday')]")
            if not bdays:
                txt=extract_year(td[0].xpath("./text()"))
                if len(txt[0])>1:
                    add_triple(ont_name,txt,str2)
                return
            else:
                add_triple(ont_name,bdays[0].xpath("./text()"),str2)
                return

        iss = td[0].xpath(".//i")
        # ont_occupation
        if iss:
            for i in iss:
                links = i.xpath("./a")
                if links:
                    link_occupy=links[0].xpath("./@href")
                    add_triple(ont_name, [link_occupy[0][6:]], str2)
                else:
                    add_triple(ont_name, i.xpath("./text()"), str2)
        else:
            lis = td[0].xpath(".//li")
            if lis:
                for li in lis:
                    links = li.xpath("./a")
                    if links:
                        link_occupy = links[0].xpath("./@href")
                        add_triple(ont_name, [link_occupy[0][6:]], str2)
                    else:
                        add_triple(ont_name, li.xpath("./text()"), str2)
            else:
                links = td[0].xpath("./a")
                if links:
                    for link in links:
                        content_link = link.xpath("./@href")
                        sub_abbrev = content_link[0][6:]
                        add_triple(ont_name, [sub_abbrev], str2)


                try_fix = td[0].xpath("./text()")
                for t in try_fix:
                    add_triple(ont_name, [t], str2)



# process human pages by the all elements that are required to the questions
def human_process(address):
    human_link = address[0]

    if human_link not in set_of_people:
        set_of_people.add(human_link)
        res = requests.get('https://en.wikipedia.org/' + human_link)

        doc = lxml.html.fromstring(res.content)
        a = doc.xpath("//table[contains(@class,'infobox')]")
        if a:

            ont_name = rdflib.URIRef(f'{PREFIX}{human_link[5:]}')
            check_human_page(ont_name, a, 'Born', 'ont_born')
            check_human_page(ont_name, a, 'Occupation', 'ont_occupation')


# check content in the movie info box
def check_movie_page(ont_name,a,str1,str2):

    td = a[0].xpath("./tbody/tr[./th//text()='"+str1+"']/td")

    if td:
        if str1=='Release date':
            bdays=td[0].xpath(".//span[contains(@class,'bday')]")
            if not bdays:
                return
            else:
                for bday in bdays:

                    add_triple(ont_name,bday.xpath("./text()"),str2)
                return

        elif str1=='Based on':
            g.add((ont_name, relation_ontologies['ont_based'],rdflib.URIRef(f'{PREFIX}/Yes') )) # based on book, we don't really care on which
            return

        iss=td[0].xpath(".//i")
        if iss:
            for i in iss:
                links = i.xpath("./a")
                if links:
                    if str1 != 'Running time':
                        abbrev=links[0].xpath("./@href")[0][6:]
                        add_triple(ont_name, [abbrev], str2)
                        human_process(links[0].xpath("./@href"))
                    else:
                        add_triple(ont_name, links[0].xpath("./text()"), str2)
                else:
                    add_triple(ont_name, i.xpath("./text()"), str2)
        else:
            lis=td[0].xpath("./div/ul/li")
            if lis:
                for li in lis:
                    links=li.xpath("./a")
                    if links:
                        if str1 != 'Running time':
                            abbrev = links[0].xpath("./@href")[0][6:]
                            add_triple(ont_name, [abbrev], str2)
                            human_process(links[0].xpath("./@href"))
                        else:
                            add_triple(ont_name, links[0].xpath("./text()"), str2)
                    else:
                        add_triple(ont_name, li.xpath("./text()"), str2)
            else:
                links=td[0].xpath("./a")
                if links:
                    if str1 != 'Running time':
                        for link in links:
                            contect_link = link.xpath("./@href")
                            sub_abbrev=contect_link[0][6:]
                            add_triple(ont_name, [sub_abbrev], str2)
                            human_process([contect_link][0])
                    else:
                        add_triple(ont_name, links[0].xpath("./text()"), str2)

                try_fix=td[0].xpath("./text()")
                for t in try_fix:
                    add_triple(ont_name, [t], str2)




# process movie pages by the all elements that are required to the questions
def movie_process(address):

    res=requests.get('https://en.wikipedia.org/'+address)
    print('https://en.wikipedia.org/'+address)
    doc = lxml.html.fromstring(res.content)
    a=doc.xpath("//table[contains(@class,'infobox')]")

    ont_name=rdflib.URIRef(f'{PREFIX}{address[5:]}')

    check_movie_page(ont_name,a,'Directed by','ont_directed')
    check_movie_page(ont_name, a, 'Produced by', 'ont_produced')
    check_movie_page(ont_name, a, 'Based on', 'ont_based')
    check_movie_page(ont_name, a, 'Starring', 'ont_starring')
    check_movie_page(ont_name, a, 'Release date', 'ont_release')
    check_movie_page(ont_name, a, 'Running time', 'ont_running')

    g.serialize("ontology.nt",format="nt")

# maybe there is a way to not pass g through all the calls
def build_ontology():

    ont_directed = rdflib.URIRef(f'{PREFIX}/directed_by')
    ont_produced = rdflib.URIRef(f'{PREFIX}/produced_by')
    ont_based = rdflib.URIRef(f'{PREFIX}/based_on')
    ont_starring = rdflib.URIRef(f'{PREFIX}/starring')
    ont_release = rdflib.URIRef(f'{PREFIX}/release_date')
    ont_running = rdflib.URIRef(f'{PREFIX}/running_time')

    ont_born=rdflib.URIRef(f'{PREFIX}/born')
    ont_occupation = rdflib.URIRef(f'{PREFIX}/occupation')

    relation_ontologies['ont_directed']=ont_directed
    relation_ontologies['ont_produced'] = ont_produced
    relation_ontologies['ont_based'] = ont_based
    relation_ontologies['ont_starring'] = ont_starring
    relation_ontologies['ont_release'] = ont_release
    relation_ontologies['ont_running'] = ont_running

    relation_ontologies['ont_born'] = ont_born
    relation_ontologies['ont_occupation'] = ont_occupation


    lst_of_address=[]
    res=requests.get(seed_address)
    doc=lxml.html.fromstring(res.content)
    # get all movies from main page
    for t in doc.xpath("/html/body/div[3]/div[3]/div[5]/div[1]/table[1]/tbody[1]/tr[./td[2]/a/text()>2009]/td[1]//a/@href"):
        lst_of_address.append(t)

    for address in lst_of_address:
        movie_process(address)

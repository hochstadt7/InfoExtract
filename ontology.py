
import requests
import lxml.html
import rdflib

PREFIX = "http://example.org"
seed_address='https://en.wikipedia.org/wiki/List_of_Academy_Award-winning_films'
relation_ontologies={}

# add triple to our ontology
def add_triple(ont_name,xpath_result,key,g):

    result=xpath_result[0].replace(" ","_")

    encoded_string = result.encode("ascii", "ignore")
    decode_string = encoded_string.decode()
    ont_val = rdflib.URIRef(f'{PREFIX}/{decode_string}')
    g.add((ont_name, relation_ontologies[key], ont_val))

# check for some possible structures of the infobox
def check_cases(ont_name,a,str1,str2,g):

    td = a[0].xpath("./tbody/tr[./th//text()='"+str1+"']/td")

    if td != []:
        if str1=='Release date':
            bdays=td[0].xpath(".//span[contains(@class,'bday')]")
            if not bdays:
                return
            else:
                for bday in bdays:

                    add_triple(ont_name,bday.xpath("./text()"),str2,g)
                return

        elif str1=='Based on':
            g.add((ont_name, relation_ontologies['ont_based'],rdflib.URIRef(f'{PREFIX}/Yes') )) # Is based on, we don't really care on what.
            return

        lis = td[0].xpath("./div/ul/li")
        for li in lis:

            iss = li.xpath(".//i")
            for i in iss:

                links = i.xpath("./a")
                if not links:
                    add_triple(ont_name, i.xpath("./text()"), str2,g)
                else:
                    for link in links:
                        add_triple(ont_name, link.xpath("./text()"), str2,g)
            if not iss:
                links = li.xpath("./a")
                if not links:
                    add_triple(ont_name, li.xpath("./text()"), str2,g)
                else:
                    for link in links:
                        add_triple(ont_name, link.xpath("./text()"), str2,g)
        if not lis:

            iss = td[0].xpath(".//i")
            for i in iss:

                links = i.xpath("./a")
                if not links:
                    add_triple(ont_name, i.xpath("./text()"), str2,g)
                else:
                    for link in links:
                        add_triple(ont_name, link.xpath("./text()"), str2,g)
            if not iss:
                dvs=td[0].xpath("./div")
                for dv in dvs:
                    links = dv.xpath("./a")
                    if not links:
                        add_triple(ont_name, dv.xpath("./text()"), str2,g)
                    else:
                        for link in links:
                            add_triple(ont_name, link.xpath("./text()"), str2,g)
                if not dvs:
                    links = td[0].xpath("./a")
                    if not links:
                        add_triple(ont_name, td[0].xpath("./text()"), str2,g)
                    else:
                        for link in links:
                            add_triple(ont_name, link.xpath("./text()"), str2,g)



# process page by the six elements that are required to the questions (for the movies)
# todo: process actors, film directors, etc.
def process_page(address,g):
    res=requests.get('https://en.wikipedia.org/'+address)
    print('https://en.wikipedia.org/'+address)
    doc = lxml.html.fromstring(res.content)
    a=doc.xpath("//table[contains(@class,'infobox')]")
    name = a[0].xpath("./tbody/tr[1]//text()")[0].replace(" ","_")

    ont_name=rdflib.URIRef(f'{PREFIX}/{name}')
    check_cases(ont_name,a,'Directed by','ont_directed',g)
    check_cases(ont_name, a, 'Produced by', 'ont_produced',g)
    check_cases(ont_name, a, 'Based on', 'ont_based',g)
    check_cases(ont_name, a, 'Starring', 'ont_starring',g)
    check_cases(ont_name, a, 'Release date', 'ont_release',g)
    check_cases(ont_name, a, 'Running time', 'ont_running',g)

    g.serialize("ontology.nt",format="nt")

# maybe there is a way to not pass g through all the calls
def build_ontology(g):

    ont_directed = rdflib.URIRef(f'{PREFIX}/directed_by')
    ont_produced = rdflib.URIRef(f'{PREFIX}/produced_by')
    ont_based = rdflib.URIRef(f'{PREFIX}/based_on')
    ont_starring = rdflib.URIRef(f'{PREFIX}/starring')
    ont_release = rdflib.URIRef(f'{PREFIX}/release_date')
    ont_running = rdflib.URIRef(f'{PREFIX}/running_time')

    relation_ontologies['ont_directed']=ont_directed
    relation_ontologies['ont_produced'] = ont_produced
    relation_ontologies['ont_based'] = ont_based
    relation_ontologies['ont_starring'] = ont_starring
    relation_ontologies['ont_release'] = ont_release
    relation_ontologies['ont_running'] = ont_running

    lst_of_address=[]
    res=requests.get(seed_address)
    doc=lxml.html.fromstring(res.content)
    # get all movies from main page
    for t in doc.xpath("/html/body/div[3]/div[3]/div[5]/div[1]/table[1]/tbody[1]/tr[./td[2]/a/text()>2009]/td[1]//a/@href"):
        lst_of_address.append(t)

    for address in lst_of_address:
        process_page(address,g)
        #process_page('/wiki/Amy_(2015_film)')
        #break
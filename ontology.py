
import requests
import lxml.html
import rdflib

PREFIX = "http://example.org"
seed_address='https://en.wikipedia.org/wiki/List_of_Academy_Award-winning_films'
relation_ontologies={}
g = rdflib.Graph()

# add triple to our ontology
def add_triple(ont_name,xpath_result,key):

    result=xpath_result[0].replace(" ","_")

    encoded_string = result.encode("ascii", "ignore")
    decode_string = encoded_string.decode()
    if key=='ont_occupation':
        decode_string=decode_string.lower()
    ont_val = rdflib.URIRef(f'{PREFIX}/{decode_string}')
    g.add((ont_name, relation_ontologies[key], ont_val))

#def extract_year(txt):


def check_human_page(ont_name,a,str1,str2):

    td = a[0].xpath("./tbody/tr[./th//text()='"+str1+"']/td")

    if td != []:
        if str1=='Born':
            bdays=td[0].xpath(".//span[contains(@class,'bday')]")
            if not bdays:

                return # need to return the year
            else:
                for bday in bdays:
                    add_triple(ont_name,bday.xpath("./text()"),str2)
                return
        elif str1=='Awards':
            g.add((ont_name, relation_ontologies['ont_award'],rdflib.URIRef(f'{PREFIX}/Yes') )) # Does award, we don't really care on which.
            return

        iss = td[0].xpath(".//i")
        # ont_occupation
        if iss:
            for i in iss:
                links = i.xpath("./a")
                if links:
                    add_triple(ont_name, links[0].xpath("./text()"), str2)  # assuming only 1 link possible under i
                else:
                    add_triple(ont_name, i.xpath("./text()"), str2)
        else:
            lis = td[0].xpath(".//li") # not like in movies, cuz of one case (Glen Greewald)
            if lis:
                for li in lis:
                    links = li.xpath("./a")
                    if links:
                        add_triple(ont_name, links[0].xpath("./@href"), str2)  # assuming only 1 link possible under li
                    else:
                        add_triple(ont_name, li.xpath("./text()"), str2)
            else:
                links = td[0].xpath("./a")
                if links:
                    add_triple(ont_name, links[0].xpath("./@href"), str2)  # assuming only 1 link possible under li
                else:
                    add_triple(ont_name, td[0].xpath("./text()"), str2)


def human_process(address):
    res = requests.get('https://en.wikipedia.org/' + address[0])
    print('https://en.wikipedia.org/' + address[0])
    doc = lxml.html.fromstring(res.content)
    a = doc.xpath("//table[contains(@class,'infobox')]")
    if a:
        name=a[0].xpath("./tbody/tr[1]//text()")
        if name:
            name = name[0].replace(" ", "_")
            ont_name = rdflib.URIRef(f'{PREFIX}/{name}')
            check_human_page(ont_name, a, 'Born', 'ont_born')
            check_human_page(ont_name, a, 'Occupation', 'ont_occupation')
            check_human_page(ont_name, a, 'Awards', 'ont_award')

            g.serialize("ontology.nt", format="nt")

# check for some possible structures of the infobox
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
            g.add((ont_name, relation_ontologies['ont_based'],rdflib.URIRef(f'{PREFIX}/Yes') )) # Is based on, we don't really care on what.
            return

        iss=td[0].xpath(".//i")
        if iss:
            for i in iss:
                links = i.xpath("./a")
                if links:
                    add_triple(ont_name, links[0].xpath("./text()"), str2) # assuming only 1 link possible under i
                    if str1 != 'Running time':
                        human_process(links[0].xpath("./@href"))
                else:
                    add_triple(ont_name, i.xpath("./text()"), str2)
        else:
            lis=td[0].xpath("./div/ul/li") # assume li must be under div/ul. if not, use .//li
            if lis:
                for li in lis:
                    links=li.xpath("./a")
                    if links:
                        add_triple(ont_name, links[0].xpath("./text()"), str2) # assuming only 1 link possible under li
                        if str1 != 'Running time':
                            human_process(links[0].xpath("./@href"))
                    else:
                        add_triple(ont_name, li.xpath("./text()"), str2)
            else:
                links=td[0].xpath("./a")
                if links:
                    add_triple(ont_name, links[0].xpath("./text()"), str2)  # assuming only 1 link possible under li
                    if str1 != 'Running time':
                        human_process(links[0].xpath("./@href"))
                else:
                    add_triple(ont_name, td[0].xpath("./text()"), str2)




# process page by the six elements that are required to the questions (for the movies)
def movie_process(address):
    res=requests.get('https://en.wikipedia.org/'+address)
    print('https://en.wikipedia.org/'+address)
    doc = lxml.html.fromstring(res.content)
    a=doc.xpath("//table[contains(@class,'infobox')]")
    name = a[0].xpath("./tbody/tr[1]//text()")[0].replace(" ","_")

    ont_name=rdflib.URIRef(f'{PREFIX}/{name}')
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
    ont_award=rdflib.URIRef(f'{PREFIX}/award')

    relation_ontologies['ont_directed']=ont_directed
    relation_ontologies['ont_produced'] = ont_produced
    relation_ontologies['ont_based'] = ont_based
    relation_ontologies['ont_starring'] = ont_starring
    relation_ontologies['ont_release'] = ont_release
    relation_ontologies['ont_running'] = ont_running

    relation_ontologies['ont_born'] = ont_born
    relation_ontologies['ont_occupation'] = ont_occupation
    relation_ontologies['ont_award'] = ont_award

    lst_of_address=[]
    res=requests.get(seed_address)
    doc=lxml.html.fromstring(res.content)
    # get all movies from main page
    for t in doc.xpath("/html/body/div[3]/div[3]/div[5]/div[1]/table[1]/tbody[1]/tr[./td[2]/a/text()>2009]/td[1]//a/@href"):
        lst_of_address.append(t)

    for address in lst_of_address:
        movie_process(address)
        #process_page('/wiki/Amy_(2015_film)')
        #break
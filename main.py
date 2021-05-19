import sys
import requests
import lxml.html
import rdflib

PREFIX = "http://example.org"
g = rdflib.Graph()
seed_address='https://en.wikipedia.org/wiki/List_of_Academy_Award-winning_films'
relation_ontologies={}

# helper function to extract entity
def extract_entity(s, start, end):

    start = s.index(start) + len(start)
    end = s.index(end, start)
    return s[start:end]

# extract entity, relation and possibly second entity
def extract_q_info(s):

    relation=entity=entity2=''
    # relation is saved as appears in the infobox on wiki, with lowercase and _ instead of space
    q_number=0
    if s[:2]=='Is':
        q_number=3
        relation = 'based_on'
        entity=extract_entity(s,'is','based on')

    elif s[:3]=='Who':
        if 'directed' in s:
            q_number = 1
            relation='directed_by'
            entity=extract_entity(s,'directed','?')
        elif 'produced' in s:
            q_number = 2
            relation = 'produced_by'
            entity = extract_entity(s, 'produced', '?')
        else:
            q_number = 6
            relation = 'starring'
            entity = extract_entity(s, 'starred in', '?')

    elif s[:3]=='Did':
        q_number = 7
        relation='starring'
        entity = extract_entity(s, 'Did', 'star in')
        entity2=extract_entity(s, 'star in', '?')

    elif s[:3]=='How':
        if 'long' in s:
            q_number = 5
            relation = 'running_time'
            entity =extract_entity(s, 'is', '?')
        elif 'based_on' in s:
            q_number = 10
            relation='based_on'
        elif 'starring' in s:
            q_number = 11
            relation='starring'
            entity=extract_entity(s,'starring', 'won')
        else:
            q_number = 12
            relation='occupation'
            entity=extract_entity(s,'many','are')
            entity2=extract_entity(s,'also','?')

    elif s[:4]=='When':
        if 'born' in s:
            q_number = 8
            relation='born'
            entity=extract_entity(s,'was','born')
        else:
            q_number = 4
            relation='released_date'
            entity=extract_entity(s,'was','released')

    elif s[:4]=='What':
        q_number = 9
        relation='occupation'
        entity=extract_entity(s,'of','?')

    else:
        print('Wrong question format')

    return q_number,relation,entity,entity2


# get answers using our ontology
def query(q_number,relation,entity,entity2):
    relation=relation.replace(' ', '_')
    entity = entity.replace(' ', '_')
    entity2=entity2.replace(' ', '_')

    if q_number==1 or q_number==2 or q_number==4 or q_number==5 or q_number==6 or q_number==8 or q_number==9:
        output=g.query("select ?a where {<"+PREFIX + entity + "> <"+PREFIX + relation + "> ?a .}")
        # produce list of answers
        output=', '.join([result[1][len(PREFIX):].replace('_',' ') for result in output])

    elif q_number==3:
        output=g.query("select ?a where {<"+PREFIX + entity + "> <"+PREFIX + relation + "> ?a .}") # how do we know if type is book? need to add to ontology too?

    elif q_number==7:
        output=g.query("select (COUNT(?s) as ?CNT) where {?s <"+PREFIX + relation + "> <"+PREFIX +entity+"> .}")

        temp = output
        for result in temp: # it will take only one iteration, this is the easiest way i found to extract the actual count
            output = result[0]

        if output=='0':
            output='No'
        else:
            output='Yes'

    elif q_number==10:
        output=g.query("select ?a where {<"+PREFIX + entity + "> <"+PREFIX + relation + "> ?a .}") # how do we know if type is book? need to add to ontology too?

    elif q_number==11:
        output=g.query("select (COUNT(?s) as ?CNT) where {?s <"+PREFIX + relation + "> ?a ."\
                       "?a <"+PREFIX+"awards> <"+PREFIX+"academy_awards> ."
        )
        temp=output
        for result in temp:
            output = result[0]

    elif q_number==12:
        output = g.query("select (COUNT(?s) as ?CNT) where {?s <"+PREFIX + relation + "> <"+PREFIX +entity+ "> ." \
                            "?s <"+PREFIX + relation + "> <"+PREFIX +entity2+ "> ."
                         )
        temp = output
        for result in temp:
            output = result[0]

    else:
        output=None

    print(output)

def add_if_not_empty(ont_name,xpath_result,key):

    for i in range(len(xpath_result)):
        result=xpath_result[i].replace(" ","_")

        if result!='\n':
            encoded_string=result.encode("ascii","ignore")
            decode_string = encoded_string.decode()
            ont_val=rdflib.URIRef(f'{PREFIX}/{decode_string}')
            g.add((ont_name, relation_ontologies[key], ont_val))

def process_page(address):
    res=requests.get('https://en.wikipedia.org/'+address)
    print('https://en.wikipedia.org/'+address)
    doc = lxml.html.fromstring(res.content)
    a=doc.xpath("//table[contains(@class,'infobox')]")
    name = a[0].xpath("./tbody/tr[1]//text()")[0].replace(" ","_")
    ont_name=rdflib.URIRef(f'{PREFIX}/{name}')

    cnt = a[0].xpath("count(./tbody/tr[./th//text()='Directed by']/td//li)")
    cnt2 = a[0].xpath("count(./tbody/tr[./th//text()='Directed by']/td//a)")
    if cnt > 0:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Directed by']/td//li//text()")
    elif cnt2 > 0:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Directed by']/td//a//text()")
    else:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Directed by']/td//text()")
    add_if_not_empty(ont_name,xpath_result,'ont_directed')

    cnt=a[0].xpath("count(./tbody/tr[./th//text()='Produced by']/td//li)")
    cnt2=a[0].xpath("count(./tbody/tr[./th//text()='Produced by']/td//a)")
    if cnt>0:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Produced by']/td//li//text()")
    elif cnt2>0:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Produced by']/td//a//text()")
    else:
        xpath_result=a[0].xpath("./tbody/tr[./th//text()='Produced by']/td//text()") # need to check if there is li tag
    add_if_not_empty(ont_name,xpath_result,'ont_produced')

    #ont_screened = a[0].xpath("./tbody/tr[./th/text()='Screenplay by']/td//text()")
    cnt = a[0].xpath("count(./tbody/tr[./th//text()='Based on']/td//li)")
    cnt2 = a[0].xpath("count(./tbody/tr[./th//text()='Based on']/td//a)")
    if cnt > 0:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Based on']/td//li//text()")
    elif cnt2 > 0:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Based on']/td//a//text()")
    else:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Based on']/td//text()")  # need to check if there is li tag
    add_if_not_empty(ont_name, xpath_result, 'ont_based')

    cnt = a[0].xpath("count(./tbody/tr[./th//text()='Starring']/td//li)")
    cnt2 = a[0].xpath("count(./tbody/tr[./th//text()='Starring']/td//a)")
    if cnt > 0:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Starring']/td//li//text()")
    elif cnt2 > 0:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Starring']/td//a//text()")
    else:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Starring']/td//text()")  # need to check if there is li tag
    add_if_not_empty(ont_name, xpath_result, 'ont_starring')

    # need to adjust it to the forum's new instructions for release
    cnt = a[0].xpath("count(./tbody/tr[./th//text()='Release date']/td//li)")
    cnt2 = a[0].xpath("count(./tbody/tr[./th//text()='Release date']/td//a)")
    if cnt > 0:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Release date']/td//li//text()")
    elif cnt2 > 0:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Release date']/td//a//text()")
    else:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Release date']/td//text()")  # need to check if there is li tag
    add_if_not_empty(ont_name, xpath_result, 'ont_release')

    cnt = a[0].xpath("count(./tbody/tr[./th//text()='Running time']/td//li)")
    cnt2 = a[0].xpath("count(./tbody/tr[./th//text()='Running time']/td//a)")
    if cnt > 0:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Running time']/td//li//text()")
    elif cnt2 > 0:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Running time']/td//a//text()")
    else:
        xpath_result = a[0].xpath("./tbody/tr[./th//text()='Running time']/td//text()")  # need to check if there is li tag
    add_if_not_empty(ont_name, xpath_result, 'ont_running')

    g.serialize("ontology.nt",format="nt")


def build_ontology():

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
    for t in doc.xpath("/html/body/div[3]/div[3]/div[5]/div[1]/table[1]/tbody[1]/tr/td[1]//a/@href"):
        lst_of_address.append(t)

    for address in lst_of_address:
        process_page(address)






if __name__ == "__main__":

    input=sys.argv[1]
    if input=='question':
        q_number,relation,entity,entity2 = extract_q_info(sys.argv[2])
        query(q_number,relation,entity,entity2)

    elif input=='create':
        # TODO: build ontology using xpath
        build_ontology()

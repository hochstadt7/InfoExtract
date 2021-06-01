import sys
import rdflib
from ontology import build_ontology,PREFIX

g = rdflib.Graph()

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
        entity=extract_entity(s,'Is ',' based on')


    elif s[:3]=='Who':
        if 'directed' in s:
            q_number = 1
            relation='directed_by'
            entity=extract_entity(s,'directed ','?')

        elif 'produced' in s:
            q_number = 2
            relation = 'produced_by'
            entity = extract_entity(s, 'produced ', '?')
        else:
            q_number = 6
            relation = 'starring'
            entity = extract_entity(s, 'starred in ', '?')

    elif s[:3]=='Did':
        if 'star in ' in s:
            q_number = 7
            relation='starring'
            entity2 = extract_entity(s, 'Did ', ' star in')
            entity=extract_entity(s, 'star in ', '?')
        # our question
        else:
            q_number = 13
            relation = 'produced_by'
            entity2=extract_entity(s,'Did ',' produce')
            entity = extract_entity(s, 'produce ', '?')

    elif s[:3]=='How':

        if 'long is' in s:

            q_number = 5
            relation = 'running_time'
            entity =extract_entity(s, 'is ', '?')
        elif 'based on' in s:

            q_number = 10
            relation='based_on'
        elif 'starring' in s:
            q_number = 11
            relation='starring'

            entity=extract_entity(s,'starring ', ' won')
        else:

            q_number = 12
            relation='occupation'
            entity=extract_entity(s,'many ',' are')
            entity2=extract_entity(s,'also ','?')

    elif s[:4]=='When':
        if 'born?' in s:
            q_number = 8
            relation='born'
            entity=extract_entity(s,'was ',' born')
        else:
            q_number = 4
            relation='release_date'
            entity=extract_entity(s,'was ',' released')

    elif s[:4]=='What':
        q_number = 9
        relation='occupation'
        entity=extract_entity(s,'of ','?')

    else:
        print('Wrong question format')

    return q_number,relation,entity,entity2


# get answers using our ontology
def query(q_number,relation,entity,entity2):

    entity = entity.replace(' ', '_')
    entity2=entity2.replace(' ', '_')
    g.parse("ontology.nt", format="nt")


    if q_number==1 or q_number==2 or q_number==4 or q_number==5 or q_number==6 or q_number==8 or q_number==9:
        res=g.query("select ?a where {<"+PREFIX +'/'+ entity + "> <"+PREFIX +'/'+ relation + "> ?a .}")
        sorted_list=sorted([result[0][len(PREFIX) + 1:].replace('_', ' ') for result in res])
        output = ', '.join(sorted_list)



    elif q_number==3:
        res=g.query("select (COUNT(?a) as ?CNT) where {<"+PREFIX +'/'+ entity + "> <"+PREFIX +'/'+ relation + "> ?a .}") # how do we know if type is book? need to add to ontology too?
        output=list(res)[0][0]
        if output:
            output='Yes'
        else:
            output='No'

    elif q_number==7 or q_number==13:
        res=g.query("ASK {<"+PREFIX +'/'+ entity + "> <"+PREFIX +'/'+ relation + "> <"+PREFIX+'/'+entity2+ "> .}")
        output=list(res)[0]
        if output:
            output='Yes'
        else:
            output='No'

    elif q_number==10:
        res=g.query("select (COUNT(?a) as ?CNT) where {?a <"+PREFIX +'/'+ relation + "> ?s .}")
        output = str(list(res)[0][0])

    elif q_number==11:
        res=g.query("select (COUNT(?s) as ?CNT) where {?s <"+PREFIX +'/'+ relation + "> <"+ PREFIX+'/'+entity+"> .}")
        output = str(list(res)[0][0])


    elif q_number==12:
        res = g.query("select (COUNT(?s) as ?CNT) where {?s <"+PREFIX +'/'+ relation + "> <"+PREFIX +'/'+entity+ "> ." \
                            "?s <"+PREFIX +'/'+ relation + "> <"+PREFIX +'/'+entity2+ "> .}"
                         )
        output=str(list(res)[0][0])

    else:
        output=None
    print(output)



if __name__ == "__main__":

    input = sys.argv[1]
    if input=='question':

        q_number,relation,entity,entity2 = extract_q_info(sys.argv[2])
        query(q_number,relation,entity,entity2)

    elif input=='create':
        build_ontology()



import spacy

prepositions = ["ADP"]
SUBJECT_DEP = ["nsubj", "nsubjpass", "csubj","conj", "csubjpass", "agent", "expl"]
SUBJECT_POS = ["NOUN","PROPN"]
COMPOUNDS = ["compound"]
AUX_VERBS = ["aux","auxpass","pcomp"]
  
def traverse_dep_tree_inorder(fact,root):
 
    if root:
        for token in root.lefts:
            traverse_dep_tree_inorder(fact,token)
 
        fact.append(root)
        
        for token in root.rights:
            traverse_dep_tree_inorder(fact,token)
            
def form_objects_phrases(objects):
    """
    objects and verbs connected by prepositions
    """
    obj_phrases = []
    for object in objects:
        if object[0].pos_ !="VERB" and object[0].pos_ != "CCONJ":
            obj_phrases.append(" ".join([word.text for word in object]))
    return obj_phrases

def get_subs_from_conjunctions(subs):
    moreSubs = []
    for sub in subs:
        # rights is a generator
        rights = list(sub.rights)
        right_deps = {tok.lower_ for tok in rights}
        if "and" in right_deps or "," in right_deps:
            moreSubs.extend([tok for tok in rights if tok.dep_ in SUBJECT_DEP or tok.pos_ in SUBJECT_POS])
            if len(moreSubs) > 0:
                moreSubs.extend(get_subs_from_conjunctions(moreSubs))
    return moreSubs

def isNegated(tok):
    negations = {"no", "not", "n't", "never", "none"}
    for dep in list(tok.lefts) + list(tok.rights):
        if dep.lower_ in negations:
            return True
    return False

def find_subs(tok):
    head = tok.head
    while head.pos_ != "VERB" and head.pos_ not in SUBJECT_POS and head.head != head:
        head = head.head
    if head.pos_ == "VERB":
        subs = [tok for tok in head.lefts if tok.dep_ == "SUB"]
        if len(subs) > 0:
            verbNegated = isNegated(head)
            subs.extend(get_subs_from_conjunctions(subs))
            return subs, verbNegated
        elif head.head != head:
            return find_subs(head)
    elif head.pos_ in SUBJECT_POS:
        return [head], isNegated(tok)
    return [], False

def get_all_subs(v):
    verbNegated = isNegated(v)
    subs = [tok for tok in v.lefts if tok.dep_ in SUBJECT_DEP ]
    if len(subs) > 0:
        subs.extend(get_subs_from_conjunctions(subs))
    else:
        foundSubs, verbNegated = find_subs(v)
        subs.extend(foundSubs)
    return subs, verbNegated

def objs_from_lefts(lefts):
    fact = []
    left_facts = []
    for left in lefts:
        if left.pos_ in prepositions:
            traverse_dep_tree_inorder(fact,left)
            left_facts.append(fact)
            fact = []
    return left_facts
    
def objs_from_rights(rights):
    fact = []
    right_facts = []
    for right in rights:
        traverse_dep_tree_inorder(fact,right)
        right_facts.append(fact)
        fact = []
    return right_facts

def get_all_objs(v):
    objects = objs_from_rights(v.rights)
    objects.extend(objs_from_lefts(v.lefts))
    return objects
    
def generate_sub_compound(sub):
    sub_compunds = []
    for tok in sub.lefts:
        if tok.dep_ in COMPOUNDS:
            sub_compunds.extend(generate_sub_compound(tok))
    sub_compunds.append(sub)
    for tok in sub.rights:
        if tok.dep_ in COMPOUNDS:
            sub_compunds.extend(generate_sub_compound(tok))
    return sub_compunds

def extract_simple_sentences(sentence_object):
    simple_sentences = []
    verbs = [tok for tok in sentence_object if tok.pos_ == "VERB" and tok.dep_ not in AUX_VERBS]
     
    subjects = []
    for v in verbs:
        subs, verb_negated = get_all_subs(v)
        subjects.extend(subs)
            
    for v in verbs:
        objects = get_all_objs(v)
        object_phrases = form_objects_phrases(objects)
        for subject in subjects:
            sub_compound = " ".join([word.text for word in generate_sub_compound(subject)])
            for word in object_phrases:
                simple_sentences.append(sub_compound + " " + v.text + " " + word )
            
            
if __name__ == 'main':
    # sentence_extracted = "Nelson Mandela,Mahatma Gandhi and Adolf Hitler were born Rolihlahla Mandela on July 18, 1918, in the tiny village of Mvezo, on the banks of the Mbashe River in Transkei, South Africa, moved to Germany in 1913, studied in London and returned in 1945"
    # sentence_extracted = "Nelson Mandela, Mahatma Gandhi and Adolf Hitler were born in Austria in 1905, moved to Germany in 1913, studied in London and returned in 1945"
    # sentence_extracted = "In 1919, Hitler joined the German Workers' Party (DAP), the precursor of the NSDAP, and was appointed leader of the NSDAP in 1921."
    # sentence_extracted = "After his release from prison in 1924, Hitler gained popular support by attacking the Treaty of Versailles and promoting Pan-Germanism, anti-semitism and anti-communism with charismatic oratory and Nazi propaganda."
    # sentence_extracted = "This led to former chancellor Franz von Papen and other conservative leaders persuading President Paul von Hindenburg to appoint Hitler as Chancellor on 30 January 1933."
    # sentence_extracted = "Adolf Hitler was born on 20 April 1889 in Braunau am Inn, a town in Austria-Hungary, close to the border with the German Empire."

    sentence_extracted = "Sachin Rahul and Ganguly plays in India,England and Australia"
    nlp = spacy.load("en_core_web_lg")
    sentence_object = nlp(sentence_extracted)
    print(extract_simple_sentences(sentence_object))
            
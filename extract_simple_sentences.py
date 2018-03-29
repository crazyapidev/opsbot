
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
            #verbNegated = isNegated(head)
            subs.extend(get_subs_from_conjunctions(subs))
            return subs #, verbNegated
        elif head.head != head:
            return find_subs(head)
    elif head.dep_ in SUBJECT_DEP:
        return [head] #, isNegated(tok)
    return [] #, False

def get_all_subs(v):
    #verbNegated = isNegated(v)
    subs = [tok for tok in v.lefts if tok.dep_ in SUBJECT_DEP ]
    if len(subs) > 0:
        subs.extend(get_subs_from_conjunctions(subs))
    else:
        foundSubs = find_subs(v)
        subs.extend(foundSubs)
    return subs #, verbNegated

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

def remove_duplicate_sentences(simple_sentences):
    marker = set()
    sentences = [not marker.add(x.casefold()) and x for x in simple_sentences if x.casefold() not in marker]
    return sentences

def extract_simple_sentences(sentence_object):
    simple_sentences = []
    verbs = [tok for tok in sentence_object if tok.pos_ == "VERB" and tok.dep_ not in AUX_VERBS]
     
    subjects = []
    for v in verbs:
        subs = get_all_subs(v)
        subjects.extend(subs)
            
    for v in verbs:
        verb_negated = isNegated(v)
        objects = get_all_objs(v)
        object_phrases = form_objects_phrases(objects)
        for subject in subjects:
            sub_compound = " ".join([word.text for word in generate_sub_compound(subject)])
            for word in object_phrases:
                if verb_negated:
                    verb_text = "not " +  v.text
                else:
                    verb_text = v.text
                simple_sentences.append(sub_compound + " " + verb_text + " " + word )
    return remove_duplicate_sentences(simple_sentences)       
 
import unittest
nlp = spacy.load("en_core_web_lg")

class TestSimpleSentenceExtractor(unittest.TestCase):
    
    def test_sub_verb_obj(self):
        sentence_extracted = "Hitler joined the German Workers' Party (DAP)"
        sentence_object = nlp(sentence_extracted)
        simple_sentences = extract_simple_sentences(sentence_object)
        self.assertListEqual(simple_sentences,["Hitler joined the German Workers ' Party ( DAP )"])
        
    def test_sub_multiple_verbs_obj(self):
        sentence_extracted = "Hitler joined the German Workers' Party (DAP), the precursor of the NSDAP, and was appointed leader of the NSDAP in 1921"
        sentence_object = nlp(sentence_extracted)
        simple_sentences = extract_simple_sentences(sentence_object)
        self.assertListEqual(simple_sentences,["Hitler joined the German Workers ' Party ( DAP ) , the precursor of the NSDAP", 'Hitler joined ,', 'Hitler appointed leader of the NSDAP', 'Hitler appointed in 1921'])
        
    def test_multiple_subs_verb_obj(self):
        sentence_extracted = "Nelson Mandela, Mahatma Gandhi and Adolf Hitler were born in Austria"
        sentence_object = nlp(sentence_extracted)
        simple_sentences = extract_simple_sentences(sentence_object)
        self.assertListEqual(simple_sentences,['Nelson Mandela born in Austria', 'Mahatma Gandhi born in Austria', 'Adolf Hitler born in Austria'])
        
    def test_multiple_subs_verb_multiple_objs(self):
        sentence_extracted = "Nelson Mandela, Mahatma Gandhi and Adolf Hitler were born in Austria in 1905"
        sentence_object = nlp(sentence_extracted)
        simple_sentences = extract_simple_sentences(sentence_object)
        self.assertListEqual(simple_sentences,['Nelson Mandela born in Austria', 'Nelson Mandela born in 1905', 'Mahatma Gandhi born in Austria', 'Mahatma Gandhi born in 1905', 'Adolf Hitler born in Austria', 'Adolf Hitler born in 1905'])
        
    def test_multiple_subs_multiple_verbs_multiple_objs(self):
        sentence_extracted = "Nelson Mandela,Mahatma Gandhi and Adolf Hitler were born Rolihlahla Mandela on July 18, 1918, in the tiny village of Mvezo, on the banks of the Mbashe River in Transkei, South Africa, moved to Germany in 1913, studied in London and returned in 1945"
        sentence_object = nlp(sentence_extracted)
        simple_sentences = extract_simple_sentences(sentence_object)
        self.assertListEqual(simple_sentences,['Nelson Mandela born Rolihlahla Mandela', 'Nelson Mandela born on July 18 , 1918 ,', 'Nelson Mandela born in the tiny village of Mvezo ,', 'Nelson Mandela born on the banks of the Mbashe River in Transkei , South Africa', 'Nelson Mandela born ,', 'Mahatma Gandhi born Rolihlahla Mandela', 'Mahatma Gandhi born on July 18 , 1918 ,', 'Mahatma Gandhi born in the tiny village of Mvezo ,', 'Mahatma Gandhi born on the banks of the Mbashe River in Transkei , South Africa', 'Mahatma Gandhi born ,', 'Adolf Hitler born Rolihlahla Mandela', 'Adolf Hitler born on July 18 , 1918 ,', 'Adolf Hitler born in the tiny village of Mvezo ,', 'Adolf Hitler born on the banks of the Mbashe River in Transkei , South Africa', 'Adolf Hitler born ,',
                'Nelson Mandela moved to Germany', 'Nelson Mandela moved in 1913', 'Nelson Mandela moved ,', 
                'Mahatma Gandhi moved to Germany', 'Mahatma Gandhi moved in 1913', 'Mahatma Gandhi moved ,', 
                'Adolf Hitler moved to Germany', 'Adolf Hitler moved in 1913', 'Adolf Hitler moved ,',
                'Nelson Mandela studied in London', 'Mahatma Gandhi studied in London', 'Adolf Hitler studied in London', 
                'Nelson Mandela returned in 1945', 'Mahatma Gandhi returned in 1945', 'Adolf Hitler returned in 1945'])
        
    def test_obj_on_left_of_subj_verb_obj(self):
        sentence_extracted = "In 1919, Hitler joined the German Workers' Party (DAP)"
        sentence_object = nlp(sentence_extracted)
        simple_sentences = extract_simple_sentences(sentence_object)
        self.assertListEqual(simple_sentences,["Hitler joined the German Workers ' Party ( DAP )",'Hitler joined In 1919'])
        
    def test_obj_on_left_of_subj_multiple_verbs_multiple_objs(self):
        sentence_extracted = "In January 1962, Mandela traveled abroad illegally to attend a conference of African nationalist leaders in Ethiopia, visit the exiled Oliver Tambo in London and undergo guerilla training in Algeria."
        sentence_object = nlp(sentence_extracted)
        simple_sentences = extract_simple_sentences(sentence_object)
        self.assertListEqual(simple_sentences,['Mandela traveled abroad', 'Mandela traveled illegally', 'Mandela traveled to attend a conference of African nationalist leaders in Ethiopia', 'Mandela traveled ,', 'Mandela traveled .', 'Mandela traveled In January 1962', 'Mandela attend a conference of African nationalist leaders in Ethiopia', 'Mandela visit the exiled Oliver Tambo in London', 'Mandela undergo guerilla training in Algeria'])
        
    def test_negated_sentence_with_one_verb_negated(self):
        sentence_extracted = "He was educated at the Harrow prep school, where he performed so poorly that he did not even apply to Oxford or Cambridge."
        sentence_object = nlp(sentence_extracted)
        simple_sentences = extract_simple_sentences(sentence_object)
        self.assertListEqual(simple_sentences,['He educated at the Harrow prep school , where he performed so poorly that he did not even apply to Oxford or Cambridge', 'He educated .', 'He performed so poorly that he did not even apply to Oxford or Cambridge', 'He not apply to Oxford or Cambridge', 'He not apply that'])
        
        
    """
    TO-DO:
        subj-verb-multiple objects(of same type entities)
            eg. sachin played in Australia,India and England
        
        Negations (done only for one verb eg.'he did not even apply to Oxford or Cambridge'.) 
            eg. He did not even bother to give reply to him
            
    """
        
        
if __name__ == '__main__':
    unittest.main()
import dash_html_components as html
import dash_core_components as dcc
import random
from matstract.utils import open_db_connection
from chemdataextractor.doc import Text
import pickle
import os
from matstract.models.AnnotationBuilder import AnnotationBuilder

db = open_db_connection(db = "matstract_db")

def highlight_multiple(text, materials, color='Yellow'):
    for mat in materials:
        text = text.replace(mat, "<s>html.Mark('{}')<s>".format(mat))
    split = text.split('<s>')
    for (idx, token) in enumerate(split):
        try:
            split[idx] = eval(token)
            split[idx].style = {'background-color': color}
        except:
            pass

    return split

def reconstruct_text(text_as_tokens):
    reconstructed = []
    chunk = []
    for token in text_as_tokens:
        if type(token) == str:
            chunk.append(token)
        else:
            if chunk:
                reconstructed += [' '.join(chunk)]
                chunk = []
            reconstructed += [' ', token, ' '] if reconstructed else [token, ' ']
    if chunk:
        reconstructed += [' '.join(chunk)]
    return reconstructed

def highlight_colors(tag):

    colors_dict = {
        'CHM' : '#FFDC00', #yellow
        'MAT' : '#FF851B', #orange
        'REF' : '#FBCEB1', #apricot
        'DSC' : '#FF4136', #red
        'PRO' : '#0074D9', #blue
        'QUA' : '#0074D9', #blue #Remove QUA once clf is trained with new rules
        'PRC' : '#DDDDDD', #silver
        'MTC' : '#BFFF00', #lime
        'PVL' : '#7FDBFF', #aqua
        'PUT' : '#39CCCC', #teal
        'CON' : '#3D9970', #olive
        'CUT' : '#2ECC40', #green
        'CVL' : '#01FF70', #lime
        'SPL' : '#85144b', #maroon
        'SMT' : '#001f3f', #navy
        'CMT' : '#F012BE', #fuchsia
        'PMT' : '#B10DC9', #purple
        'APL' : '#AAAAAA' #gray
    }
    return colors_dict[tag]

def full_tag_names(tag):
    label_dict = {label['value']:label['text']  for label in  AnnotationBuilder.LABELS}
    label_dict['QUA'] = 'Quality'
    return label_dict[tag]

def highlight_ne(tagged_doc):
    ne_tagged_doc = []
    white_list = ['PRO', 'QUA', 'CON', 'DSC', 'SPL', 'SMT', 'PMT', 'CMT']
    for token, ne_tag in tagged_doc:
        if ne_tag == 'O':
            ne_tagged_doc.append(token)
        else:
            marked = html.Mark(token)
            color = highlight_colors(ne_tag[-3:])
            marked.style = {'background-color': color, 'color' : 'white' if ne_tag[-3:] in white_list else 'black'}
            ne_tagged_doc.append(marked)
    return ne_tagged_doc

def extract_ne(abstract):

    #load in a classifier
    classifier_location = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '../../nlp/lr_classifier.p')
    clf = pickle.load(open(classifier_location, 'rb'))

    #load in feature generator
    feature_generator_location = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '../../nlp/feature_generator.p')
    feature_generator = pickle.load(open(feature_generator_location, 'rb'))

    #tag and tokenize
    text = Text(abstract)
    tagged_tokens = text.pos_tagged_tokens

    #NE tag
    tagged_doc = []
    for sent in tagged_tokens:
        prev_BIO = '<out_of_bounds>'
        for idx, word_tag in enumerate(sent):
            predicted_BIO = clf.predict(feature_generator.transform(word_tag, sent, idx, prev_BIO))
            prev_BIO = predicted_BIO
            tagged_doc.append((word_tag[0], predicted_BIO[0]))


    #Unique list of NE tags found
    tags_found = list(set([BIO_tag[-3:] for word, BIO_tag in tagged_doc if BIO_tag != 'O']))
    tags_highlighted = []
    white_list = ['PRO', 'QUA', 'CON', 'DSC', 'SPL', 'SMT', 'PMT', 'CMT']
    for tag in tags_found:
        color = highlight_colors(tag)
        marked = html.Mark(full_tag_names(tag))
        marked.style = {'background-color': color, 'color' : 'white' if tag in white_list else 'black'}
        tags_highlighted.append(marked)
    #Add highlights and reconstruct
    return reconstruct_text(highlight_ne(tagged_doc)), tags_highlighted


def highlighter(text, parsed, missed):
    # sort both lists in order of increasing length
    # combine
    parsed = sorted(parsed, key=len, reverse=True)
    parsed = [(w, 'parsed') for w in parsed]
    missed = sorted(missed, key=len, reverse=True)
    missed = [(w, 'missed') for w in missed]
    chems = parsed + missed

    txt = [text]
    for (chem, key) in chems:
        tag_all = []
        for token in txt:
            if type(token) == str:
                color = 'Cyan' if key == 'parsed' else 'Orange'
                tag_all += highlight_multiple(token, [chem], color)
            else:
                tag_all.append(token)
        txt = tag_all

    return txt


def random_abstract():
    random_document = list(db.abstracts.aggregate([{"$sample": {"size": 1}}]))[0]
    return random_document['abstract']

# The Extract App
layout = html.Div([
    html.Div([
        html.Div([
            html.P('Matstract Extract: named entity extraction from text sources.')
        ], style={'margin-left': '10px'}),
        html.Label('Enter text for named entity extraction:'),
        html.Div(dcc.Textarea(id='extract-textarea',
                     style={"width": "100%"},
                     autoFocus=True,
                     spellCheck=True,
                     wrap=True,
                     placeholder='Paste abstract/other text here to extract named entity mentions.'
                     )),
        html.Div([html.Button('Extract Entities', id='extract-button'),
                  html.Button('Choose a random abstract', id = 'extract-random')]),
        html.Div(id='extract-highlighted'
        ),
        #html.Div(html.Label('Extracted:')),
        html.Div(id='extracted')
    ], className='twelve columns'),
])

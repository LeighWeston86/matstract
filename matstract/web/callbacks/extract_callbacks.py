from dash.dependencies import Input, Output, State
import dash_html_components as html
from matstract.models.database import AtlasConnection
from chemdataextractor.doc import Text
import pickle
import _pickle
import gzip
import os
from matstract.models.annotation_builder import AnnotationBuilder

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


def full_tag_names(tag):
    label_dict = {label['value']:label['text'] for label in AnnotationBuilder.LABELS}
    label_dict['QUA'] = 'Quality'
    return label_dict[tag]


def highlight_ne(tagged_doc):
    ne_tagged_doc = []
    for token, ne_tag in tagged_doc:
            ne_tagged_doc.append(html.Span(token, className="highlighted " + ne_tag[-3:]))
    return ne_tagged_doc


def extract_ne(abstract):

    # load classifier
    classifier_location = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '../../nlp/lr_classifier.p')
    with open(classifier_location, 'rb') as f:
        clf = _pickle.load(f)

    # load in feature generator
    feature_generator_location = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '../../nlp/feature_generator.p')
    with open(feature_generator_location, 'rb') as f:
        feature_generator = _pickle.load(f)

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
    for tag in tags_found:
        marked = html.Span(full_tag_names(tag), className="highlighted " + tag)
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
    # locations for relevant/not relevant classifier and vecotrizers
    models_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../nlp/')
    classifier_location = os.path.join(models_location, 'r_nr_classifier.p')
    cv_location = os.path.join(models_location, 'cv.p')
    tfidf_location = os.path.join(models_location, 'tfidf.p')

    # load in relevant/not-relevant classifier and vectorizers
    r_nr_clf = pickle.load(open(classifier_location, 'rb'))
    cv = pickle.load(open(cv_location, 'rb'))
    tfidf = pickle.load(open(tfidf_location, 'rb'))
    no_abstract = True
    random_abs = None
    db = AtlasConnection.db(local=True, db="production").db
    while no_abstract:
        random_document = list(db.abstracts.aggregate([{"$sample": {"size": 1}}]))[0]
        random_abs = random_document['abstract']
        vectorized = cv.transform([random_abs])
        transformed = tfidf.transform(vectorized)
        if r_nr_clf.predict(transformed):
            no_abstract = False
    return random_abs


def bind(app):
    ### Extract App Callbacks ###
    @app.callback(
        Output('extract-highlighted', 'children'),
        [Input('extract-button', 'n_clicks')],
        [State('extract-textarea', 'value')])
    def highlight_extracted(n_clicks, text):
        if n_clicks is not None:
            text, tags = extract_ne(text)
            spaced_tags = []
            for tag in tags:
                #spaced_tags += [tag, html.Span()]
                span = html.Span(tag)
                span.style = {'padding-right': '15px'}
                spaced_tags.append(span)
            return html.Div(text), html.Br(), html.Div(html.Label('Extracted Entity tags:')), html.Div(spaced_tags)

    @app.callback(
        Output('extract-textarea', 'value'),
        # Output('similar-textarea', 'value'),
        [Input("extract-random", 'n_clicks')])
    def get_random(n_clicks):
        if n_clicks is not None:
            text = random_abstract()
            return text
        return ""
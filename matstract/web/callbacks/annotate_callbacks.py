from dash.dependencies import Input, Output, State
import os
from matstract.models.annotation_builder import AnnotationBuilder
from matstract.models.annotation import TokenAnnotation, MacroAnnotation
from matstract.web.view import annotate_app
from matstract.web.view.annotate import token_ann_app, macro_ann_app
from matstract.models.database import AtlasConnection

db = AtlasConnection().db

def bind(app):
    def _auth_message(n_clicks, user_key):
        if n_clicks is not None:
            builder = AnnotationBuilder(local=True)
            if builder.get_username(user_key) is None:
                return "Not authorised - did not save!"
        return ""

    @app.callback(
        Output('annotation_message', 'children'),
        [Input('annotate_confirm', 'n_clicks'),
         Input('token_ann_flag', 'n_clicks'),
         Input('annotate_skip', 'n_clicks')],
        [State('user_key_input', 'value')])
    def annotation_message(confirm_click, flag_click, skip_click, user_key):
        if skip_click is not None:
            return _auth_message(None, user_key)
        if flag_click is not None:
            return _auth_message(flag_click, user_key)
        return _auth_message(confirm_click, user_key)

    @app.callback(
        Output('macro_ann_message', 'children'),
        [Input('macro_ann_confirm', 'n_clicks'),
         Input('macro_ann_not_rel', 'n_clicks'),
         Input('macro_ann_flag', 'n_clicks'),
         Input('macro_ann_skip', 'n_clicks')],
        [State('user_key_input', 'value')])
    def macro_ann_message(conf_click, not_rel_click, flag_click, skip_click, user_key):
        if skip_click is not None:
            return _auth_message(None, user_key)
        if conf_click is not None:
            return _auth_message(conf_click, user_key)
        elif flag_click is not None:
            return _auth_message(flag_click, user_key)
        return _auth_message(not_rel_click, user_key)


    # sets the user key every time it is updated
    @app.callback(
        Output('user_key', 'children'),
        [Input('user_key_input', 'value')])
    def set_user_key(user_key):
        return user_key

    # updates the authentication info with person's name
    @app.callback(
        Output('auth_info', 'children'),
        [Input('user_key_input', 'value')])
    def set_user_info(user_key):
        builder = AnnotationBuilder(local=True)
        username = builder.get_username(user_key)
        return annotate_app.serve_auth_info(username)


    @app.callback(
        Output('annotation_parent_div', 'children'),
        [Input('annotate_skip', 'n_clicks'),
         Input('annotate_confirm', 'n_clicks'),
         Input('token_ann_flag', 'n_clicks')],
        [State('annotation_container', 'tokens'),
         State('doi_container', 'children'),
         State('abstract_tags', 'value'),
         State('user_key_input', 'value'),
         State('annotation_labels', 'children'),
         State('annotation_container', 'passiveLabels')])
    def load_next_abstract(
            skip_clicks,
            confirm_clicks,
            flag_clicks,
            tokens,
            doi,
            abstract_tags,
            user_key,
            annotation_labels,
            previous_labels):
        labels = [label["value"] for label in AnnotationBuilder.LABELS]
        if annotation_labels is not None:
            labels = annotation_labels.split('&')
        new_labels = labels
        if len(previous_labels) > 0:
            new_labels = list(set(labels).union([label["value"] for label in previous_labels]))
        builder = AnnotationBuilder(local=True)
        if builder.get_username(user_key) is not None:
            if confirm_clicks is not None:
                tags = [tag["value"].lower() for tag in abstract_tags] if abstract_tags is not None else None
                annotation = TokenAnnotation(doi=doi,
                                             tokens=tokens,
                                             labels=new_labels,
                                             tags=tags,
                                             user=user_key)
                builder.insert(annotation, builder.ANNOTATION_COLLECTION)
                builder.update_tags(tags)
                doi = None
            elif flag_clicks is not None:
                macro_ann = MacroAnnotation(doi=doi,
                                            relevant=None,
                                            flag=True,
                                            abs_type=None,
                                            user=user_key)
                builder.insert(macro_ann, builder.MACRO_ANN_COLLECTION)
                doi = None
        if skip_clicks is not None:
            doi = None  # to load a new abstract
        past_tokens = tokens if doi is not None else None  # reload tokens from previous annotation
        return token_ann_app.serve_abstract(db,
                                            user_key,
                                            show_labels=labels,
                                            past_tokens=past_tokens,
                                            doi=doi)

    ## Macro Annotation Callbacks
    @app.callback(
        Output('macro_ann_parent_div', 'children'),
        [Input('macro_ann_not_rel', 'n_clicks'),
         Input('macro_ann_skip', 'n_clicks'),
         Input('macro_ann_confirm', 'n_clicks'),
         Input('macro_ann_flag', 'n_clicks')],
        [State('doi_container', 'children'),
         State('macro_ann_type', 'value'),
         State('user_key_input', 'value')])
    def load_next_macro_ann(
            not_rel_click,
            skip_click,
            confirm_click,
            flag_click,
            doi,
            abs_type,
            user_key):
        flag = False
        if confirm_click is not None:
            relevant = True
        elif not_rel_click is not None:
            relevant = False
        elif flag_click is not None:
            relevant = None
            flag = True
        else:  # either skip is clicked or first load
            return macro_ann_app.serve_plain_abstract()
        builder = AnnotationBuilder(local=True)
        if builder.get_username(user_key) is not None:
            macro_ann = MacroAnnotation(doi, relevant, flag, abs_type, user=user_key)
            builder.insert(macro_ann, builder.MACRO_ANN_COLLECTION)
        return macro_ann_app.serve_plain_abstract()

    @app.callback(
        Output('macro_ann_instructions', 'children'),
        [Input('url', 'pathname')])
    def load_instructions(_):
        full_path = os.path.join(os.getcwd(), 'matstract/web/static/docs/MACRO_help.md')
        with open(full_path, 'r') as instructions:
            text = instructions.read()
        return annotate_app.build_markdown(text)

    @app.callback(
        Output('annotation_instructions', 'children'),
        [Input('annotation_container', 'selectedValue')]
    )
    def load_instructions(selected_value):
        full_path = os.path.join(os.getcwd(), 'matstract/web/static/docs/', selected_value + '_help.md')
        with open(full_path, 'r') as instructions:
            text = instructions.read()
        return annotate_app.build_markdown(text)


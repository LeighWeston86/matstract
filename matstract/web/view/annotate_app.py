from matstract.web.view.annotate import token_ann_app, macro_ann_app, my_ann_app, diff_ann_app
import dash_html_components as html
import dash_core_components as dcc
from textwrap import dedent as s


def serve_layout(db, user_key, path):
    """Generates the layout dynamically on every refresh"""
    mode, attrs = get_ann_mode(path)

    if mode == "token":
        ann_app = token_ann_app
    elif mode == "my_annotations":
        ann_app = my_ann_app
    elif mode == "diff":
        ann_app = diff_ann_app
    else:
        ann_app = macro_ann_app

    return [serve_ann_options(),
            html.Div(
                serve_user_info(user_key),
                id="user_info_div",
                className="row",
                style={"textAlign": "right"}),
            html.Div(ann_app.serve_layout(db, user_key, attrs)),
            ]


def serve_auth_info(username):
    if username is not None and len(username) > 0:
        username_info = [html.Span("Annotating as "),
                         html.Span(username, style={"font-weight": "bold"}),
                         html.Span(" ( "),
                         dcc.Link("my annotations", href="/annotate/my_annotations"),
                         html.Span(" )")]
    else:
        username_info = "Not Authorised to annotate"
    return username_info


def serve_user_info(user_key):
    return [html.Div([
                html.Span("User key: "),
                dcc.Input(id='user_key_input',
                          type='text',
                          placeholder='Enter user key here.',
                          value=user_key,
                          style={"margin-bottom": "0", "height": "auto", "padding": "5px"}
                          )
            ]),
            html.Div(serve_auth_info(""), id="auth_info", style={"padding": "5px 10px 0px 0px"})]


def serve_ann_options():
    return html.Nav(children=[
                html.Span('Tasks: | '),
                dcc.Link("Macro", href="/annotate/macro", ),
                html.Span(' | '),
                dcc.Link("Materials", href="/annotate/token/CHM&MAT&REF&MTC&DSC"),
                html.Span(' | '),
                dcc.Link(
                    "Properties and Conditions",
                    href="/annotate/token/PRO&PVL&PUT&CON&CVL&CUT&PRC&SPL"),
                html.Span(' | '),
                dcc.Link("Methods and Applications", href="/annotate/token/SMT&CMT&PMT&APL"),
                html.Span(' | '),
                dcc.Link("All", href="/annotate/token/"),
                html.Span(' |'),
    ])


def get_ann_mode(path):
    mode,attrs = None, None
    if path.startswith('/annotate/token/'):
        mode = 'token'
        attrs = path.split('/')[3:]
    elif path.startswith('/annotate/token'):
        mode = path.split('/')[-1]
        attrs = path.split('/')[3:]
    elif path.startswith('/annotate/diff/'):
        mode = "diff"
        attrs = path.split('/')[3:]
    elif path.startswith('/annotate/'):
        mode = path.split('/')[-1]
        attrs = path.split('/')[2:]
    return mode, attrs


def build_markdown(text):
    return dcc.Markdown(s(text))

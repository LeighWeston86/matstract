from matstract.web.view.annotate import token_ann_app, macro_ann_app
import dash_html_components as html
import dash_core_components as dcc


def serve_layout(db, user_key, path):
    """Generates the layout dynamically on every refresh"""
    mode, attr = get_ann_mode(path)

    if mode == "token":
        ann_app = token_ann_app
    else:
        ann_app = macro_ann_app

    return [serve_ann_options(),
            html.Div(
                serve_user_info(user_key),
                id="user_info_div",
                className="row",
                style={"textAlign": "right"}),
            html.Div(ann_app.serve_layout(db, attr)),
            ]


def serve_auth_info(username):
    if username is not None and len(username) > 0:
        username_info = [html.Span("Annotating as "), html.Span(username, style={"font-weight": "bold"})]
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
                dcc.Link("Macro", href="/annotate//macro", ),
                html.Span(' | '),
                dcc.Link("Materials", href="/annotate/token/material"),
                html.Span(' | '),
                dcc.Link(
                    "Properties",
                    href="/annotate/token/property&property_value&property_unit"),
                html.Span(' | '),
                dcc.Link("Methods", href="/annotate/token/characterization_method&synthesis_method"),
                html.Span(' | '),
                dcc.Link("Applications", href="/annotate/token/application"),
                html.Span(' |'),
    ])


def get_ann_mode(path):
    mode, attr = None, None
    if path.startswith('/annotate/token/'):
        mode = 'token'
        attr = path.split('/')[-1]
        if attr == '':
            attr = None
    elif path.startswith('/annotate/token'):
        mode = path.split('/')[-1]
    elif path.startswith('/annotate/'):
        mode = path.split('/')[-1]
    return mode, attr
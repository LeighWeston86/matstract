import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objs as go
from matstract.nlp.data_preparation import DataPreparation


def serve_layout(db):
    """Generates the layout dynamically on every refresh"""

    return html.Div(serve_searchbox())


def serve_searchbox():
    return html.Div([
                html.Div([
                    html.Span("+"),
                    dcc.Input(id='matsearch_input',
                              placeholder='e.g. ferroelectric',
                              type='text'),
                    html.Span("-"),
                    dcc.Input(id='matsearch_negative_input',
                              placeholder='e.g. perovskite',
                              type='text'),
                    html.Span("+"),
                    dcc.Dropdown(id='has_elements',
                                 options=[{'label': el, "value": el} for el in DataPreparation.ELEMENTS],
                                 className="element_select",
                                 value=None,
                                 multi=True),
                    html.Span("-"),
                    dcc.Dropdown(id='n_has_elements',
                                 options=[{'label': el, "value": el} for el in DataPreparation.ELEMENTS],
                                 className="element_select",
                                 value=None,
                                 multi=True),
                    html.Button("Search", id="matsearch_button"),
                    ], className="row matsearch-div"),
                html.Div([html.Div(
                    serve_matlist([]),
                    id='relevant_materials_container',
                    # style={"maxHeight": "500px", "overflow": "scroll"},
                    className="six columns"),
                html.Div("", id="material_summary_div", className="six columns")], className="row")])


def matlist_figure(material_names, material_scores, material_counts):
    if len(material_names) == 0:
        return {}
    else:
        return {
            "data": [
                go.Bar(
                    x=list(reversed(material_scores)),
                    y=list(reversed(material_names)),
                    orientation='h',
                    marker=dict(color='rgb(158,202,225)'),
                    opacity=0.6,
                    name="score",
                    xaxis="x2"),
                go.Bar(
                    x=[0] * len(material_names),
                    y=list(reversed(material_names)),
                    orientation='h',
                    showlegend=False,
                    hoverinfo='none',
                    xaxis="x2"),
                go.Bar(
                    x=[0] * len(material_names),
                    y=list(reversed(material_names)),
                    orientation='h',
                    showlegend=False,
                    hoverinfo='none',
                ),
                go.Bar(
                    x=list(reversed(material_counts)),
                    y=list(reversed(material_names)),
                    orientation='h',
                    marker=dict(color='#1f77b4'),
                    name="mentions",
                    opacity=0.8),
            ],
            "layout": go.Layout(
                # title="Relevant materials",
                showlegend=False,
                legend=dict(orientation='h'),
                margin=go.Margin(l=150, pad=4, t=40),
                height=25 * len(material_scores),
                xaxis=dict(
                    title="mentions",
                    tickfont=dict(color='#1f77b4'),
                    titlefont=dict(color='#1f77b4'),
                ),
                xaxis2=dict(
                    tickfont=dict(color='rgb(158,202,225)'),
                    titlefont=dict(color='rgb(158,202,225)'),
                    title="score",
                    overlaying='x',
                    side='top'
                ),
                yaxis=dict(
                    tickangle=0,
                )
            ),
        }


def serve_matlist(matlist):
    # top materials by mention frequency
    material_names, material_scores, material_counts = [], [], []
    if len(matlist) > 0:
        material_names, material_scores, material_counts, _ = zip(*matlist)
    chart_materials = dcc.Graph(
        id="material_metrics",
        figure=matlist_figure(material_names, material_scores, material_counts)
    )
    return chart_materials

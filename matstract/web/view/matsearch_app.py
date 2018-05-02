import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objs as go


def serve_layout(db):
    """Generates the layout dynamically on every refresh"""

    return html.Div(serve_searchbox())


def serve_searchbox():
    return html.Div([
                html.Div([
                    dcc.Input(id='matsearch_input',
                              placeholder='e.g. Li-ion batteries',
                              type='text'),
                    html.Button("Search", id="matsearch_button"),
                    ]),
                html.Div('', id='relevant_materials_container')])


def serve_matlist(matlist):
    # top materials by mention frequency
    material_names, material_scores, material_counts = zip(*matlist)
    chart_materials = dcc.Graph(
        id="material_metrics",
        figure={
            "data": [
                go.Bar(
                    x=list(reversed(material_scores)),
                    y=list(reversed(material_names)),
                    orientation='h',
                    marker=dict(color='rgb(158,202,225)'),
                    opacity=0.6,
                    name="scores"),
                go.Bar(
                    x=[0] * len(matlist),
                    y=list(reversed(material_names)),
                    orientation='h',
                    showlegend=False,
                    hoverinfo='none',
                    name="scores"),
                go.Bar(
                    x=[0] * len(matlist),
                    y=list(reversed(material_names)),
                    orientation='h',
                    showlegend=False,
                    hoverinfo='none',
                    xaxis="x2"),
                go.Bar(
                    x=list(reversed(material_counts)),
                    y=list(reversed(material_names)),
                    orientation='h',
                    marker=dict(color='#1f77b4'),
                    name="count",
                    opacity=0.8,
                    xaxis="x2"),
            ],
            "layout": go.Layout(
                # title="Relevant materials",
                showlegend=False,
                legend=dict(orientation='h'),
                margin=go.Margin(l=150, pad=4),
                height=600,
                xaxis=dict(
                    title="score",
                    tickfont=dict(color='rgb(158,202,225)'),
                    titlefont=dict(color='rgb(158,202,225)'),
                ),
                xaxis2=dict(
                    tickfont=dict(color='#1f77b4'),
                    titlefont=dict(color='#1f77b4'),
                    title="# total mentions",
                    overlaying='x',
                    side='top'
                )
            ),
        }
    )
    return chart_materials

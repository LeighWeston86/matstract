import dash_html_components as html
import dash_core_components as dcc
import dash_materialsintelligence as dmi
from matstract.models.search import MatstractSearch


def search_html():
    return html.Div([
        html.Div(dcc.Input(
            id="search_input",
            type="text",
            autofocus=True,
            placeholder="Text search...",
            style={"width": "100%"}),
            style={"display": "table-cell", "width": "100%"}),
        html.Div(html.Button(
            "Search",
            className="button-search",
            id="search_btn"),
            style={"display": "table-cell", "verticalAlign": "top", "paddingLeft": "10px"})],
            className="row", style={"display": "table", "marginTop": "10px"}
        )


def serve_layout(path=None):
    if path is not None and len(path) > len("/search"):
        path = path[len("/search")+1::]
        path = path.replace("%20", " ")
    if path is not None:
        filter_value_material = path.split("/")
        if len(filter_value_material) == 3:
            options = [{'label': 'material:' + filter_value_material[2],
                        'value': 'material:' + filter_value_material[2]},
                       {'label': filter_value_material[0] + ':' + filter_value_material[1],
                        'value': filter_value_material[0] + ':' + filter_value_material[1]}]
            value = options
        else:
            options = []
            value = options
    return [search_html(),
    dmi.DropdownCreatable(
        options=options,
        multi=True,
        promptText="Add filter ",
        className="search-filters",
        placeholder="filter:value1,value2",
        value=value,
        id='search_filters'),
    html.Div(
        'Valid filters: ' + ', '.join(MatstractSearch.VALID_FILTERS),
        style={"color": "grey", "padding": "10px 1px", "fontSize": "10pt"},
        className="row"),
    html.Div("", id="search_results", className="row"),
    html.Div([
        html.Span("Attribution Notice: This data was downloaded from the Scopus API between January - July 2018"),
        html.Br(),
        html.Span(" via https://api.elsevier.com and https://www.scopus.com.")],
        style={
            "color": "grey",
            "textAlign": "center",
            "fontSize": "10pt",
            "marginTop": "30px"},
        className="row")]
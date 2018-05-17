import dash_html_components as html
from matstract.models.annotation_builder import AnnotationBuilder


def serve_layout(_, user_key, __):
    builder = AnnotationBuilder()
    leaderboard = builder.get_leaderboard(user_key)
    if leaderboard is not None:
        header = build_row([
            "User",
            "Macro Abstracts",
            "Token Abstracts",
            "Total Label Types"],
        "three columns table-header")
        user_rows = []
        for user in leaderboard:
            user_rows.append(build_row([
                builder.get_username(user),
                leaderboard[user]["macro_abstracts"],
                leaderboard[user]["token_abstracts"],
                leaderboard[user]["labels"],
            ], "three columns table-row"))

        return html.Div([html.H5("Annotation Leaderboard")] + [header] + user_rows)
    return "Not Authorized"


def build_row(array, classname):
    table_cells = []
    for elem in array:
        table_cells.append(html.Div(elem, className=classname))
    return html.Div(table_cells, className="row")


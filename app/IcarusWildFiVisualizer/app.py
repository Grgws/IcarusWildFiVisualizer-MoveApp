#%%
import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, ClientsideFunction
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots
import plotly.graph_objects as go
pio.templates.default = "plotly_white"
import flask

from dash.exceptions import PreventUpdate
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform, html

import dash_mantine_components as dmc
from dash_iconify import DashIconify

from . import config as cfg
from . import dataLoader as dl

from .components.TagSelectorModalAIO import TagSelectorModalAIO

server = flask.Flask(__name__)

app = DashProxy(
    # transforms=[MultiplexerTransform()],
    use_pages=True, 
    # Don't use auto imported pages as they don't support dash extensions transforms.
    # Instead we create dash extensions blueprints and register them manually
    pages_folder="",
    # suppress_callback_exceptions=True
    server=server,
    )

from .siteBlueprints.mapBlueprint import bp as mapPage
from .siteBlueprints.networkBlueprint import bp as networkPage
from .siteBlueprints.dataCheckBlueprint import bp as dataCheckPage

mapPage.register(app,"GPS",order=0, path="/")#,prefix="network")
networkPage.register(app,"PROXIMITY",order=1)#,prefix="network")
dataCheckPage.register(app,"DATACHECK",order=2)#,prefix="network")

(_, df, _, tagsDf) = dl.getData()

def getPageButtons(url):
    return [
        dmc.Anchor(
                    href=page["relative_path"],
                    children=[
                        dmc.Button(
                            page['module'],
                            ml=20,
                            id={'type':"page-btn", 'index': i},
                            variant=("filled" if page["path"] == url else "subtle")
                            )
                ])
                for i, page in enumerate(dash.page_registry.values())
    ]

# HACKY!: Page container from dash.py modified to have 100% height style for better layout with ag grid
hacky_page_container = html.Div(
    style={"height":"100%"},
    children=
    [
        dcc.Location(id=dash.dash._ID_LOCATION),
        html.Div(id=dash.dash._ID_CONTENT, disable_n_clicks=True, style={"height":"100%"}),
        dcc.Store(id=dash.dash._ID_STORE),
        html.Div(id=dash.dash._ID_DUMMY, disable_n_clicks=True),
    ]
)

app.layout = dmc.MantineProvider(
    withGlobalStyles=True,
    withNormalizeCSS=True,
    children=[
        html.Div(
            style={"display": "flex",
            "flex-direction": "column",
            "height": "100vh"}, 
            children=[
                dcc.Location(id='url', refresh=True),
                TagSelectorModalAIO(tagsDf.reset_index(), aio_id="tag-selector"),
                dcc.Store(
                    id=TagSelectorModalAIO.ids.selectedIdsStore("tag-selector"),
                    data=tagsDf.index.to_list(),
                    storage_type="local",
                ),
                dmc.Header(
                    className="header",
                    height=40,
                    position="right",
                    children=[
                          dmc.Title("WildFi Data Visualizer",order=4,id="title",style={"flex":"1"}),

                        html.Div(id="page-btns",children=getPageButtons("/")),

                        html.Div(
                            style={"flex":"1"},
                            children=[
                                dmc.Menu(
                                    trigger="hover",
                                    style={"width":"fit-content","margin-left": "auto"},
                                    children=[
                                        dmc.MenuTarget(
                                            dmc.ActionIcon(
                                                DashIconify(icon="clarity:settings-line", width=20),
                                                size="lg",
                                                variant="subtle",
                                                color="primary",
                                                style={}
                                            ),
                                        ),
                                        dmc.MenuDropdown(
                                            children=
                                            [
                                                dmc.MenuItem(
                                                    "Select tags to show",
                                                    id=TagSelectorModalAIO.ids.openBtn("tag-selector"),
                                                    icon=DashIconify(icon="clarity:filter-line", width=20),
                                                ),
                                            ]
                                        ),
                                    ]
                                ),
                            ]
                        ),
                    ]
                ),
                hacky_page_container
        ])
    ]
)

# Highlight correct page button
@app.callback(
    Output("page-btns","children"),
    Input("url","pathname"),
    # State({'type': 'filter-dropdown'},"nclicks")
)
def updatePageBtns(url):
    return getPageButtons(url)


# Run server when this script is executed
if __name__ == '__main__':
    if cfg.runOnGunicorn:
        # Start gunicorn from script (https://docs.gunicorn.org/en/latest/custom.html)
        # Alternatively run gunicorn via this command:
        #   gunicorn -b :8050 app:server --workers 1
        import gunicorn.app.base
        class StandaloneApplication(gunicorn.app.base.BaseApplication):

            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                config = {key: value for key, value in self.options.items()
                        if key in self.cfg.settings and value is not None}
                for key, value in config.items():
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        options = {
            'bind': '%s:%s' % ('127.0.0.1', '8050'),
            'workers': 5,
            'reload': True,
        }
        StandaloneApplication(server, options).run()

    else:
        # Run dash in debug mode if not running in debugger
        # https://stackoverflow.com/questions/53501352/how-to-run-dash-in-debug-mode-only-if-not-running-in-debugger
        import sys
        gettrace = getattr(sys, 'gettrace', None)   

        if gettrace is None or not gettrace():
            app.run_server(debug=True)
        else:
            app.run_server(debug=False)
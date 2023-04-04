import numpy as np

from dash import Dash, html, dcc, Input, Output, ctx, dash_table
import dash_ag_grid as dag
import dash
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go

from dash_extensions.enrich import  DashBlueprint

import dash_mantine_components as dmc
from dash_iconify import DashIconify

from .. import dataLoader as dl

from ..wildFiData import wildFiDataChecker as dataChecker

(badDf, _, _, _) = dl.getData()
# Convert list columns to string
badDf[["missingProxCols","missingGPSCols"]] = badDf[["missingProxCols","missingGPSCols"]].apply(lambda c: c.str.join(", "))


columns = ["tagId","utcDate","csvIndex","filename","duplicate","missingProxCols","missingGPSCols","accMalformed","proxMalformed","badProxCount","duplicateProxCount","badProxIds","duplicateProxIds"]
boolCols= ["duplicate","accMalformed","proxMalformed"]
nbrCols = ["badProxCount","duplicateProxCount"]
strCols = ["missingProxCols","missingGPSCols"]

bp = DashBlueprint()

# TODO: Show bad rows in measurments figure like on map page

#Basic layout of the website
bp.layout = dmc.LoadingOverlay(
    style={"height":"100%","font-family":"sans-serif"},
    children=[

        dag.AgGrid(
            columnDefs=[{"headerName":col, "field":col} for col in columns],
            rowData=badDf[badDf.anyProblems].to_dict('records'),
            # columnSize="autoSizeAll",
            columnSize="sizeToFit",
            defaultColDef=dict(
                filter=True,    
                # floatingFilter=True,
                resizable=True,
                sortable=True,
                editable=True,
            ),
            cellStyle={
                "styleConditions": 
                    [{
                        "condition": f"colDef.headerName == '{col}' && value", 
                        "style": {"backgroundColor": "red","color": "white"}
                    } for col in boolCols]
                    +
                    [{
                        "condition": f"colDef.headerName == '{col}' && value", 
                        "style": {"backgroundColor": "red","color": "white"}
                    } for col in nbrCols]
                    +
                    [{
                        "condition": f"colDef.headerName == '{col}' && (value != '' && value)", 
                        "style": {"backgroundColor": "red","color": "white"}
                    } for col in strCols]
                    ,
                
            },
            style={"height":"100%"}
        ),
        html.Div(
            style={"position": "absolute","left": "50px","bottom": "50px"},
            children=[
                dmc.Tooltip(
                    label="Download data as xlsx",
                    multiline=True,
                    position="top",
                    children=[
                        dmc.ActionIcon(
                            DashIconify(icon="ic:baseline-download",width=25),
                            id="badDataDlButton",
                            variant="light",
                            color="primary",
                            size="lg",
                        ),
                        dcc.Download(id="badDataDownload"),
                    ],
                ),
            ],
        ),
    ])

@bp.callback(
    Output("badDataDownload", "data"),
    Input("badDataDlButton", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    with np.printoptions(linewidth=100000): # Avoid newlines inserted by numpy to str conversion
        excelWriter = dataChecker.toFormattedExcel
        excelWriter.__name__ = "to_excel"
        return dcc.send_data_frame(excelWriter, "badRows.xlsx", df=badDf[columns], boolCols=boolCols, nbrCols=nbrCols, strCols=strCols)




if __name__ == '__main__':
    bp.run_server(debug=True, port=8051)

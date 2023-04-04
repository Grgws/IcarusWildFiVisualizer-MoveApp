import pandas as pd

from dash import Dash, html, dcc, Input, Output, ctx
import dash
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import  DashBlueprint
import plotly.express as px
import plotly.graph_objects as go
from .. import config as cfg
px.set_mapbox_access_token(cfg.mapBoxAccessToken)

import dash_mantine_components as dmc
from dash_iconify import DashIconify

from .. import dataLoader as dl
from ..wildFiData import wildFiImporter as wfi

from ..components.TagSelectorModalAIO import TagSelectorModalAIO


(_, df, edgeDf, tagsDf) = dl.getData()


# Read in the Point Of Interest data
# poiPath = "/home/gwilbs/vscode/WildFiTest/Cyprus/Data/MetaData/mapPoints6.csv"
# poisDf = pd.read_csv(poiPath, sep=";")

#Options for the dropdowns
tagIds = df.tagId.unique().tolist()
mapDataStyles = ["tracks","proxPoints"]
mapBackgroundStyles = ["open-street-map","stamen-terrain","basic", "streets", "outdoors", "light", "dark", "satellite","satellite-streets"]
measColors = ["proxCount","VeDBAMean","ODBAMean","GPS","locationCategory"]
accVars = wfi.getAccBurstDf(df.iloc[0,]).columns.to_list()


bp = DashBlueprint()

#Basic layout of the website
bp.layout = html.Div([
    html.Div([

        dmc.LoadingOverlay(
            zIndex=50,
            style={"height": "100%"},
            children=[
                dcc.Graph(
                    id='mapFig',
                    config=dict(
                        # displayModeBar=True,
                        displaylogo=False,
                        showAxisRangeEntryBoxes=True, # Click on left or right axis label to enter displayed range
                        showSendToCloud=True,
                        plotlyServerURL="https://chart-studio.plotly.com"
                    )
                ),
                dmc.Group(
                    style={"position": "absolute","bottom": "10px","left": "10px","align-items": "end"},
                    children=[
                        dmc.Select(
                            label="Map type",
                            id = 'mapDataStyleSelector',
                            data=mapDataStyles,
                            value="proxPoints",
                            placeholder="Select map type",
                            clearable=False,
                            size="xs",
                            style={"z-index":"5"}, # Put this selector infront of mapbox badge
                            persistence = True,
                            persistence_type="local",
                        ),
                        dmc.Select(
                            label="Map background",
                            id = 'mapBackgroundStyleSelector',
                            data=mapBackgroundStyles,
                            value="outdoors",
                            placeholder="Select map background style",
                            clearable=False,
                            size="xs",
                            persistence = True,
                            persistence_type="local",
                        ),
                        dmc.ActionIcon(
                                    DashIconify(icon="ic:baseline-download",width=20),
                                    id="mapDlButton",
                                    variant="light",
                                    color="primary",
                                    # size="lg",
                                ),
                        # dmc.Button("Download Map",id="mapDlButton",size="xs",variant="light"),
                        dcc.Download(id="mapDownload"),
                    ],
                )
            ],
        ),

        dmc.LoadingOverlay(
            zIndex=50,
            style={"height": "100%"},
            children=[
                dcc.Graph(
                    id='measFig',
                    config=dict(
                            # displayModeBar=True,
                            displaylogo=False,
                            showAxisRangeEntryBoxes=True, # Click on left or right axis label to enter displayed range
                            showSendToCloud=True,
                            plotlyServerURL="https://chart-studio.plotly.com"
                        )
                ),
                dmc.Select(
                    label="Color by",
                    id = 'metricVarSelector',
                    data=measColors,
                    value="GPS",
                    placeholder="Select a variable to color the graph below",
                    style={"position": "absolute","top": "0","left": "10px","right":"10px","width":"15%"},
                    size="xs",
                    persistence = True,
                    persistence_type="local",
                    # clearable=True,
                ),
            ],
        ),


        dmc.LoadingOverlay(
            zIndex=50,
            style={"height": "100%"},
            children=[
                dcc.Graph(
                    id='accFig',
                    config=dict(
                        # displayModeBar=True,
                        displaylogo=False,
                        showAxisRangeEntryBoxes=True, # Click on left or right axis label to enter displayed range
                        showSendToCloud=True,
                        plotlyServerURL="https://chart-studio.plotly.com"
                    )
                ),
                # Wrapped in div to make dropdown inside hideable
                html.Div(
                    style= {'display': 'none', 'position': 'absolute', 'bottom': '10px', 'left': '10px'},
                    id = 'accVarSelectorContainer',
                    children=[
                        dmc.Select(
                            label="Variable to show",
                            id = 'accVarSelector',
                            data=accVars,
                            value=accVars[4],
                            clearable=False,
                            size="xs",
                            persistence = True,
                            persistence_type="local",
                        ),
                    ], 
                ),
            ],
        ),
    
    ]),

    dcc.Store(id='currentlyShownAccPoints')
],style={"font-family":"sans-serif"}
    )

# Update map figure based on selected tagIds, mapDataStyle, mapBackground, and
# hover/selection in the measurment graph. On press of mapDlButton html file of current map
# plot is generated and downloaded
@bp.callback(
    Output('mapFig', 'figure'),
    Output('mapDownload','data'),
    Input(TagSelectorModalAIO.ids.selectedIdsStore("tag-selector"), 'data'),
    Input('mapDataStyleSelector', 'value'),
    Input('mapBackgroundStyleSelector', 'value'),
    Input('measFig', 'selectedData'),
    Input('mapDlButton', 'n_clicks'))
def updateMapFig(tagIds, dataStyle, mapStyle, selectedTimePoints, dlClicks):
    # TODO: Abstract tracks and prox mode -> showtracks=True/False and color=var

    if(not tagIds): 
        raise PreventUpdate

    # If specific points are selected in the measurement graph, only show those
    if selectedTimePoints:
        points = selectedTimePoints["points"]
        selIdx = [p["customdata"][0] for p in points] # Index is stored in customdata property of points
        plotDf = df.loc[selIdx,:]
        plotDf = plotDf[plotDf.lat.notna() & (plotDf.proxCount >= 1)]
    else:
        plotDf = df[df.lat.notna() & df.tagId.isin(tagIds) & ((df.proxCount >= 1) if dataStyle == "proxPoints" else True)]
    if(plotDf.empty):
        raise PreventUpdate

    # good options for mapbox_style without api key: open-street-map, stamen-terrain
    # api key needed for: "basic", "streets", "outdoors", "light", "dark", "satellite", or "satellite-streets"
    # If map is white it is moste likely due to the api key not being set while using a mapbox_style that requires it
    if (dataStyle == "tracks"):
        fig = px.line_mapbox(plotDf, lat="lat", lon="lon",color="tagId", hover_data=["time"],custom_data=[plotDf.index],
                            mapbox_style=mapStyle)
        #Also show points
        fig.update_traces(mode="markers+lines")
        fig.update_traces(selected_marker=dict(size=15),marker=dict(size=4))
        # fig.update_traces(line=dict(opacity=.3))
    if (dataStyle == "proxPoints"):
        fig = px.scatter_mapbox(plotDf, lat="lat", lon="lon",color="proxCount", 
                            hover_data=["tagId","time","proxIdBurstSorted","ttfSeconds","gpsTimeDiff"],
                            mapbox_style=mapStyle,
                            custom_data=[plotDf.index],
                            range_color=[0,8])
        # fig2 = px.scatter_mapbox(plotDf, lat="lat_GPS", lon="lon_GPS",color="proxCount", hover_data=["time","proxIdBurstSorted"],custom_data=[plotDf.index],mapbox_style="open-street-map")
        fig.update_traces(selected_marker=dict(size=15),marker=dict(size=4))

   #Show POIs (to display text over points mapbox styles with api key need to be used)
    # poiFig = px.scatter_mapbox(poisDf[poisDf.lat.notna()],lat="lat",lon="lon",color="visited_category",hover_data=["name","description"],
    #                             mapbox_style=mapStyle,
    #                             text="name",
    #                             color_discrete_map={"visited":"green","pending":"red","backlog":"grey"})
    # poiFig.update_traces(marker=dict(size=10))
    # poiFig.update_traces(mode="text+markers",textposition="top center")
    # poiFig.update_layout(font_color="white")

    # fig = px.density_mapbox(df[df.lat.notna() & df.tagId.isin(tagIds)], lat="lat", lon="lon",radius=10, hover_data=["time"],mapbox_style="open-street-map")
    fig.update_layout(mapbox_zoom=10)
    # fig.update_layout(mapbox_uirevision=mapStyle)
    colorQuantiles = plotDf.proxCount.quantile([0,.99]).values
    fig =  {
            'data': fig.data,#+poiFig.data, #fig.data,
            'layout': {
                # https://community.plotly.com/t/preserving-ui-state-like-zoom-in-dcc-graph-with-uirevision-with-dash/15793
                # -> If the value of UI revision is the same as in previous return, the UI state will be preserved.
                # 'uirevision': True,
                'clickmode': 'event+select',
                'margin':{'l':0, 'b': 0, 't': 0, 'r': 0},
                'coloraxis':{
                    'colorscale':[[0,"#BAA6DF"],[1,"#39008F"]],#px.colors.get_colorscale("Teal"),
                    'cmax':colorQuantiles[1],
                    'cmin':colorQuantiles[0],
                    'colorbar':{
                        'len':0.9,
                        'x':1.02,
                        'y':0.07,
                        'yanchor':'bottom',
                        'title':{'text':'Proximity<br>Count'},
                    }
                },#fig.layout.coloraxis,
                'legend':{'y':0.95},
                'mapbox': fig.layout.mapbox,
                'modebar':{'orientation':'h'},
                'height':500,
            }
        }

    # Download btn pressed?
    mapDl = None
    if( ctx.triggered_id == "mapDlButton"):
        exportFig = fig
        exportFig["layout"].pop("height")
        go.Figure(exportFig).write_html(f"export.html")
        mapDl = dcc.send_file(f"export.html")


    return [fig, dash.no_update if not mapDl else mapDl]



# Update measurments figure when selected tagIds or metricVar changes or data is selected
# on map
@bp.callback(
    Output('measFig', 'figure'),
    Output('metricVarSelector', 'value'),
    Input(TagSelectorModalAIO.ids.selectedIdsStore("tag-selector"), 'data'),
    Input('metricVarSelector', 'value'),
    Input('mapFig', 'selectedData'),)
def updateMeasFig(tagIds,metricVar, selectedMapPoints):
    if(not tagIds): 
        raise PreventUpdate

    # Set metricVar to gps (to show GPS points) when GPS points are selected on map
    metricVar = "gps" if (selectedMapPoints and ctx.triggered_id == "mapFig") else metricVar
    
    # plotDf = df[(df.lon.isna() if metricVar != "gps" else True) & df.tagId.isin(tagIds)]
    plotDf = df[df.tagId.isin(tagIds)] # Don't filter out GPS points, if they are already merged to prox by importer

    fig = px.scatter(plotDf,
                        "time","tagId",
                        color=metricVar,
                        hover_data=(["proxCount"] ),
                        custom_data=[plotDf.index], # For easier matching of selected data points
                        color_continuous_scale="agsunset")#,facet_row="wrapType")
    if(selectedMapPoints and metricVar == "GPS"):
        # print(json.dumps(selectedMapPoints["points"], indent=4))
        selIdxs = [p["customdata"][0] for p in selectedMapPoints["points"]]
        selPoints = plotDf[plotDf.GPS].reset_index(names=["origIdx"]).origIdx.isin(selIdxs)
        fig.data[1]["selectedpoints"] = selPoints[selPoints.values].index.tolist()
        
    fig.layout = {
                # https://community.plotly.com/t/preserving-ui-state-like-zoom-in-dcc-graph-with-uirevision-with-dash/15793
                # -> If the value of UI revision is the same as in previous return, the UI state will be preserved.
                'uirevision': True,
                'xaxis':{'title': {'text': "Time"}},
                'yaxis':{'title': {'text': "TagId"}},
                'clickmode': 'event+select',
                'margin':{'l':60, 'b': 60, 't': 45, 'r': 0},
                'modebar':{'orientation':'v'},
                'coloraxis':{
                    'colorbar':{
                        'orientation':'h',
                        'thickness':20,
                        'xanchor':'left',
                        'len':0.78,
                        'x':0.155,
                        'ypad':8,
                        'ticklabelposition':'inside'
                    }
                },
                'legend':{
                    'orientation':'h',
                    'xanchor':'left',
                    'x':0.155,
                    'y':1.1,
                    'yanchor':'top',
                    'title':{
                        'text':metricVar+":",
                        'side':'top'
                    }
                }

            }
    return [
        fig,
        dash.no_update # If GPS not merged: ("GPS" if (selectedMapPoints and ctx.triggered_id == "mapFig") else dash.no_update)
        ]

# Update the acc graph based on hover or selection in the measurment graph and the
# selected accVar if multiple datapoints are selected
@bp.callback(
    Output('accFig', 'figure'),
    Output('accVarSelectorContainer', 'style'),
    Output('currentlyShownAccPoints', 'data'),
    Input('measFig', 'hoverData'),
    Input('measFig', 'selectedData'),
    Input('currentlyShownAccPoints', 'data'),
    Input('accVarSelector', 'value'))
def updateAccFig(hoverPoints, selectedTimePoints, shownPoints, accVar):
    # No hover or selected data -> return empty figure
    if(not hoverPoints and not selectedTimePoints): 
        return [{
                'layout': {
                    # https://community.plotly.com/t/preserving-ui-state-like-zoom-in-dcc-graph-with-uirevision-with-dash/15793
                    # -> If the value of UI revision is the same as in previous return, the UI state will be preserved.
                    'uirevision': True,
                    'title': f"Hover over or select a point to see acc data",
                    'yaxis':{'range':[-3,3] },
                    'margin':{'l':40, 'b': 40, 't': 40, 'r': 0},

                }
            },
            {'display': 'none'},
            None
            ]
    # print(hoverPoints)
    # Show data for selected points if available and 5 or less points are selected otherwise show hover points
    points = selectedTimePoints if (selectedTimePoints and len(selectedTimePoints["points"]) <= 50) else hoverPoints

    points = [p for p in points["points"]]# When GPS not merged: [p for p in points["points"] if p["curveNumber"] == 0]
    # And return if no points left also no acc points are hovered
    if(not points and len(points:=hoverPoints["points"]) == 0): # or when gps not merged: points:=[p for p in hoverPoints["points"] if p["curveNumber"]== 0]
        raise PreventUpdate

    # Skip updates if points are the same as before 
    #  (avoids lengthy hover updates when many points are selected and mouse is moved over the graph)
    if (points == shownPoints):
        raise PreventUpdate


    # Get acc data for points(s)
    selIdx = [p["customdata"][0] for p in points] # Index is stored in customdata property of points
    selDf = df.loc[selIdx,:]
    # accDfs = selDf[selDf.gps == "PROX"].apply(lambda row: wfi.getAccBurstDf(row),axis=1).values.tolist()
    accDfs = selDf.apply(lambda row: wfi.getAccBurstDf(row),axis=1).values.tolist()
        
    # Multiple points selected?
    multisel = len(points) > 1
    if(multisel):
        # print(json.dumps(selectedTimePoints, indent=4))
        # Add unified identifier column
        for accDf, (idx, row) in zip(accDfs,selDf.iterrows()):
            accDf["point"] = f"{row.tagId} {row.time}"

        accDf = pd.concat(accDfs)
        fig = px.line(accDf, y=accVar, color="point")
    
    # Single point selected
    else:
        # Generate plotly express figure and then only update the data
        fig = px.line(accDfs[0])
    return [{
                'data': fig.data,
                'layout': {
                    # https://community.plotly.com/t/preserving-ui-state-like-zoom-in-dcc-graph-with-uirevision-with-dash/15793
                    # -> If the value of UI revision is the same as in previous return, the UI state will be preserved.
                    'uirevision': True,
                    'title': (f"Acc data for {selDf.iloc[0].tagId} at {selDf.iloc[0].time}+X") if not multisel else f"{accVar} data for selected points",
                    'xaxis':{'title': {'text': "Time (ms)"}},
                    'yaxis':{'title': {'text': "Acceleration (g)"},'range':[-3,3]},
                    'margin':{'l':40, 'b': 40, 't': 40, 'r': 0},
                }
            },
            {'display': ('none' if not multisel else 'block')},
            points
            ]



# if __name__ == '__main__':
#     bp.run_server(debug=True, port=8051)

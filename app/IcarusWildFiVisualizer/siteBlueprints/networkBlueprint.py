from datetime import datetime
import time
import random
import json

import pandas as pd
import numpy as np
import networkx as nx

import dash
from dash import Dash, callback, clientside_callback,html, dcc, Input, Output, State, ctx, ClientsideFunction
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots
import plotly.graph_objects as go
pio.templates.default = "plotly_white"

from dash.exceptions import PreventUpdate
from dash_extensions.enrich import  DashBlueprint, Output, DashProxy, Input, MultiplexerTransform, html

import dash_mantine_components as dmc
from dash_iconify import DashIconify
# import dash_renderjson

from .. import dataLoader as dl
from ..wildFiData.proximity import proxVis as pv

from .. import config as cfg

from ..components.TagSelectorModalAIO import TagSelectorModalAIO

timeFormat = "%d.%m.%Y %H:%M:%S" # For displaying time 

aggVarTimeOptions = {"night":{"freq":"d","offset":"-12H"},"day":{"freq":"d"},"hour":{"freq":"h"},"30min":{"freq":"30min"},"15min":{"freq":"15min"},"5min":{"freq":"5min"}}
aggVarColumnOptions = ["locationCategory","GPS"]
aggVarOptions = aggVarColumnOptions + list(aggVarTimeOptions.keys())
aggValsDescText = {
    "locationCategory":"""**Unknown:** No GPS fix was obtained and no gateways with locationCategory field set were in proximity of tag.
                          **Outside:** GPS fix was obtained or gateway with locationCategory field set to Outside was in proximity
                          **xyz:** No GPS fix was obtained while gateway with locationCategory field set to xyz was in proximity""",
    "GPS":"""**True:** GPS fix was obtained
             **False:** No GPS fix was obtained""",
    "night":"Timespans of 24h start at the stated time respectively.",
    "day":"Timespans of 24h start at the stated time respectively.",
    "hour":"Timespans of 1h start at the stated time respectively.",
    "30min":"Timespans of 30min start at the stated time respectively.",
    "15min":"Timespans of 15min start at the stated time respectively.",
    "5min":"Timespans of 5min start at the stated time respectively.",
}

defaultAggValToShow = 4 # Max number of values to select by default after agg variable was selected
maxAggValToShow = 10 # Max number of values to show in graph before refusing to show graph

colorVarOptions = ["temperatureInDegCel","humidityInPercent","pressureInHPA","proxCount","VeDBAMean","ODBAMean","hdop","ttfSeconds"]

(_, df, edgeDf, tagsDf) = dl.getData()

#%%    

# app = dash.Dash(__name__)
proxyLocation = html.Div() # Proxy store elements of MultiplexerTransform will be stored in this
# div so that Loading element above sees correct loading state
# MultiplexerTransform is needed to output data to the graphFig from server and clientside callback
# app = DashProxy(transforms=[MultiplexerTransform(proxy_location=proxyLocation)])
bp = DashBlueprint(transforms=[MultiplexerTransform(proxy_location=proxyLocation)])


bp.layout = dmc.NotificationsProvider([
    html.Div(id="notificationsContainer"),
    dmc.Group(
        p="xs",
        spacing="sm",
        style={"height":"250px","width":"100%","align-items": "flex-start"},
        children=[
            dmc.Paper(
                p="3px",
                withBorder=True,
                shadow="xs",
                style={"alignItems": "flex-end","flex-grow": "1", "height": "100%"},
                children=[
                    dmc.LoadingOverlay(
                        zIndex=50,
                        style={"height": "100%"},
                        children=[
                            dcc.Graph(
                                id='timeSelFig',
                                responsive=True,
                                style={"height": "100%"},
                                config=dict(
                                    displayModeBar=False,
                                    displaylogo=False,
                                    showAxisRangeEntryBoxes=True, # Click on left or right axis label to enter displayed range
                                    showSendToCloud=True,
                                    plotlyServerURL="https://chart-studio.plotly.com"
                                )
                            ),
                            dmc.Title(
                                "Time",
                                order=4,
                                style={
                                            "position": "absolute",
                                            "top": "10px",
                                            "left": "20px"
                                        }
                            ),
                            html.Div(
                                style={
                                            "position": "absolute",
                                            "bottom": "10px",
                                            "right": "10px"
                                        },
                                children=[
                                    dmc.Tooltip(
                                        label="Show network for selected timespan",
                                        multiline=True,
                                        width=110,
                                        children=[
                                            dmc.Button(
                                                "Update",
                                                id="updateButton",
                                                
                                            ),
                                        ],
                                    ),
                                ],
                            )
                        ],
                    ),
                ]
            ),
            dmc.Paper(
                p="xs",
                withBorder=True,
                shadow="xs",
                style={"alignItems": "flex-end"},
                children=[
                    dmc.Title("Variables", order=4),
                    dmc.HoverCard(
                        id="aggHoverCard",
                        withArrow=True,
                        position="left",
                        shadow="md",
                        children=[
                            dmc.HoverCardTarget(
                                dmc.Select(
                                    label="Aggregate by",
                                    id='aggVarSelector',
                                    data=aggVarOptions,
                                    value=aggVarOptions[0],
                                    searchable=True,
                                    # description="Select variable to aggregate by",
                                    placeholder="Nothing",
                                    nothingFound="Nothing found",
                                    clearable=True,
                                    zIndex=100
                                )
                            ),
                            dmc.HoverCardDropdown(
                                children=[
                                    dmc.Text(
                                        "Values to show in graph",
                                        size="sm",
                                        mb="sm",
                                        align="left"
                                    ),
                                    dmc.MultiSelect(
                                        id='aggValSelector',
                                        placeholder="Select at least one value",
                                        searchable=True,
                                        nothingFound="Nothing found",
                                        # debounce=2000, # <- debounce not working with multi select
                                        size="sm",
                                        style={"max-width": "200px"},
                                        zIndex=100
                                    ),
                                    dcc.Markdown(
                                        children="",
                                        id="aggValsDescText",
                                        style={
                                            "white-space": "pre-line",
                                            "font-size": "12px",
                                            "margin-top": "15px",
                                            "margin-left": "8px",
                                            "max-width": "200px"},
                                    ),
                                ]
                            ),
                        ],
                    ),
                    dmc.Select(
                        label="Color",
                        id='colorVarSelector',
                        data=colorVarOptions,
                        value=colorVarOptions[0],
                        searchable=True,
                        nothingFound="Nothing found",
                        zIndex=100
                    ),
                ],
            ),
            dmc.Paper(
                p="xs",
                withBorder=True,
                shadow="xs",
                style={"alignItems": "flex-end"},
                children=[
                    dmc.Title("Layout", order=4),
                    dmc.Group(
                        children=[
                            dmc.NumberInput(
                                id="seedInput",
                                label="Seed",
                                value=random.randint(0, 100),
                                debounce=500,
                                hideControls=True,
                                style={"width": "50px"}
                            ),
                            dmc.Button("Random Seed", id="randomSeedButton", variant="light"),
                        ],
                        style={"alignItems": "flex-end"}
                    ),
                    dmc.NumberInput(
                        id="layoutIterationsInput",
                        label="Max iterations",
                        value=100,
                        max=1000,
                        min=1,
                        step=50,
                        debounce=500
                    ),
                    dmc.NumberInput(
                        id="layoutDistanceInput",
                        label="K - Optimal distance",
                        value=3,
                        max=100,
                        min=0.1,
                        step=1,
                        precision=1,
                        debounce=500
                    ),
                ],
            ),
        ]),
        # TODO: Add range sliders for rssi and prox count filtering
        dmc.LoadingOverlay(
            zIndex=50,
            children=[
                dcc.Graph(id='graphFig',
                            config=dict(
                                showSendToCloud =True,
                                plotlyServerURL = "https://chart-studio.plotly.com",
                                scrollZoom = True,
                                #TODO: Add scroll zoom toggle
                                ),
                            # style={"height":"600px"},
                            ),
                proxyLocation,
                html.Div(
                    style={"position": "absolute","top": "20px","right": "130px"},
                    children=[
                        dmc.Tooltip(
                            label="Download proximity graph",
                            multiline=True,
                            position="bottom",
                            children=[
                                dmc.ActionIcon(
                                    DashIconify(icon="ic:baseline-download",width=20),
                                    id="proxDlButton",
                                    variant="light",
                                    color="primary",
                                    size="lg",
                                ),
                                dcc.Download(id="proxDownload"),
                            ],
                        ),
                    ],
                ),
        ]),
        # html.Pre(id='json'),
        dcc.Store(id="graphMeta"),
        dcc.Store(id="graphSubplotRowCnt", data=1)

])
        


@bp.callback(
    Output('aggValSelector', 'data'),
    Output('aggValSelector', 'value'),
    Output('aggValSelector', 'error'),
    Output('aggValsDescText', 'children'),
    Output("aggHoverCard","disabled"),
    Input('aggVarSelector', 'value'),
    State('timeSelFig', 'relayoutData'),
    Input('updateButton', 'n_clicks'),
    Input(TagSelectorModalAIO.ids.selectedIdsStore("tag-selector"), 'data'))
def updateAggValSelector(aggVar,timeSelFigRelayoutData,_,tagIds):
    if not aggVar:
        return [],[],"","",True

    # Filter for selected time on edgeDf so only agg Vals that have prox data in the
    # selected timespan are shown
    aggVals = edgeDf[getTimeFilter(edgeDf.time,timeSelFigRelayoutData) & edgeDf.sendId.isin(tagIds) & edgeDf.recvId.isin(tagIds)]\
                .groupby(getAggGrouper(aggVar), observed=True, as_index=False)\
                .size().query("size>0")

    aggVals = aggValToStr(list(aggVals.iloc[:,0]))
    
    if len(aggVals) > defaultAggValToShow:
        error = f"Only showing a subset of {len(aggVals)} aggregation values!"
        return aggVals,aggVals[:defaultAggValToShow],error,aggValsDescText.get(aggVar,""),False
    else:
        return aggVals,aggVals,"",aggValsDescText.get(aggVar,""),False

    # aggVals = aggValToStr(
    #             list(
    #                 # Filter on edgeDf so only agg Vals that have prox data are shown
    #                 edgeDf[getTimeFilter(edgeDf.time,timeSelFigRelayoutData)] # Filter by selected time so that we only show values that have data for the selected time
    #                     .groupby(getAggGrouper(aggVar),sort=True, observed=True)
    #                     .groups.keys()
    #                 )
    #             )




@bp.callback(
    Output('timeSelFig', 'figure'),
    Input('aggVarSelector', 'value'),
    Input(TagSelectorModalAIO.ids.selectedIdsStore("tag-selector"), 'data'))
def updateTimeFig(aggVar,tagIds):
    dataCountsDf = df[df.tagId.isin(tagIds)].groupby(["GPS","time"]).size().rename("size").reset_index()
    fig = px.area(dataCountsDf,"time","size",color="GPS",category_orders ={"GPS":[True,False]})
    fig.update_layout(xaxis_rangeslider=dict(visible=True))
    # fig.update_layout(dragmode="select")
    # fig.update_layout(activeselection_fillcolor="rgba(255,255,255,0.4)")
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, title=None)
    fig.update_layout({
                # https://community.plotly.com/t/preserving-ui-state-like-zoom-in-dcc-graph-with-uirevision-with-dash/15793
                # -> If the value of UI revision is the same as in previous return, the UI state will be preserved.
                'uirevision': True,
                'hovermode': 'x unified', # Show one tooltip for all traces
                'margin':{'l':0, 'b': 8, 't': 0, 'r': 0},
                'legend':{
                    'xanchor':'right',
                    'x':1,
                    'bgcolor':'rgba(255, 255, 255, 0.0)',
                },
                'xaxis':{
                    'title':None,
                    'showgrid':False,
                    'showticklabels':True,
                    'rangeslider':{
                        'visible':True,
                        'range':[dataCountsDf.time.min(),dataCountsDf.time.max()],
                    },
                    'range':[dataCountsDf.time.min(),dataCountsDf.time.max()],
                    'rangeselector':{
                        'xanchor':'center',
                        'x':0.5,
                        'yanchor':'top',
                        'y':0.95,
                        'buttons':[
                            {
                                'step':'all',
                            },
                            {
                                'count':1,
                                'step':'day',
                                'stepmode':'backward',
                            },
                            {
                                'count':12,
                                'step':'hour',
                                'stepmode':'backward',
                            },
                            {
                                'count':6,
                                'step':'hour',
                                'stepmode':'backward',
                            },
                            {
                                'count':3,
                                'step':'hour',
                                'stepmode':'backward',
                            },
                            {
                                'count':1,
                                'step':'hour',
                                'stepmode':'backward',
                            },
                        ]
                    },
                },
                'yaxis':{
                    'title':None,
                    'ticklabelposition':'inside',
                    # 'rangeslider':{'visible':True},
                    'showgrid':False,
                    'nticks':4,
                    'showticklabels':True,
                }
            })
    return fig

# Download prox fig -> needs to happen based on clients representation of graphFig to
# include highlighted nodes in export
@bp.callback(
    Output('proxDownload', 'data'),
    Input('proxDlButton', 'n_clicks'),
    State('graphFig', 'figure'),
    State('timeSelFig', 'relayoutData'),
    State('colorVarSelector', 'value'),
    )
def downloadProxFig(n_clicks,graphFig,timeSelFigRelayoutData,colorVar):
    if n_clicks is None or graphFig is None:
        return dash.no_update

    # Replace None colors with np.nan so that they can be converted to figure object by plotly
    for trace in graphFig["data"]:
        if "color" in trace["marker"]:
            trace["marker"]["color"] = [ (color if color else np.nan) for color in trace["marker"]["color"] ]

    (tStart, tEnd) = getTimeFilterBounds(timeSelFigRelayoutData)
    if(tStart is None or tEnd is None):
        # Determine min/max time from df
        tStart = df.time.min().strftime(timeFormat)
        tEnd = df.time.max().strftime(timeFormat)
    else:
        tStart = pd.Timestamp(tStart).strftime(timeFormat)
        tEnd = pd.Timestamp(tEnd).strftime(timeFormat)

    dlFig = go.Figure(graphFig)
    dlFig.update_layout(
        dict(
            margin=dict(t=60),
            title=dict(text=f"Proximity Graph from {tStart} to {tEnd} colored by {colorVar}"),
        )
    )
    dlFig.layout.pop("height")

    dlFig.write_html(f"export.html",config=dict(scrollZoom = True))
    return dcc.send_file(f"export.html")

@bp.callback(
    Output('graphFig', 'figure'),
    Output('graphMeta', 'data'),
    Output('graphSubplotRowCnt', 'data'), # Needed to update the figure height dependent on window size in clientside callback
    Output('notificationsContainer','children'),
    State('timeSelFig', 'relayoutData'),
    Input('updateButton', 'n_clicks'),
    Input('aggVarSelector', 'value'),
    Input('aggValSelector', 'value'),
    Input('colorVarSelector', 'value'),
    Input('seedInput', 'value'),
    Input('layoutIterationsInput', 'value'),
    Input('layoutDistanceInput', 'value'),
    Input(TagSelectorModalAIO.ids.selectedIdsStore("tag-selector"), 'data'),
    )
def updateGraphFig(timeSelFigRelayoutData,_,aggVar,aggVals,colorVar,seed,layoutIterations,layoutDistance,tagIds):
    
    if len(aggVals) > maxAggValToShow:
        ntfc = dmc.Notification(
            title="Too many aggregation values",
            id="too-many-agg-vals",
            action="show",
            color="red",
            message=f"Please restrict the selection of aggregation values to a maximum of {maxAggValToShow}!",
            icon=DashIconify(icon="mdi:alert-circle"),
            autoClose=5000,
        )
        return dash.no_update,dash.no_update,dash.no_update,[ntfc]


    if len(tagIds) < 2:
        ntfc = dmc.Notification(
            title="Too few tags selected",
            id="too-few-tags",
            action="show",
            color="red",
            message="Please select at least two tags for proximity visualization!",
            icon=DashIconify(icon="mdi:alert-circle"),
            autoClose=5000,
        )
        return dash.no_update,dash.no_update,dash.no_update,[ntfc]

    #%%Filter
    # Filter by time selected in timeSelFig
    dfFilter = getTimeFilter(df.time,timeSelFigRelayoutData)
    
    # Filter by aggregation variable values selected in aggValSelector
    if len(aggVals) > 0: 
        if aggVar in aggVarColumnOptions:
            dfFilter = dfFilter & (df[aggVar].isin(strToAggVal(aggVals)))
        elif aggVar in aggVarTimeOptions:
            # Time aggregation types are not columns in the dataframe, so we need to
            # determine which time groups are selected and to what indicies they correspond
            sel = pd.concat([pd.Series(df.groupby(getAggGrouper(aggVar)).groups),pd.Series(True,index=[pd.Timestamp(av,tz=cfg.importArgs["convertToTZ"] if cfg.importArgs["convertToTZ"] else ...) for av in aggVals])],axis=1).fillna(False)
            sel[0] = sel[0] - 1
            dfFilter = dfFilter & (sel.set_index(0).reindex(df.index,method="bfill"))[1]

    dfFilter = dfFilter & (df.tagId.isin(tagIds))
    edgeFilter = dfFilter.reindex_like(edgeDf) & edgeDf.sendId.isin(tagIds)
    
    # Apply filter and only copy if necessary
    filteredDf = df if dfFilter.all() else df[dfFilter].copy()
    filteredEdgeDf = edgeDf if edgeFilter.all() else edgeDf[edgeFilter].copy()

    # If no data is left after filtering, return no update and show notification
    if filteredDf.shape[0] == 0:
        ntfc = dmc.Notification(
            title="No data in selection",
            id="no-selection",
            action="show",
            color="red",
            message="There is no data in the selected time range and aggreagation values!",
            icon=DashIconify(icon="mdi:alert-circle"),
            autoClose=5000,
        )
        return dash.no_update,dash.no_update,dash.no_update,[ntfc]


    #%% Aggregate
    # Variable to aggregate by: will result in one graph column per unique value
    aggGrouper = getAggGrouper(aggVar)

    # Aggregation function paramters for metadata that is displayed for each node
    metaVars = [(colorVar,"mean")]
    metaAggNames = [f"{aggFunc}_{col}" for col, aggFunc in metaVars]
    metaAgg = dict(zip(metaAggNames, metaVars))

    # Make edge undirected by sorting ids
    filteredEdgeDf[["minId","maxId"]] = np.sort(filteredEdgeDf[["recvId","sendId"]],axis=1)

    # Shift rssi to get positive values-> 0 should be not seen so summation and 
    # subsequent division ends up producing a lower value when edge was less frequently observed
    filteredEdgeDf["weight"] = filteredEdgeDf.rssi + 100 

    aggsEdgeDf = filteredEdgeDf.groupby([aggGrouper,"maxId","minId"], as_index=True, observed=True).agg(edgeCount=("weight","size"), weightSum = ("weight","sum") )
    # aggEdgeDf = aggEdgeDf.sort_index(level=0, ascending=True)

    metaDf = filteredDf.groupby([aggGrouper,"tagId"], as_index=True, observed=True)\
                .agg(**metaAgg)

    #%% Visualize

    # Prepare parameters for the layout
    fixedNodePositions = pv.getFixedNodesDict(tagsDf) 
    # seed = random.randint(0,100)

    # Create empty dict to store graphs for each aggVar category (convert timestamp to
    # string if necessary)
    graphs = {aggVal:[]
                for aggVal in 
                aggsEdgeDf.index.get_level_values(level=0).unique()}

    # Create empty dict to store graph metadata for clientside rssi highlighting on selection
    graphMeta = {"edges":{},"traces":[]}

    # Build seperate graphs for each aggVar
    for aggVal, aggEdgeDf in aggsEdgeDf.groupby(level=0, observed=True,sort=True):
        aggEdgeDf = aggEdgeDf.reset_index()

        # Add edges to graphMetadata for clientside rssi highlighting
        graphMeta["edges"][aggValToStr(aggVal)] = {r.maxId + r.minId:r.weightSum for r in aggEdgeDf.itertuples()}


        # Create networkX graph from edges
        G = nx.from_pandas_edgelist(aggEdgeDf, source="maxId", target="minId", edge_attr=["weightSum"], create_using=nx.Graph) # Or: nx.DiGraph

        # Split Graph into components for separate layout and plotting
        Gcomponents = [G.subgraph(c) # Get subgraph from node list of each component
                        for c in 
                            sorted( # Sort by size
                                nx.connected_components(G),
                                key=len,
                                reverse=True
                            )
                        ]

        aggMetaDf = metaDf.reset_index(level=1).loc[aggVal].set_index("tagId") # Multiindex didnt't work with bool values so reset and set tagId index before and after
        
        for component in Gcomponents:
            # Spring layout doesn't like fixed nodes that are not in the graph, so remove them
            fixedNodes = set.intersection(set(component),fixedNodePositions.keys())
            if(len(fixedNodes) == 0): fixedNodes = None

            # Determine node positions
            nodePositions = nx.spring_layout(component,
                    k=layoutDistance, 
                    iterations=layoutIterations, 
                    scale=1.0, 
                    #  center=(0,0), 
                    #  dim=2, 
                    seed=seed, 
                    weight='weightSum', 
                    # weight=None,
                    pos=fixedNodePositions, 
                    fixed=fixedNodes
                    )
            # Build dataframe from nodepostions dict to merge with metadata and draw with plotly
            nodeDf = pd.DataFrame.from_dict(nodePositions,orient="index",columns=["x","y"])
            nodeDf = nodeDf.join(aggMetaDf, how="left")
            nodeDf = nodeDf.join(tagsDf, how="left")


            # Build edge arys for plotly
            (x,y) = pv.getPlotlyEdgeArrays(nodePositions,component.edges)

            graphs[aggVal].append(
                        [go.Scatter(x=x, y=y, # ScatterGL speeds up things quite a bit, but always is rendered on top of the nodes since z-index feature is missing: https://github.com/plotly/plotly.py/issues/1514
                                    line=dict(width=0.1, color='rgba(8, 8, 8, 0.3)'),
                                    hoverinfo='none',
                                    mode='lines')]
                            +
                        list(px.scatter(nodeDf, 
                                    x="x", y="y",
                                    symbol="Type", 
                                    color=metaAggNames[0],
                                    text=np.full(len(nodeDf)," "), #nodeDf.index,
                                    hover_data=["Type","location",nodeDf.index] + metaAggNames)\
                                    .update_traces(mode="markers+text", textposition="middle center")
                                    .data)
            )

    # Assemble and display plots        
    maxComponentCount = max([len(f) for f in graphs.values()])
    fig = make_subplots(rows=maxComponentCount, cols=len(graphs),
                        subplot_titles=aggValToStr(list(graphs.keys())),
                        horizontal_spacing=0,
                        vertical_spacing=0,)
    
    for aggN, (aggVar, figs) in enumerate(graphs.items()):
        for figN, f in enumerate(figs):
            for trace in f:
                graphMeta["traces"].append(aggValToStr(aggVar))
                
                fig.add_trace(trace, row=figN+1, col=aggN+1)

    # Hide Plot axes and show seperatoion lines between subplots
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, showline=True, linewidth=1, linecolor='rgb(206, 212, 218)', mirror=False)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, showline=True, linewidth=1, linecolor='rgb(206, 212, 218)', mirror=False)

    fig.update_traces(selected_marker=dict(size=8),unselected_marker=dict(size=4,opacity=0.6),marker=dict(size=5))

    # Move titles into plots so more vertical space for information
    fig.update_annotations(yshift=-30)

    fig.update_layout({'clickmode': 'event+select'})
    # fig.update_layout() 
    fig.update_layout(go.Layout(
                    # https://community.plotly.com/t/preserving-ui-state-like-zoom-in-dcc-graph-with-uirevision-with-dash/15793
                    # -> If the value of UI revision is the same as in previous return, the UI state will be preserved.
                    uirevision="".join(aggVals),
                    # title='<br>Network graph made with Python',
                    # titlefont_size=16,
                    height=550*maxComponentCount,
                    showlegend=False,
                    # hovermode='closest',
                    # xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    # yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    margin={'l':0, 'b': 0, 't': 0, 'r': 150},
                    modebar=dict(orientation="v"),
                    coloraxis=dict(
                        # Always keep the same colorscale (there was a bug where the
                        # colorscale would change when selecting some specific nodes)
                        autocolorscale= False, 
                        colorscale=px.colors.sequential.Inferno, 

                        colorbar=dict( # Keep Colorbar aligned to first subplot
                            len=1/maxComponentCount,
                            yanchor="top",
                            y=1   
                        ))
                    ))
    return [fig, graphMeta, maxComponentCount, []]

bp.clientside_callback(
    ClientsideFunction(
        namespace='proxClientside',
        function_name='highlightProxCb'
    ),
    Output('graphFig', 'figure'),
    Input('graphFig', 'selectedData'),
    Input('graphMeta', 'data'),
    State('graphFig', 'figure'))

#Update seedInput with random seed between 0 and 100
bp.clientside_callback(
    """
    function(seedInput) {
        return Math.floor(Math.random() * 100);
    }""",
    Output('seedInput', 'value'),
    Input('randomSeedButton', 'n_clicks'))


#Update graph height based on number of subplots
# bp.clientside_callback(
#     """
#     function(graphSubplotRowCnt) {
#         return {'height': 600*graphSubplotRowCnt};
#     }""",
#     Output('graphFig', 'style'),
#     Input('graphSubplotRowCnt', 'data'))


# @bp.callback(
#     Output('json', 'children'),
#     Input('graphFig', 'selectedData'),
#     Input('graphFig', 'figure'),)
# def updateGraphFigSelection(selected,figure):
#     # print(json.dumps(selected,indent=4))
#     # return(json.dumps(figure,indent=4))
#     return dash_renderjson.DashRenderjson(id="input", data=figure, max_depth=3,invert_theme=True)

# Get the grouper for the selected aggregation variable
def getAggGrouper(aggVar):
    if not aggVar: # If no aggregation variable is selected, use a dummy variable so all selected datapoints are aggregated into one graph
        return lambda x: "-"

    if args := aggVarTimeOptions.get(aggVar, False):
        return pd.Grouper(key="time", sort=True, **args)

    return pd.Grouper(aggVar)

# Get the string representation of an aggregation value
def aggValToStr(aggVal):
    if isinstance(aggVal, list):
        return [aggValToStr(v) for v in aggVal]

    if isinstance(aggVal, pd.Timestamp):
        return aggVal.strftime(timeFormat)
    return str(aggVal)

# Get the object representation of an aggregation value
def strToAggVal(aggVal):
    if isinstance(aggVal, list):
        return [strToAggVal(v) for v in aggVal]

    if isinstance(aggVal, str):
        try:
            return pd.Timestamp(aggVal)
        except:
            pass

        if aggVal in ["True","False"]:
            return aggVal == "True"

    return aggVal

def getTimeFilterBounds(selFigRelayoutData):
    try:
        # Format of relayoutData is slightly differrent depending on whether the main time figure
        # was zoomed or the "overview bar" was used
        tStart = selFigRelayoutData.get("xaxis.range[0]") or selFigRelayoutData.get("xaxis.range")[0] # -> throws exception if no time selection is made
        tEnd   = selFigRelayoutData.get("xaxis.range[1]") or selFigRelayoutData.get("xaxis.range")[1]
        return (tStart, tEnd)
    except Exception as e:
        return(None, None)

def getTimeFilter(time, selFigRelayoutData):
    tStart, tEnd = getTimeFilterBounds(selFigRelayoutData)
    
    if(tStart == None or tEnd == None):
        # If no time selection is made, use all data
        return pd.Series(True,index=time.index)

    dfFilter = (time >= tStart) & (time <= tEnd)
    # print("Filtered from {} to {}".format(tStart,tEnd))
    # filteredDf = df[df.time >= pd.Timestamp("27.01.2023 05:30",tz="UTC")]
    # filteredDf = df[df.time == pd.Timestamp("27.01.2023 09:30",tz="UTC")]
    return dfFilter

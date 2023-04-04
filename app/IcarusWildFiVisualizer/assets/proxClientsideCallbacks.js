window.dash_clientside = Object.assign({}, window.dash_clientside, {
    proxClientside: {
        highlightProxCb: function(selected, graphMeta, figure) {
            // Ignore if figure is not yet loaded or graphMeta and figure are not in sync
            if(!figure || !figure.data|| !graphMeta || graphMeta.traces.length != figure.data.length) return window.dash_clientside.no_update;

            // Deselect all points if most recent selection action deselected all points
            // in a subplot
            if(selected == null) return Object.assign({},resetGraphHighlighting(figure));

            // Remove prior selection areas
            if(figure.layout.selections) figure = removeSelections(selected, figure)
            // console.log(selected);
            
            selIds = new Set(selected.points.map(({customdata}) => customdata[2]))

            //Show weightSum for every connected point if only one point is selected
            if(selIds.size == 1){
                if(graphMeta == null) return window.dash_clientside.no_update;
                
                mainId = selIds.values().next().value;

                for(let j = 0; j < figure.data.length; j++){
                    if(figure.data[j].customdata == null) continue;

                    // Get to which graph column/aggregation value the trace belongs to
                    aggVal = graphMeta.traces[j];

                    // Get corresponding edges for this graph column/aggregation value
                    edges = graphMeta.edges[aggVal];

                    selIdx = [];
                    text = [];
                    color = [];
                    for (let i = 0; i < figure.data[j].customdata.length; i++) {
                        nodeId = figure.data[j].customdata[i][2]
                        if(nodeId == mainId){
                            t = "X"
                            c = null;
                        } else {
                            edgeKey = [nodeId, mainId].sort().reverse().join("")
                            w = edges[edgeKey]
                            t =  w || " ";
                            c =  w || 0;
                        }
                        color.push(c);
                        text.push(t);
                        if(t != " ") selIdx.push(i);

                    }
                    figure.data[j].selectedpoints = selIdx;

                    if(!figure.data[j].origText ){
                        figure.data[j].origText = figure.data[j].text
                    }
                    figure.data[j].text = text;

                    if(!figure.data[j].marker.origColor ){
                        figure.data[j].marker.origColor = figure.data[j].marker.color
                    }
                    figure.data[j].marker.color = color
                }
            }else 
            if(selIds.size > 1){
                figure = resetGraphHighlighting(figure); // In case we had a single selection before text and color need to be reset

                for(let j = 0; j < figure.data.length; j++){
                    if(figure.data[j].customdata == null) continue;
                    selIdx = [];
                    for (let i = 0; i < figure.data[j].customdata.length; i++) { 
                        if(selIds.has(figure.data[j].customdata[i][2])) {
                            selIdx.push(i);
                        }
                    }
                    figure.data[j].selectedpoints = selIdx;
                }
                // if(figure.layout.datarevision == null) figure.layout.datarevision = 0;
                // figure.layout.datarevision++;
            }
            return Object.assign({},figure); // We need to copy figure for plotly to redraw as datarevision doesn't seem to work
            }
        }
});


function resetGraphHighlighting(figure){
    for(trace of figure.data){
        trace.selectedpoints = null;
        if(trace.marker.origColor){
            trace.marker.color = trace.marker.origColor;
            trace.marker.origColor = null;
        } 
        if(trace.origText){
            trace.text = trace.origText;
            trace.origText = null;
        } 
    }
    return figure; // We need to copy figure for plotly to redraw as datarevision doesn't seem to work
}

function removeSelections(selected, figure){

    newSelections = [];

    // selected.range is only filled if user selects via lasso or box selection if user
    // clicks on a point it is null and all other selections polygons are removed
    if(selected.range){
        // -> Only keep this last selection
        axis = Object.keys(selected.range)
        for(sel of figure.layout.selections){
            if(axis[0] == (sel.xref) && axis[1] == (sel.yref)){
                newSelections.push(sel)
            }
        }
    }

    figure.layout.selections = newSelections;
    return figure;
}
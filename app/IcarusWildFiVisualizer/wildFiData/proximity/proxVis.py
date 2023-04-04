def getFixedNodesDict(tagDf):
    """Returns dict of fixed nodes with tagId as key and (locationX,locationY) as values
        from tagDf. TagId should be index of tagDf.  Ready for use with networkX spring_layout"""
    fixTagDf = tagDf[tagDf.locationX.notna() & tagDf.index.notna()]
    return {r.Index:(r.locationX,r.locationY) for r in fixTagDf.itertuples(index=True)}


def getPlotlyEdgeArrays(nodePosDict, edgeTuples):
    """Returns Tuple of x and y lists for plotting edges with plotly lines plot. Edges are
        separated by None to create discrete segments in the lines plot"""
    x,y = [], []

    extX = x.extend # extend unpacks tuples/lists it is given and appends each element individually
    extY = y.extend
    for edge in edgeTuples:
        startPos = nodePosDict[edge[0]]
        endPos = nodePosDict[edge[1]]
        extX((startPos[0],endPos[0], None))
        extY((startPos[1],endPos[1], None))
    return (x,y)
import pandas as pd

def extractProxGraphDf(mainDf, returnMalformedRows=False, additionalCols=[]):
    """Extracts prox edge data from df

    Args:
        df (pandas.DataFrame): DataFrame with columns time, tagId, proxIdBurst and proxRssiBurst
        returnMalformedRows (bool, optional): Also return series of booleans with input
                                                df's index. Defaults to False.
        additionalCols (list, optional): List of additional columns of input df to include in output edgeDf.

    Returns:
        pandas.DataFrame / Tuple: DataFrame with columns time, recvId, sendId, rssi and one row for each edge
                                    and if returnWellformedRows is true additionally pandas.Series
                                    with input df's index and boolean values where false
                                    indicates a row with non matching proxIdBurst and
                                    proxRssiBurst lengths
    """    
    
    proxIds = mainDf.proxIdBurst.str.split()
    proxRssis = mainDf.proxRssiBurst.str.split()
    
    proxLen = proxIds.str.len()
    proxWellformed = (proxLen == proxRssis.str.len())
    proxValid = (proxLen > 0) & proxWellformed

    edgeData = {"time":mainDf.time,"recvId":mainDf.tagId,"rssi":proxRssis,"sendId":proxIds}
    edgeData.update({col:mainDf[col] for col in additionalCols})

    edgeDf = pd.DataFrame(edgeData)
    # edgeDf = pd.DataFrame({"time":mainDf.time,"recvId":mainDf.tagId,"rssi":proxRssis,"sendId":proxIds}+{col:mainDf[col] for col in additionalCols})
    edgeDf.drop(edgeDf[~proxValid].index, inplace=True)
    edgeDf = edgeDf.explode(["sendId","rssi"])
    edgeDf.rssi = edgeDf.rssi.astype("int16")

    if returnMalformedRows:
        return edgeDf, ~proxWellformed
    else:
        return edgeDf

def mergeLocation(proxDf, tagLocations, mainDfIndex = None):
    """Merges location data of Gateways from tagDf on proxDf (on sendId)

    Args:
        proxDf (pandas.DataFrame): Prox dataframe with column sendId as well as
                                    same index as mainDf (multiple rows with same index if
                                    originating from same row in main df)
        tagLocations (pandas.Series): Series with index tagId and location as data
        mainDfIndex (Index): Index of main dataframe (The first of two returned series will be
                                reidexed to this parameter is passed). Default is None 

    Returns:
        pandas.Series / Tuple: If mainDfIndex == None Series of locations for each proxDf
        row is returned otherwise tuple of two series containing list of locations for
        each main row and location for each prox row is returned
    """
    # Merge locations from tagsDf into proxDf
    #  (map is faster than merge/join)
    proxLocation = proxDf.sendId.map(tagLocations).rename("location")

    # Just map to proxDf?
    if(mainDfIndex == None):
        return proxLocation

    # Aggregate list of locations for each row in main dataframe (level=0 is main df's index
    # from edgeDf)
    mainLocations = proxLocation.dropna()\
                        .groupby(level=0)\
                        .agg((lambda ls: list(set(ls))))\
                        .reindex(mainDfIndex)\
                        .fillna("") 
                        # .str.join(" ")

    return (mainLocations,proxLocation)

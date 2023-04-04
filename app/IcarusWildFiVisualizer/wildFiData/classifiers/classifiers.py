import pandas as pd

from ..proximity import proxUtils as pu

def classifyLocation(  mainDf,
                            proxDf, 
                            locations):
    """Classifies location for each datapoint in mainDf 
        -> Based on what gateway signals are received and if GPS signal is present

    Args:
        mainDf (pandas.DataFrame): Main dataframe with boolean column "gps" indicating
                                    when GPS location could be determined
        proxDf (pandas.DataFrame): Prox dataframe with column "sendId" as well as
                                    same index as mainDf (multiple rows with same index if
                                    originating from same row in main df)
        locations (pandas.Series): Gateway location Series with index tagId and column
                                    location. 
                                    > Use index "gps" to specify location if gps fix is present. 
                                    > Use index "none" to specify location if no location is known
                                    
                                    > Sort by what locations should take precedence if multiple gateways
                                        are observed at the same time.

    Returns:
        Tuple of pandas.Series: Tuple of Series with index of mainDf/proxDf containing
        location for (mainDf, proxDf) rows
    """

    # fakeEdgeDf = pd.DataFrame(data={"sendId":["F6A8","E18C","F6A8","E18C","F6A8","E18C"]},index=[1,1,2,2,3,4])
    # fakeMainDf = pd.DataFrame(data={"gps":[True,False,True,True]},index=[1,2,3,4])

    # locations = pd.Series({"F6A8":"InCave","gps":"Outside","E18C":"OutsideGW"})

    if(locations.dtype.name == "category" and locations.dtype.ordered == False):
        locType = locations.dtype
    else:
        locType = pd.CategoricalDtype(locations.unique(),ordered=True)
        locations = locations.astype(locType)

    
    proxLocations = pu.mergeLocation(proxDf , locations)

    # Fill prox rows where no location is known with none location if specified
    if "none" in locations.index:
        proxLocations = proxLocations.fillna(locations["none"])

    # Add "fake" gps location rows for each index that had gps
    proxLocations = pd.concat(
        [
            proxLocations,
            locations[["gps"]].reset_index(drop=True)
                .reindex(mainDf[mainDf.GPS].index, method="nearest")
        ]
    )

    # Sort by category order so that first location in order is taken for whole row of mainDf data
    proxLocations = proxLocations.sort_values()

    # Groupby mainDf row index and take first location for all proxDf rows belonging to this
    mainLocations =  proxLocations.groupby(level=0).apply("first")

    # Broadcast back to proxDf
    proxLocations = pd.Series(
        index=proxDf.index,
        data=proxDf.index.map(mainLocations)
        )

    return (mainLocations,proxLocations)
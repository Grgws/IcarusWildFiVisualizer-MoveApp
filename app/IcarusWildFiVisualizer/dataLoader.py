"""This module imports and caches data at a centralized location so not every page in the
app loads the data separately."""

import time
from datetime import datetime

import pandas as pd
import cache_df as cdf

from . import wildFiData as wfd

from . import config as cfg

_badDf = None
_mainDf = None
_proxDf = None

_tagsDf = None

def getData(wildFiDataDir = cfg.wildFiDataDir, cacheDir =  cfg.cacheDir, tagMetaFile = cfg.tagMetaFile, importArgs = cfg.importArgs):
    """Load data from csv or cache files and return a tuple of pandas.DataFrames with bad rows df,
    main df, prox df and tags metadata dataframe.

    Args:
        wildFiDataDir (str, optional): Directory containing decoded WildFi data csv files. Defaults to cfg.wildFiDataDir.
        cacheDir (str, optional): Path at which cache files should be stored. Defaults to cfg.cacheDir.
        tagMetaFile (str, optional): Path of csv containing metadata for each tagId. Defaults to cfg.tagMetaFile.
        importArgs (dict, optional): Dict of kwargs for importWildFiData function. Defaults to cfg.importArgs.

    Returns:
        Tuple of pandas.DataFrames: A tuple of pandas.DataFrames:
            - badDf  (bad rows)
            - mainDf (main data)
            - proxDf (proximity graph edge data)
            - tagsDf (metadata)
    """
    global _badDf
    global _mainDf
    global _proxDf

    global _tagsDf
    # POIS? ...
    
    global cache

    cache = cdf.CacheDF(cacheDir)

    # Is data already loaded?
    if _badDf is None or _mainDf is None or _proxDf is None:
        # Load data from cache or csv files...
        if not cache.is_cached("badDf") or not cache.is_cached("mainDf") or not cache.is_cached("proxDf") or not cache.is_cached("tagsDf"):
            (_badDf,_mainDf, _proxDf, _tagsDf) = loadData(wildFiDataDir,tagMetaFile,importArgs)
            cache.cache(_badDf ,"badDf")
            cache.cache(_mainDf,"mainDf")
            cache.cache(_proxDf,"proxDf")
            cache.cache(_tagsDf,"tagsDf")
        else:
            start = time.time()
            _badDf = cache.read("badDf")
            _mainDf = cache.read("mainDf")
            _proxDf = cache.read("proxDf")        
            _tagsDf = cache.read("tagsDf")
            print(f"{datetime.now().strftime('%H:%M:%S')} Loaded from cache in {time.time()-start:.2f}s")

    return (_badDf,_mainDf, _proxDf, _tagsDf)

def clearCache():
    """Clears cache files"""
    global cache
    cache.clear()
    
def loadData(wildFiDataDir,tagMetaFile,importArgs):
    """Loads data from csv files and returns a tuple of pandas.DataFrames

    Returns:
        Tuple: Tuple of pandas.DataFrame with bad rows, main dataframe and prox dataframe
    """
    # Load tag metadata
    tagsDf = pd.read_csv(tagMetaFile,sep=";").drop_duplicates("tagId").set_index("tagId")

    # Load main tag data csv files
    rawDf = wfd.readRawWildFiData(wildFiDataDir)

    # Check for bad data
    badDf = wfd.checkWildFiData(rawDf,  knownTagIds=tagsDf.index.values,onlyReturnBadData=True).join(rawDf,how="left")

    # Remove bad data for further processing
    rawDf = rawDf[~badDf.anyProblems.reindex(rawDf.index,fill_value=False)].copy()

    # Import data (add additional metrics, convert datetime types, etc.)
    mainDf = wfd.importWildFiData(rawDf,**importArgs)

    # Extract proximity data edges
    proxDf = wfd.extractProxGraphDf(mainDf)


    #Add row counts to tagsDf
    rowCnts = mainDf.groupby(["GPS","tagId"]).size()
    tagsDf.insert(0,column="onlyProxRows",value=tagsDf.index.map(rowCnts[False]))
    tagsDf.insert(0,column="proxAndGPSRows",value=rowCnts[True])
    tagsDf.insert(0,column="totalRows",value=tagsDf.onlyProxRows + tagsDf.proxAndGPSRows)
    tagsDf[["onlyProxRows","proxAndGPSRows","totalRows"]] = tagsDf[["onlyProxRows","proxAndGPSRows","totalRows"]].fillna(0).astype("int")


    # Classify location
    locationCategories = tagsDf.locationCategory.copy().dropna()
    locationCategories["gps"] = "Outside"
    locationCategories["none"] = "Unknown"
    locationCategories = locationCategories.astype("category")
    locationCategories = locationCategories.cat.reorder_categories(["Outside","InCave","Unknown"])

    (mainDf["locationCategory"],proxDf["locationCategory"]) = wfd.classifiers.classifyLocation(mainDf,proxDf,locationCategories)

    # Join GPS indicator to proxDf (for proximity visualization)
    proxDf["GPS"] = proxDf.index.map(mainDf.GPS)

    return (badDf, mainDf, proxDf, tagsDf)

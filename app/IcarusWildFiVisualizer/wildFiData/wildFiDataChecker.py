#%%
import sys
sys.path.append("../CyprusPrep/WildFiAnalyzer/")
from .proximity import proxUtils as pu
from . import dbaCalculator as dba
import pandas as pd

import numpy as np

# TODO: Check for abnormally high acc values
    
def checkWildFiData(df, knownTagIds = [], onlyReturnBadData = False):
    """Returns pandas.DataFrame indicating various malformed data conditions for each row of the input dataframe.

    Args:
        df (pandas.DataFrame): WildFi data dataframe to check (acc and prox data need to
                                be unparsed strings)
        tagList (list, optional): List of known tagIds for checking proximity data ignored if empty list. Defaults to [].
        onlyReturnBadData (bool, optional): If True, only return rows with bad data. Defaults to False.
          
    Returns:
        pandas.DataFrame: Dataframe containing all metrics for bad data

    Notes:
        The following columns are appended to the input dataframe:
            - duplicate: True if the row is a duplicate of another row
            - duplicateExceptFirst: True if the row is a duplicate of another row, except
              the first occurence

            - missingProxCols: Array of column names with missing data in the row
              (considering if  row contains gps or prox data)
            - missingGPSCols: Array of column names with missing data in the row (see above)

            - accMalformed: True if the row contains malformed acc data (count of values
              not evenly divisible by 3)

            - proxMalformed: True if the row contains malformed prox data (count of
              proxIdBurst values and proxRssiBurst values not equal)

            - badProxIds: Array of proxIds from proxIdBurst that are not in knownTagIds
            - badProxCount: Count of unknown proxIds in proxIdBurst

            - duplicateProxIds: Array of unique proxIds from proxIdBurst that are duplicates
            - duplicateProxCount: Total (non-unique) count of duplicate proxIds in proxIdBurst

    """
    
    #%% Create empty dataframe to store check results -----------------------------
    checkDf = pd.DataFrame(index=df.index)
    checkDf["anyProblems"] = False

    #%% Duplicate data rows -------------------------------------------------------
    checkDf["duplicate"] = df.duplicated(["utcTimestamp","tagId"],keep=False)
    checkDf["duplicateExceptFirst"] = df.duplicated(["utcTimestamp","tagId"],keep="first")
    
    checkDf.anyProblems = checkDf.anyProblems | checkDf.duplicate | checkDf.duplicateExceptFirst

    # print(f"Duplicate Rows: Total: {df.duplicate.sum()}, Unique: {df.duplicate.sum() - df.duplicateExceptFirst.sum()}")


    #%% Determine missing values in each row --------------------------------------
    proxCols = ["tagId","utcTimestamp","utcDate","temperatureInDegCel","humidityInPercent","pressureInHPA","accInGBurst"] # Leave out "proxIdBurst" and "proxRssiBurst" because they are also valid when empty
    gpsCols = ["tagId","utcTimestamp","utcDate","lat","lon","hdop","ttfSeconds"]

    notnaDf = df.notna()

    # Classify data row type by comparing number of missing values for prox and gps columns
    proxNotNaCount = notnaDf.loc[:,proxCols].sum(axis=1)
    gpsNotNaCount  = notnaDf.loc[:,gpsCols].sum(axis=1)
    isProxRow = proxNotNaCount > gpsNotNaCount

    # Determine wich columns are missing in each row
    checkDf["missingProxCols"] = notnaDf.loc[isProxRow,proxCols].apply(lambda row: [col for (col, field) in zip(proxCols,row) if not field],axis=1)
    checkDf["missingGPSCols"] =  notnaDf.loc[~isProxRow,gpsCols].apply(lambda row: [col for (col, field) in zip( gpsCols,row) if not field],axis=1)

    checkDf.anyProblems = checkDf.anyProblems | (checkDf.missingProxCols.str.len()>0) | (checkDf.missingGPSCols.str.len()>0)

    # print(f"{(df.missingProxCols.str.len()>0).sum()}/{isProxRow.sum()} prox rows with na values")
    # print(f"{(df.missingGPSCols.str.len()>0).sum()}/{(~isProxRow).sum()} gps rows with na values")



    #%% Determine rows with malformed acc data ------------------------------------
    checkDf["accMalformed"] = ((df[df.accInGBurst.notna()]                    # Only check rows with acc data \
                            .accInGBurst.str.split().str.len()%3 != 0)   # If count of values is not evenly divisible by acc is malformed\
                                .reindex(df.index,fill_value=False))     # Fill all rows without acc with False

    checkDf.anyProblems = checkDf.anyProblems | checkDf.accMalformed


    #%% Extract Prox df and determine malformed rows -------------------------------
    # Replace nan with empty string to avoid errors when parsing
    df["proxIdBurst"] = df["proxIdBurst"].astype(str).replace("nan","")
    df["proxRssiBurst"] = df["proxRssiBurst"].astype(str).replace("nan","")
    (proxDf,checkDf["proxMalformed"]) = pu.extractProxGraphDf(df.rename(columns={"utcTimestamp":"time"}), returnMalformedRows=True, additionalCols=["filename","csvIndex"])

    checkDf.anyProblems = checkDf.anyProblems | checkDf.proxMalformed

    #%% Determine unknown tagIds in prox senders -----------------------------------
    if len(knownTagIds):
        # Determine prox graph edges with unknown senders
        badProxDf = proxDf[~proxDf.sendId.isin(knownTagIds)].copy()

        # Determine count of each bad id
        badIdCountsSeries = badProxDf.sendId.value_counts()

        # Aggregate bad graph edges by time and receiver
        badProxDf = badProxDf.reset_index()\
                                .groupby(["index"], as_index=False)\
                                .agg(badProxIds=("sendId",list),badProxCount=("sendId","count"))\
                                .set_index("index")


        # Add bad prox columns
        checkDf[badProxDf.columns] = badProxDf

        checkDf.anyProblems = checkDf.anyProblems | (checkDf.badProxCount > 0)






    # %% What rows contain the same proxId multiple times? -------------------------

    duplicateProxDf = proxDf[proxDf.duplicated(["filename","csvIndex","sendId"],keep=False)].sort_values(["time","recvId","sendId"])

    duplicateProxDf = duplicateProxDf.reset_index() \
                        .groupby(["index"],as_index=False)\
                        .agg(duplicateProxIds=("sendId",lambda s:s.unique()),duplicateProxCount=("sendId","count"))\
                        .set_index("index")

    # Add duplicate Prox columns
    checkDf[duplicateProxDf.columns] = duplicateProxDf

    checkDf.anyProblems = checkDf.anyProblems | (checkDf.duplicateProxCount > 0)

    #TODO: Recognize when recvId and sendId is the same!

    if onlyReturnBadData:
        checkDf = checkDf[checkDf.anyProblems].copy()

    #%% Return checkDf
    return checkDf


def toFormattedExcel(excel_writer, df, boolCols, nbrCols, strCols):
    
    # Create a Pandas Excel writer using the provided file path
    with pd.ExcelWriter(excel_writer, engine='xlsxwriter') as writer:
      
      # Convert the dataframe to an XlsxWriter Excel object.
      df.to_excel(writer, sheet_name='BadData', index=False)
      
      # Get the workbook and active worksheet
      workbook = writer.book
      worksheet = writer.sheets["BadData"]
      
      # Add a format.
      redBg = workbook.add_format({'bg_color': 'red'})
      
      # Get the dimensions of the dataframe.
      (max_row, max_col) = df.shape

      # Apply conditional formatting to boolean columns
      for col in boolCols:
          col_idx = df.columns.get_loc(col)
          worksheet.conditional_format(1, col_idx, max_row, col_idx,
                              {'type':     'text',
                                'criteria': 'containing',
                                'value':    'TRUE',
                                'format':   redBg})
      
      # Apply conditional formatting to numeric columns
      for col in nbrCols:
          col_idx = df.columns.get_loc(col)
          worksheet.conditional_format(1, col_idx, max_row, col_idx,
                               {'type':     'cell',
                                'criteria': 'greater than',
                                'value':    0,
                                'format':   redBg})
      
      # Apply conditional formatting to string columns
      for col in strCols:
          col_idx = df.columns.get_loc(col)
          worksheet.conditional_format(1, col_idx, max_row, col_idx,
                               {'type':     'no_blanks',
                                'format':   redBg})

      # Freeze the first row
      worksheet.freeze_panes(1, 0)
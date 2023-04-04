from sdk.moveapps_io import MoveAppsIo as mIO
import os 

# wildFiDataDir = "/home/gwilbs/vscode/WildFiTest/Cyprus/Data/23_DecoderDebugged"
# tagMetaFile = "/home/gwilbs/vscode/WildFiTest/Cyprus/Data/MetaData/tagAndBat.csv"
wildFiDataDir = mIO.get_app_file_path("wildFiDataDir")
tagMetaFile = os.path.join(mIO.get_app_file_path("tagMetaDir"),"metadata.csv")
cacheDir = "./cache"

importArgs = dict(
    mergeGPSPoints=True, 
    parseAcc=True,
    convertToTZ = "EET"
)

# TODO: CREATE SETTING FOR THIS!!!
mapBoxAccessToken = "pk.eyJ1IjoiZ3dpbGJzIiwiYSI6ImNsZGl5dm5ncjAwNjAzb3BkdWMzeTRlc3kifQ.Wy56HkFKWq_3h273LN1log"

runOnGunicorn = False
# Copy and rename this file to config.py and fill in the values

wildFiDataDir = "/data"
tagMetaFile = "/meta.csv"
cacheDir = "/cache"

importArgs = dict(
    mergeGPSPoints=True, 
    parseAcc=True,
    convertToTZ = "EET"
)

mapBoxAccessToken = None

runOnGunicorn = True
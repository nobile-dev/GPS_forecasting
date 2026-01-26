import pandas as pd
from .db import get_engine
from .config import DB_COMMUNITY_ID, RAW_DIR

QUERY_GEN = """
SELECT
    MG.CommunityId,
    MG.DateTimeUtc,
    MG.Generation,
    MG.GenerationCommunity,
    MG.MeteringPointId,
    MP.EnergySource,
    MP.Number,
    A.PostalCode,
    A.City
FROM [NobileConnected].[dbo].[MeterGeneration] MG
JOIN [NobileConnected].[dbo].[MeteringPoint] MP 
    ON MG.MeteringPointId = MP.ID
LEFT JOIN [NobileConnected].[dbo].[Adress] A 
    ON MP.AdressId = A.ID
WHERE MG.CommunityId = {community_id}
ORDER BY MG.DateTimeUtc;
"""

QUERY_CON = """
SELECT
    MC.CommunityId,
    MC.DateTimeUtc,
    MC.Consumption,
    MC.ConsumptionCommunity,
    MC.MeteringPointId,
    MP.EnergySource,
    MP.Number,
    A.PostalCode,
    A.City
FROM [NobileConnected].[dbo].[MeterConsumption] MC
JOIN [NobileConnected].[dbo].[MeteringPoint] MP 
    ON MC.MeteringPointId = MP.ID
LEFT JOIN [NobileConnected].[dbo].[Adress] A 
    ON MP.AdressId = A.ID
WHERE MC.CommunityId = {community_id}
ORDER BY MC.DateTimeUtc;
"""

def extract_raw():
    engine = get_engine()

    df_gen_raw = pd.read_sql(QUERY_GEN.format(community_id=DB_COMMUNITY_ID), engine)
    df_con_raw = pd.read_sql(QUERY_CON.format(community_id=DB_COMMUNITY_ID), engine)

    # Speichern (damit du nicht immer SQL ziehen musst)
    gen_path = RAW_DIR / "df_gen_raw.parquet"
    con_path = RAW_DIR / "df_con_raw.parquet"
    df_gen_raw.to_parquet(gen_path, index=False)
    df_con_raw.to_parquet(con_path, index=False)

    print(f" Gespeichert: {gen_path}")
    print(f" Gespeichert: {con_path}")

    return df_gen_raw, df_con_raw

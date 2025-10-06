import json, pandas as pd
from pathlib import Path
from common.config import DATA_EVENTS_PATH, FEATURES_TRAIN_PATH, FEATURES_VAL_PATH
from datetime import datetime

# 1) Carrega eventos NDJSON
rows = []
with open(DATA_EVENTS_PATH) as f:
    for line in f:
        rows.append(json.loads(line))
df = pd.DataFrame(rows)
df["event_time"] = pd.to_datetime(df["event_time"])

# 2) Split temporal simples (últimos 2 dias = validação)
cut = df["event_time"].max() - pd.Timedelta(days=2)
train = df[df["event_time"] <= cut].copy()
val   = df[df["event_time"]  > cut].copy()

# 3) Labels (save_recipe = 1; view = 0)
def to_label(x): return 1 if x == "save_recipe" else 0
train["label"] = train["event_name"].apply(to_label)
val["label"]   = val["event_name"].apply(to_label)

# 4) Agregações mínimas User×Recipe (KISS)
def build_feats(dd):
    grp = dd.groupby(["user_id","recipe_id"])
    out = grp.agg(
        views=("event_name", lambda s: (s=="recipe_view").sum()),
        saves=("event_name", lambda s: (s=="save_recipe").sum()),
        last_ts=("event_time","max")
    ).reset_index()
    out["conv"] = out["saves"] / out["views"].clip(lower=1)
    return out

ftrain = build_feats(train)
fval   = build_feats(val)

# 5) Juntar label recente (se houve save)
lbl = train.groupby(["user_id","recipe_id"])["label"].max().reset_index()
ftrain = ftrain.merge(lbl, on=["user_id","recipe_id"], how="left").fillna({"label":0})

lblv = val.groupby(["user_id","recipe_id"])["label"].max().reset_index()
fval = fval.merge(lblv, on=["user_id","recipe_id"], how="left").fillna({"label":0})

# 6) Salva Parquet
Path(FEATURES_TRAIN_PATH).parent.mkdir(parents=True, exist_ok=True)
ftrain.to_parquet(FEATURES_TRAIN_PATH, index=False)
fval.to_parquet(FEATURES_VAL_PATH, index=False)
print("ok: features ->", FEATURES_TRAIN_PATH, FEATURES_VAL_PATH)


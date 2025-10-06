import pandas as pd, numpy as np, lightgbm as lgb
from common.config import FEATURES_TRAIN_PATH, FEATURES_VAL_PATH, MODEL_PATH
from sklearn.metrics import ndcg_score
from pathlib import Path

# Carrega
tr = pd.read_parquet(FEATURES_TRAIN_PATH)
va = pd.read_parquet(FEATURES_VAL_PATH)

# ==== Baseline NDCG@10 (popularidade por recipe) ====
pop = tr.groupby("recipe_id")["saves"].sum().sort_values(ascending=False)
# Avaliação baseline: para cada user em val, rankear por pop
def eval_baseline(val):
    users = val["user_id"].unique()
    y_true, y_score = [], []
    for u in users:
        du = val[val.user_id==u]
        # y_true: 1 se du.label>0, caso contrário 0
        y = du["label"].astype(int).to_numpy()
        # score = popularidade do recipe (fallback 0)
        s = du["recipe_id"].map(pop).fillna(0).to_numpy()
        if len(y) >= 2:
            y_true.append(y[np.newaxis, :])
            y_score.append(s[np.newaxis, :])
    if not y_true: return 0.0
    return float(np.mean([ndcg_score(y_t, y_s, k=10) for y_t, y_s in zip(y_true, y_score)]))

ndcg_base = eval_baseline(va)

# ==== LightGBM LambdaMART ====
# grupo por user para ranking
def groups(df): return df.groupby("user_id").size().tolist()

# features simples
drop_cols = ["user_id","recipe_id","last_ts","label"]
Xtr = tr.drop(columns=drop_cols)
ytr = tr["label"]

Xva = va.drop(columns=drop_cols)
yva = va["label"]

params = dict(objective="lambdarank", metric="ndcg", ndcg_eval_at=[10],
              learning_rate=0.05, num_leaves=63, min_data_in_leaf=50)

train_set = lgb.Dataset(Xtr, label=ytr, group=groups(tr))
val_set   = lgb.Dataset(Xva, label=yva, group=groups(va), reference=train_set)

model = lgb.train(params, train_set, valid_sets=[val_set],
                  num_boost_round=1000,
                  callbacks=[lgb.early_stopping(50)])

# avaliação NDCG@10 modelo
def eval_model(df, scores):
    users = df["user_id"].unique()
    ndcgs = []
    start = 0
    for g in groups(df):
        end = start + g
        seg = df.iloc[start:end]
        y_true = seg["label"].to_numpy()[np.newaxis, :]
        y_score = scores[start:end][np.newaxis, :]
        if seg.shape[0] >= 2:
            ndcgs.append(ndcg_score(y_true, y_score, k=10))
        start = end
    return float(np.mean(ndcgs)) if ndcgs else 0.0

scores_val = model.predict(Xva)
ndcg_model = eval_model(va, scores_val)

print(f"NDCG@10 baseline={ndcg_base:.3f} | model={ndcg_model:.3f}")

Path(MODEL_PATH).parent.mkdir(parents=True, exist_ok=True)
model.save_model(MODEL_PATH)
print("ok:", MODEL_PATH)


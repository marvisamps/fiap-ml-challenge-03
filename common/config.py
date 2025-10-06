from dotenv import load_dotenv
import os

load_dotenv()
APP_PORT = int(os.getenv("APP_PORT", "8080"))
TOP_K = int(os.getenv("TOP_K", "10"))
CANDIDATES_TOPN = int(os.getenv("CANDIDATES_TOPN", "200"))
DATA_EVENTS_PATH = os.getenv("DATA_EVENTS_PATH", "data/events.jsonl")
FEATURES_TRAIN_PATH = os.getenv("FEATURES_TRAIN_PATH", "data/feat_train.parquet")
FEATURES_VAL_PATH = os.getenv("FEATURES_VAL_PATH", "data/feat_val.parquet")
MODEL_PATH = os.getenv("MODEL_PATH", "artifacts/model.txt")


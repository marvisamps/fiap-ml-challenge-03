import json, uuid, random
from datetime import datetime, timedelta

random.seed(7)
users = [str(uuid.uuid4()) for _ in range(200)]
recipes = [f"rec_{i}" for i in range(500)]
diet_opts = ["low_carb","low_fodmap","veg","none"]
platforms = ["android","ios"]

def gen_event(u, r, ts):
    ev = random.choices(["recipe_view","save_recipe"], [0.9,0.1])[0]
    return {
      "event_time": ts.isoformat()+"Z",
      "user_id": u,
      "event_name": ev,
      "recipe_id": r,
      "diet_selected": random.choice(diet_opts),
      "platform": random.choice(platforms),
      "app_version": f"2.1.{random.randint(0,5)}",
      "source": random.choice(["organic","push","ads"])
    }

now = datetime.utcnow()
with open("data/events.jsonl","w") as f:
    for _ in range(20000):
        ts = now - timedelta(minutes=random.randint(0, 60*24*14))
        e = gen_event(random.choice(users), random.choice(recipes), ts)
        f.write(json.dumps(e)+"\n")
print("ok: data/events.jsonl")


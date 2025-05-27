import atexit
import json
import os
import signal
from sys import exit
from typing import Any, Final

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


# .envファイルを読み込み
load_dotenv()

ENV_KEY: Final[str] = os.environ["KEY"]
SAVE_DATA_PATH: Final[str] = os.environ.get("SAVE_PATH", "savedata.json")


class DataType(BaseModel):
    headStatus: bool
    stock: dict[str, int]


class UpdateStock(BaseModel):
    target: dict[str, int]


data: dict[str, Any] = {
    "headStatus": True,
    "stock": {"avrasm": 75, "smartremote_guide": 35, "unicode_animal_book": 14},
}


@app.get("/", response_class=HTMLResponse)
async def root():
    return "<DOCTYPE html><html><body><h1>Hello world!</h1><p>This is nikatech realtimeserver ver2025.05.27</p><p>created by nikachu</p></body></html>"


@app.get("/status")
async def status():
    return data


@app.post("/admin/update")
async def update(json_body: DataType, authorization: str = Header()):
    # 認証されているかチェック
    if authorization != "Bearer " + ENV_KEY:
        raise HTTPException(status_code=401, detail="authorization failed")

    global data
    data = json_body.model_dump()

    return {"status": True}


@app.patch("/admin/headStatus")
async def headStatus(authorization: str = Header()):
    # 認証されているかチェック
    if authorization != "Bearer " + ENV_KEY:
        raise HTTPException(status_code=401, detail="authorization failed")

    global data
    # headStatusを反転
    data["headStatus"] = not data["headStatus"]

    return {"status": True, "headStatus": data["headStatus"]}


@app.patch("/admin/decrement")
async def decrement(json_body: UpdateStock, authorization: str = Header()):
    # 認証されているかチェック
    if authorization != "Bearer " + ENV_KEY:
        raise HTTPException(status_code=401, detail="authorization failed")

    global data
    body = json_body.model_dump()
    for id, count in body["target"].items():
        # targetに指定されたidがstock内に存在するか確認
        if not id in data["stock"]:
            return HTTPException(status_code=404, detail="item id is not found")

        if data["stock"][id] - count <= 0:
            # マイナスにならないように
            data["stock"][id] = 0
        else:
            data["stock"][id] -= count

    return {"status": True, "data": data}


# プログラム終了時に呼ばれるの関数
@atexit.register
def save(signum=None, frame=None) -> None:
    with open(SAVE_DATA_PATH, mode="w", encoding="utf-8") as f:
        json.dump(data, f)
    print("[STATUS] Database File saved.")


if __name__ == "__main__":
    # SIGTERMシグナル時にも呼ばれるように
    signal.signal(signal.SIGTERM, save)

    if os.path.exists(SAVE_DATA_PATH):
        with open(SAVE_DATA_PATH, mode="r", encoding="UTF-8") as f:
            # データベースのファイルを読み込み
            data = json.load(f)
            pass

    print(ENV_KEY)

    # start fastapi server
    # import uvicorn

    # uvicorn.run(app=app, host=os.environ["IP"], port=int(os.environ["PORT"]))

    exit(0)

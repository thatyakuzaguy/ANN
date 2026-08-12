from fastapi import FastAPI

app = FastAPI(title="3D Pong Arena API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "3d-pong-arena"}

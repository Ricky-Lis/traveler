"""导出 FastAPI 应用的 OpenAPI 3.0 规范到 docs/openapi.json，供前端/工具使用。"""
import json
from pathlib import Path

# 项目根目录（脚本在 scripts/ 下）
ROOT = Path(__file__).resolve().parent.parent

def main():
    import sys
    sys.path.insert(0, str(ROOT))
    from app.main import app

    spec = app.openapi()
    if not spec.get("servers"):
        spec["servers"] = [{"url": "http://localhost:8000", "description": "本地开发"}]
    out_path = ROOT / "docs" / "openapi.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    print(f"Written: {out_path}")

if __name__ == "__main__":
    main()

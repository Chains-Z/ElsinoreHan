"""按真实游戏导出的纹理、UI网格和图层做软件合成预览；不称为GPU截图。"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "runtime/build/font-audit-deps"))
import UnityPy


def texture_data(directory, picture, sources, audit):
    if picture.get("raw_file"):
        data = (directory / picture["raw_file"]).read_bytes()
        return np.frombuffer(data, np.uint8).reshape(picture["height"], picture["width"], 4)[::-1] / 255.0
    obj = sources[picture["texture"]]
    texture = obj.read()
    data = texture.get_image_data()
    audit[picture["texture"]] = {"asset": obj.assets_file.name, "path_id": obj.path_id,
        "encoded_sha256": hashlib.sha256(data).hexdigest(), "format": texture.m_TextureFormat}
    mode = texture.m_TextureFormat
    size = texture.m_Width, texture.m_Height
    if mode in (10, 12):
        image = Image.frombytes("RGBA", size, data, "bcn", 1 if mode == 10 else 3)
    elif mode == 4:
        image = Image.frombytes("RGBA", size, data[:size[0] * size[1] * 4])
    else:
        raise ValueError("未核查的书页预览纹理格式：" + str(mode))
    return np.asarray(image)[::-1] / 255.0


def paint(canvas, vertices, triangles, texture, color=None, threshold=None):
    points = np.array([[v["x"], v["y"]] for v in vertices])
    uv = np.array([[v["u"], v["v"]] for v in vertices])
    left, top = np.maximum(np.floor(points.min(axis=0)).astype(int), (0, 0))
    right, bottom = np.minimum(np.ceil(points.max(axis=0)).astype(int), (canvas.shape[1], canvas.shape[0]))
    if right <= left or bottom <= top:
        return
    yy, xx = np.mgrid[top:bottom, left:right]
    xy = np.stack((xx + 0.5, yy + 0.5), axis=-1)
    mapped = np.zeros(xy.shape, dtype=float)
    valid = np.zeros(xx.shape, bool)
    for offset in range(0, len(triangles), 3):
        ids = triangles[offset:offset + 3]
        a, b, c = points[ids]
        determinant = np.cross(b - a, c - a).item()
        if abs(determinant) < 1e-8:
            continue
        d = xy - a
        wb = (d[:, :, 0] * (c - a)[1] - d[:, :, 1] * (c - a)[0]) / determinant
        wc = ((b - a)[0] * d[:, :, 1] - (b - a)[1] * d[:, :, 0]) / determinant
        wa = 1 - wb - wc
        use = (wa >= -1e-7) & (wb >= -1e-7) & (wc >= -1e-7) & ~valid
        coords = wa[:, :, None] * uv[ids[0]] + wb[:, :, None] * uv[ids[1]] + wc[:, :, None] * uv[ids[2]]
        mapped[use] = coords[use]
        valid |= use
    h, w = texture.shape[:2]
    tx = np.clip(mapped[:, :, 0] * w - 0.5, 0, w - 1)
    ty = np.clip((1 - mapped[:, :, 1]) * h - 0.5, 0, h - 1)
    x0, y0 = tx.astype(int), ty.astype(int)
    x1, y1 = np.minimum(x0 + 1, w - 1), np.minimum(y0 + 1, h - 1)
    fx, fy = (tx - x0)[:, :, None], (ty - y0)[:, :, None]
    sample = ((1 - fx) * (1 - fy) * texture[y0, x0] + fx * (1 - fy) * texture[y0, x1]
              + (1 - fx) * fy * texture[y1, x0] + fx * fy * texture[y1, x1])
    if threshold is not None:
        alpha = np.clip((sample[:, :, 0] - threshold) / 0.06 + 0.5, 0, 1) * color[3]
        sample = np.broadcast_to(color, (*xx.shape, 4)).copy()
        sample[:, :, 3] = alpha
    sample[:, :, 3] *= valid
    target = canvas[top:bottom, left:right]
    a = sample[:, :, 3:4]
    target[:, :, :3] = sample[:, :, :3] * a + target[:, :, :3] * (1 - a)
    target[:, :, 3:4] = a + target[:, :, 3:4] * (1 - a)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--game-data", type=Path, default=Path("D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data"))
    args = parser.parse_args()
    scenes = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(args.directory.glob("book-render-*.json"))]
    if not {"normal", "turn-left", "turn-right"}.issubset({scene["state"] for scene in scenes}):
        raise ValueError("书页预览必须同时包含静态、向左及向右翻页")
    wanted = {p["texture"] for s in scenes for p in s["pictures"] if not p.get("raw_file")}
    environment = UnityPy.load(str(args.game_data))
    sources = {}
    for obj in environment.objects:
        if obj.type.name == "Texture2D":
            name = obj.read().m_Name
            if name in wanted:
                if name in sources:
                    raise ValueError("原始预览纹理名称不唯一")
                sources[name] = obj
    audit, previews = {}, []
    for scene in scenes:
        canvas = np.ones((scene["height"], scene["width"], 4), dtype=float)
        canvas[:, :, :3] = 0.08
        commands = [(v["depth"], "image", v) for v in scene["pictures"]] + [(v["depth"], "glyph", v) for v in scene["glyphs"]]
        for _, kind, item in sorted(commands, key=lambda v: v[0]):
            if kind == "image":
                pixels = texture_data(args.directory, item, sources, audit)
                paint(canvas, item["vertices"], item["triangles"], pixels)
            else:
                raw = (args.directory / item["atlas"]).read_bytes()
                if len(raw) != item["atlas_width"] * item["atlas_height"]:
                    raise ValueError("预览字形图集不是已核查Alpha8")
                pixels = np.frombuffer(raw, np.uint8).reshape(item["atlas_height"], item["atlas_width"], 1)[::-1] / 255.0
                paint(canvas, item["vertices"], [0, 1, 2, 2, 3, 0], pixels, np.array(item["color"]), item["threshold"])
        path = args.directory / ("book-preview-" + scene["state"] + ".png")
        Image.fromarray(np.round(np.clip(canvas, 0, 1) * 255).astype(np.uint8)).save(path)
        previews.append({"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "state": scene["state"]})
    result = {"textures": audit, "previews": previews, "scope": "真实UI网格/字形/纹理的软件合成，SDF边缘近似，不是GPU或用户屏幕截图"}
    (args.directory / "book-preview-analysis.json").write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({"previews": len(previews), "source_textures": len(audit)}))


if __name__ == "__main__":
    main()

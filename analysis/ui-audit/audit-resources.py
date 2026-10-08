"""只读审核资源字段及 Unity 序列化组件中的玩家可见字符串。"""

from __future__ import annotations

import collections
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
import analyze

OUT = Path(__file__).resolve().parent
GAME = analyze.GAME
SUGGESTED = {
    "The Dungeon": "地牢", "The Guard House": "卫兵室", "Laertes's Chambers": "雷欧提斯的房间",
    "The Main Deck": "主甲板", "Polonius's Chambers": "波洛涅斯的房间", "Ophelia's Chambers": "奥菲莉娅的房间",
    "The Forest Path": "林间小径", "The Chapel": "礼拜堂", "A Dungeon Cell": "牢房", "Castle Town's Streets": "城镇街道",
    "The Grounds": "城堡外庭", "The Walls": "城墙", "The Kitchen": "厨房", "The Flinty & Steel": "燧石与钢酒馆",
    "The Great Hall": "大厅", "The Courtyard": "庭院", "The Graveyard": "墓地", "Claudius's Chambers": "克劳狄斯的房间",
    "The Captain's Quarters": "船长室", "The Guards' Quarters": "卫兵宿舍", "Lower Hallway": "下层走廊",
    "The Upper Deck": "上甲板", "Upper Hallway": "上层走廊", "The Landing": "平台", "The Royal Gallery": "王室画廊",
    "Lower Garden": "下层花园", "The Docks": "码头", "Hamlet's Chambers": "哈姆雷特的房间", "Shack": "小屋", "Limbo": "虚空",
    "Ship Wheel": "船舵", "Altar": "祭坛", "Missing Portrait": "空缺的肖像", "Pond": "池塘", "Large Grave": "大墓碑",
    "Guard Cot": "卫兵床铺", "The Queen's Plants": "王后的盆栽", "Large Urn": "大瓮", "Coat of Arms": "家徽",
    "Inlaid Cabinet": "镶嵌橱柜", "Fountain": "喷泉", "Grave": "墓碑", "Polonius's Hearth": "波洛涅斯的壁炉",
    "Assorted Papers": "杂乱的纸张", "My Mother's Diary": "母亲的日记", "Confiscation Table": "收缴物品桌",
    "Well": "水井", "Personal Belongings": "私人物品", "Rolled-Up Letter": "卷起的信", "Window Slit": "狭窄的窗缝",
    "Pans": "锅具", "Lady Edith": "伊迪丝夫人", "Portrait": "肖像", "Bucket": "水桶", "Statue": "雕像",
    "Stolen Portrait": "偷来的肖像", "Fireplace": "壁炉", "Hamlet's Bed": "哈姆雷特的床", "Gertrude's Hearth": "葛特露德的壁炉",
    "Table": "桌子", "The Fields": "田野", "Brother's Bed": "哥哥的床", "Stables": "马厩", "Curtains": "窗帘",
    "Queen's Portrait": "王后的肖像", "Plates": "盘子", "Books": "书籍", "Beautiful Portrait": "美丽的肖像",
    "Mother": "母亲", "Gertrude's Diary": "葛特露德的日记", "Chest": "箱子", "Food": "食物", "Stove": "炉灶",
    "My Dresser": "我的衣柜", "Weapons Rack": "武器架", "Straw": "稻草", "My Bed": "我的床", "Messy Papers": "凌乱的纸张",
    "Gertrude's Bed": "葛特露德的床", "Gertrude's Mirror": "葛特露德的镜子", "My Desk": "我的书桌", "Father's Bed": "父亲的床",
    "Next Page": "下一页", "Destroy Book": "毁掉书", "Previous Page": "上一页", "Open Map": "打开地图",
    "Conversation History": "对话记录", "Reset Loop": "重置循环", "Pause Game": "暂停游戏", "Open Timeline": "打开时间线",
    "Open Journal": "打开日志", "View Second Floor": "查看二楼", "View Next Loop": "查看下一轮循环",
    "View Previous Loop": "查看上一轮循环", "View First Floor": "查看一楼", "Next Line": "下一句", "Listen to Event": "旁听事件",
    "Loading...": "正在加载……", "FIN": "终", "Show Buttons": "显示按钮",
    "Lady of Denmark": "丹麦贵族小姐", "Prince of Denmark, Former Paramour": "丹麦王子，昔日恋人",
    "Queen Consort of Denmark, Mother to Hamlet": "丹麦王后，哈姆雷特的母亲", "King of Denmark, Uncle to Hamlet": "丹麦国王，哈姆雷特的叔父",
    "Chamberlain, Duke of Denmark, My Father": "宫廷总管，丹麦公爵，我的父亲", "Lord of Denmark, My Brother": "丹麦贵族，我的哥哥",
    "Lady-in-Waiting to Her Highness": "王后的侍女", "Friend to Hamlet, Soldier, Poet": "哈姆雷特的朋友，士兵，诗人",
    "Castle Cook, Attendant to Her Majesty": "城堡厨娘，王后的侍从", "Knight-Guard of Elsinore": "埃尔西诺的卫兵骑士",
    "Master Chamberlain, Duke of Denmark, Father": "宫廷总管，丹麦公爵，父亲", "Lord of Denmark, Brother": "丹麦贵族，哥哥",
    "Lady of Denmark, Friend to Hamlet": "丹麦贵族小姐，哈姆雷特的朋友", "Playmaster": "剧团团长",
    "Former King of Denmark, Father to Hamlet": "丹麦先王，哈姆雷特的父亲", "Prince of Norway, Would-Be Conqueror": "挪威王子，野心勃勃的征服者",
    "Barkeep, Teller of Tall Tales": "酒馆老板，爱讲奇闻轶事", "Pirate Queen of Connacht": "康诺特的海盗女王",
    "Former King of Denmark, Hamlet's Father": "丹麦先王，哈姆雷特的父亲",
    "Ah. Ophelia. What's wrong?": "啊，奥菲莉娅。出什么事了？", "What? This had better be important.": "什么事？最好是要紧事。",
    "Hello, love. What would you like to discuss?": "你好，亲爱的。你想聊什么？", "Good to see you.": "见到你真好。",
    "Yes? What?": "嗯？什么事？", "Hello, lass. How goes it?": "你好，姑娘。近来怎么样？", "Be quick about it.": "有话快说。",
    "What can I do fer ye?": "有什么能帮你的？", "How can I be of assistance today?": "今天有什么需要我帮忙的？",
    "At your service, my lady.": "听候您的吩咐，小姐。", "At yer service, m'lady!": "听您吩咐，小姐！",
    "I am, in theory, above gossip... what would you like to say?": "按理说，我不该过问闲话……你想说什么？",
    "What's the latest dirt?": "最近有什么八卦？", "Hello, my heart. What is it?": "你好，我的心肝。什么事？",
    "What news, sister?": "有什么消息，妹妹？", "Out with it, my lady! I'm a busy woman!": "有话直说，小姐！我还忙着呢！",
    "What's the gossip du jour, Lady Ophelia?": "今天有什么新鲜传闻，奥菲莉娅小姐？", "Ah... A familiar face...": "啊……一张熟悉的面孔……",
    "Our performances' plots are ever-changing... What's the gossip du jour, Lady Ophelia?": "我们的戏码总在变化……今天有什么新鲜传闻，奥菲莉娅小姐？",
    "Mother's Grave": "母亲的墓碑", "Locked Chest": "锁上的箱子", "King's Portrait": "国王的肖像", "Landscape": "风景画",
    "Weapon Rack": "武器架", "Bookshelf": "书架", "Letter to Claudius": "致克劳狄斯的信",
    "Cleocatra": "克莉奥猫特拉", "Echo": "埃科", "Edgar": "埃德加", "Junior": "小家伙", "Marellow": "马洛",
    "Maxine": "玛克辛", "Misty": "米斯蒂", "Oedipuss": "俄狄喵斯", "Simon": "西蒙", "Clementine": "克莱门汀",
    "Kiki": "琪琪", "Maple": "枫枫", "Max": "麦克斯", "Mina": "米娜",
    "Polonius, Quince": "波洛涅斯、奎因斯", "Rosencrantz, Guildenstern": "罗森克兰兹、吉尔登斯吞",
    "King Hamlet": "哈姆雷特先王", "Irma, Simona": "伊尔玛、西蒙娜", "Grace O'Malley": "格蕾丝·奥马利",
    "Music and Lyrics": "作曲、作词", "Vocals": "演唱", "Violin": "小提琴", "Cello": "大提琴", "Winds": "管乐",
    "Guitar": "吉他", "Music and Lyrics, Choir": "作曲、作词、合唱", "Choir": "合唱", "Viola": "中提琴",
    "Guitar, Gango": "吉他、Gango", "Strings": "弦乐", "Music": "作曲", "Lyrics": "作词",
    "String Quartet courtesy of Xiaoan Li": "弦乐四重奏由Xiaoan Li提供",
    "Brit": "布莉特", "Fortinbras": "福丁布拉斯",
}
SUGGESTED = {source: target.replace("葛特露德", "乔特鲁德")
             .replace("福廷布拉斯", "福丁布拉斯").replace("布里特", "布莉特")
             .replace("的房间", "的寝室") for source, target in SUGGESTED.items()}


def read_serialized(path):
    """读取本机 Unity v17 的对象表，不运行组件，也不读取存档。"""
    data = path.read_bytes()
    metadata_size, file_size, version, data_offset = struct.unpack_from(">4I", data)
    if version != 17 or data[16] != 0:
        raise ValueError("当前解析器只支持本机的小端 Unity v17")
    pos = data.index(0, 20) + 1
    platform = struct.unpack_from("<i", data, pos)[0]
    pos += 4
    has_tree = data[pos]
    pos += 1
    if has_tree:
        raise ValueError("发现类型树，不能继续按无类型树结构读取")
    count = struct.unpack_from("<i", data, pos)[0]
    pos += 4
    types = []
    for _ in range(count):
        class_id, stripped, script_index = struct.unpack_from("<iBh", data, pos)
        pos += 7
        if class_id == 114:
            pos += 16
        pos += 16
        types.append((class_id, script_index))
    count = struct.unpack_from("<i", data, pos)[0]
    pos += 4
    objects = {}
    for _ in range(count):
        pos = (pos + 3) & ~3
        object_id, offset, size, type_index = struct.unpack_from("<qIIi", data, pos)
        pos += 20
        objects[object_id] = {"class_id": types[type_index][0], "script_index": types[type_index][1],
                              "offset": data_offset + offset, "size": size}
    script_count = struct.unpack_from("<i", data, pos)[0]
    pos += 4
    for _ in range(script_count):
        pos += 4
        pos = (pos + 3) & ~3
        pos += 8
    external_count = struct.unpack_from("<i", data, pos)[0]
    pos += 4
    externals = []
    for _ in range(external_count):
        pos = data.index(0, pos) + 1
        pos += 20
        end = data.index(0, pos)
        externals.append(data[pos:end].decode("utf-8"))
        pos = end + 1
    return {"data": data, "objects": objects, "externals": externals}


def read_string(data, pos):
    length = struct.unpack_from("<i", data, pos)[0]
    if length < 0 or length > len(data) - pos - 4:
        raise ValueError("字符串长度越界")
    return data[pos + 4:pos + 4 + length].decode("utf-8"), (pos + 4 + length + 3) & ~3


def main():
    translations = json.loads((ROOT / "translation/sol-full-2026-10-09/translations.json").read_text(encoding="utf-8"))
    exact = {r["source"]: r for r in translations}
    normalized = {analyze.normalize(r["source"]): r for r in translations}
    inventory = json.loads((ROOT / "analysis/text_inventory.json").read_text(encoding="utf-8"))
    extracted = {analyze.normalize(r["text"]) for r in inventory}
    rows = []
    errors = []
    assets = list(analyze.read_text_assets((GAME / "resources.assets").read_bytes()))

    def add(source, origin, decision, reason, category, **extra):
        row = {"source": source, "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
               "origin": origin, "decision": decision, "reason": reason, "category": category, **extra}
        if source in exact:
            row.update(coverage="exact", translation_id=exact[source]["id"], target=exact[source]["target"])
        elif analyze.normalize(source) in normalized:
            match = normalized[analyze.normalize(source)]
            row.update(coverage="whitespace_normalized", translation_id=match["id"], target=match["target"])
        else:
            row["coverage"] = "missing"
        row["in_primary_inventory"] = analyze.normalize(source) in extracted
        if decision == "player_facing":
            row["decision"] = "covered" if row["coverage"] != "missing" else "candidate"
        rows.append(row)

    display_fields = {"text", "slug", "title", "subtitle", "long", "short", "description", "presentline", "categories"}
    technical_roots = {"animations", "musiccues", "smalltalk", "config", "anim_prop_mapping"}

    def visit(value, asset, digest, path="$", field="", parent=None):
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, asset, digest, path + "." + key, key, value)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, asset, digest, path + f"[{index}]", field, parent)
        elif isinstance(value, str):
            origin = {"file": "resources.assets", "asset": asset, "asset_sha256": digest,
                      "json_path": path, "field": field, "record_id": parent.get("id") if isinstance(parent, dict) else None}
            if not value.strip():
                add(value, origin, "excluded", "空字段", "empty")
            elif not re.search(r"[A-Za-z]", value):
                add(value, origin, "excluded", "不含英文字母的符号或数字，不新增英文译文", "symbols")
            elif asset in technical_roots:
                add(value, origin, "excluded", "配置、动画、音乐或场景调度标识，不是显示正文", "technical")
            elif asset == "credits" and field in {"name", "main", "team", "testers", "backers", "thanks", "pets"}:
                add(value, origin, "excluded", "片尾真实署名或宠物致谢名称，保留原名，不改写姓名", "credit_name")
            elif asset == "credits" and field == "title":
                if value in exact or analyze.normalize(value) in normalized:
                    add(value, origin, "player_facing", "片尾标题已有同名译文，保留既有覆盖", "credit_song_title")
                else:
                    add(value, origin, "retain_original", "片尾歌曲作品原名，保留便于查找，不自造官方中文题名", "credit_song_title")
            elif asset == "name_mapping" or field in display_fields or (asset == "pets" and field == "name") or (asset == "credits" and field in {"role", "roles"}):
                if value in {"N/A", "I SHOULDN'T BE PRESENTABLE", "CAN'T SEE THIS MEAL PREP"}:
                    add(value, origin, "excluded", "显式开发占位或不应展示的角色调试台词", "placeholder")
                else:
                    add(value, origin, "player_facing", "显示字段；不使用词数或长度门槛", "resource_ui")
            elif field == "name" and asset in {"schedule", "schedule_background", "endings", "knowledge", "information", "bios", "closeups", "leads"}:
                add(value, origin, "player_facing", "事件或资料的显示名称字段", "resource_ui")
            else:
                add(value, origin, "excluded", "内部ID、条件、场景、音效、标记或资源地址字段", "technical")

    for name, digest, text in assets:
        if name.startswith("scenes") or name == "common_declarations":
            # 对话正文已有全量来源清单；此任务只审核 UI 资源字段。
            continue
        if name == "event-html":
            add("event-html", {"file": "resources.assets", "asset": name, "asset_sha256": digest},
                "excluded", "开发人员事件数据HTML，含条件、ID与调度说明；不是游戏UI数据入口", "developer_report")
            continue
        try:
            visit(analyze.read_json(text), name, digest)
        except json.JSONDecodeError as error:
            errors.append({"asset": name, "sha256": digest, "error": str(error), "fallback": "宽松处理字符串外的00数字，不修补真实资源"})
            cleaned = re.sub(
                r'"(?:\\.|[^"\\])*"|(?<![A-Za-z0-9_.])0+(\d+)(?![A-Za-z0-9_.])',
                lambda match: match.group() if match.group().startswith('"') else str(int(match.group())),
                analyze.remove_comments(text),
            )
            try:
                visit(analyze.read_json(cleaned), name, digest)
                continue
            except json.JSONDecodeError:
                pass
            # 残存测试资源也可能有无效引号；保留字符串字段字节位置与行号。
            for match in re.finditer(r'"(?P<field>[^"\\]+)"\s*:\s*"(?P<value>(?:\\.|[^"\\])*)"', analyze.remove_comments(text)):
                source = json.loads('"' + match.group("value") + '"')
                field = match.group("field")
                origin = {"file": "resources.assets", "asset": name, "asset_sha256": digest,
                          "field": field, "character_offset": match.start(), "line": text.count("\n", 0, match.start()) + 1,
                          "parser": "field_string_fallback"}
                decision = "player_facing" if field in display_fields or field == "name" else "excluded"
                add(source, origin, decision, "显示字段词法回收" if decision == "player_facing" else "内部字段词法回收", "resource_ui" if decision == "player_facing" else "technical")

    files = {}
    for path in GAME.iterdir():
        if path.name.endswith(".assets") or re.fullmatch(r"level\d+", path.name):
            try:
                files[path.name] = read_serialized(path)
            except Exception as error:
                errors.append({"file": path.name, "error": str(error)})
    scripts = {}
    for name, data in files.items():
        for path_id, obj in data["objects"].items():
            if obj["class_id"] != 115:
                continue
            raw = data["data"][obj["offset"]:obj["offset"] + obj["size"]]
            try:
                script_name, pos = read_string(raw, 0)
                pos += 20
                classname, pos = read_string(raw, pos)
                namespace, pos = read_string(raw, pos)
                assembly, pos = read_string(raw, pos)
                scripts[(name, path_id)] = {"name": script_name, "class": classname, "namespace": namespace, "assembly": assembly}
            except Exception as error:
                errors.append({"file": name, "path_id": path_id, "class": "MonoScript", "error": str(error)})
    component_stats = collections.Counter()
    for name, data in files.items():
        for path_id, obj in data["objects"].items():
            if obj["class_id"] != 114:
                continue
            raw = data["data"][obj["offset"]:obj["offset"] + obj["size"]]
            try:
                file_id, script_id = struct.unpack_from("<iq", raw, 16)
                script_file = Path(data["externals"][file_id - 1]).name if file_id else name
                script = scripts.get((script_file, script_id), {})
                object_name, pos = read_string(raw, 28)
            except Exception as error:
                errors.append({"file": name, "path_id": path_id, "class": "MonoBehaviour", "error": str(error)})
                continue
            classname = script.get("class", "unknown")
            component_stats[classname] += 1
            # 无类型树文件只做组件归属可追溯的四字节对齐字符串扫描；具体字段须通过 IL 消费者核对。
            for offset in range(pos, len(raw) - 4, 4):
                length = struct.unpack_from("<i", raw, offset)[0]
                if not 1 <= length <= min(20000, len(raw) - offset - 4):
                    continue
                payload = raw[offset + 4:offset + 4 + length]
                if any(b < 32 and b not in (9, 10, 13) for b in payload):
                    continue
                try:
                    source = payload.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                if not re.search(r"[A-Za-z]", source):
                    continue
                origin = {"file": name, "path_id": path_id, "class": classname, "component_name": object_name,
                          "script": script, "object_offset": offset, "absolute_offset": obj["offset"] + offset,
                          "parser": "aligned_length_prefixed_utf8"}
                decision = "excluded"
                category = "technical"
                reason = "组件配置、动画状态、输入绑定/设备数据库、字体字形、音效或对象引用；无玩家文字显示路径"
                if classname == "RoomMarker" and offset == pos:
                    decision, category, reason = "player_facing", "room_name", "RoomMarker.playerFacingName；UiStrings.FormatRoomId与ExplorationUI.updateTimeText消费"
                    origin["field"] = "playerFacingName"
                    origin["ui_path"] = "RoomMarker.playerFacingName -> UiStrings.FormatRoomId / ExplorationUI.updateTimeText -> TMP_Text.SetText"
                elif classname == "ObservableSceneObject":
                    _, object_name_pos = read_string(raw, pos)
                    if offset == object_name_pos:
                        decision, category, reason = "player_facing", "interaction_label", "ObservableSceneObject.ObjectName；IInteractable.get_Tooltip消费"
                        origin["field"] = "ObjectName"
                        origin["ui_path"] = "ObservableSceneObject.ObjectName -> IInteractable.get_Tooltip -> ExplorationUI.Tooltip"
                    else:
                        reason = "ObservableSceneObject.SceneName为Enviro_*剧情场景ID，不是ObjectName显示字段"
                        origin["field"] = "SceneName"
                elif classname in {"ElsinoreButton", "StandardButton"} and offset == 264:
                    decision, category, reason = "player_facing", "button_tooltip", "ElsinoreButton.tooltip；IInteractable.get_Tooltip消费"
                    origin["field"] = "tooltip"
                    origin["ui_path"] = "ElsinoreButton.tooltip -> IInteractable.get_Tooltip -> UI Tooltip"
                elif classname == "TextMeshProUGUI" and offset == 68:
                    decision, category, reason = "player_facing", "tmp_text", "TextMeshProUGUI.m_text序列化默认显示文本；需区分真实标签和开发占位"
                    origin["field"] = "m_text"
                    placeholders = ("Lorem ipsum", "I'm some text that's talking", "I am a description of the hearsay", "I am some rather", "Ver. 0.0.0", "Some Button", "Option Text", "fdsf", "bedroom_ophelia -", "Day 1, 07:02", "\\n\\n\\n\\n\\nCredits go here.")
                    if source.startswith(placeholders) or "<b>Some Time</b> Log Entry" in source:
                        decision, category, reason = "excluded", "placeholder", "TMP开发占位、默认调试值或随后由真实数据替换的字段"
                    else:
                        origin["ui_path"] = "TextMeshProUGUI.m_text -> UI静态默认显示"
                elif classname == "Text" and offset == 124:
                    decision, category, reason = "excluded", "placeholder", "FPS调试标签或NotificationItem模板默认文本"
                add(source, origin, decision, reason, category)

    OUT.mkdir(exist_ok=True)
    (OUT / "resource-strings.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    candidates = {}
    suggestions_file = OUT / "resource-suggested-translations.json"
    if suggestions_file.exists():
        SUGGESTED.update(json.loads(suggestions_file.read_text(encoding="utf-8")))
    for row in rows:
        if row["decision"] != "candidate":
            continue
        candidate = candidates.setdefault(row["source"], {"source": row["source"], "source_sha256": row["source_sha256"],
            "coverage": row["coverage"], "decision": "candidate", "origins": [], "categories": [], "reasons": []})
        candidate["origins"].append(row["origin"])
        for key, value in [("categories", row["category"]), ("reasons", row["reason"])]:
            if value not in candidate[key]:
                candidate[key].append(value)
        if row["source"] in SUGGESTED:
            candidate["suggested_target"] = SUGGESTED[row["source"]]
        elif row["source"].startswith("Peculiar Tales, Vol. "):
            candidate["suggested_target"] = "奇闻异事，第" + row["source"].rsplit(" ", 1)[1] + "卷"
        elif row["source"].replace("\\n", "\n") in exact:
            candidate["suggested_target"] = exact[row["source"].replace("\\n", "\n")]["target"]
            candidate["suggested_target_note"] = "复用现有真实译文；该序列化版本包含字面量反斜杠n"
    (OUT / "resource-ui-candidates.json").write_text(json.dumps(list(candidates.values()), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "resource-exclusions.json").write_text(json.dumps([row for row in rows if row["decision"] == "excluded"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"text_asset_count": len(assets), "serialized_files": list(files), "audited_occurrences": len(rows),
               "decisions": dict(collections.Counter(row["decision"] for row in rows)),
               "coverage": dict(collections.Counter(row["coverage"] for row in rows if row["decision"] in {"covered", "candidate"})),
               "unique_candidates": len(candidates), "candidate_categories": dict(collections.Counter(category for row in candidates.values() for category in row["categories"])),
               "candidate_suggestions": sum("suggested_target" in row for row in candidates.values()),
               "retained_song_titles": [row for row in rows if row["decision"] == "retain_original"],
               "component_classes": dict(component_stats), "errors": errors,
               "ui_evidence": "analysis/ui-audit/assembly-ui-paths.il.txt",
               "limitations": ["静态资源审计，不是游戏像素验收", "无类型树资源通过对象表、MonoScript归属、字段偏移与IL消费者联合审核", "保留未启用测试资源，不宣称均为可达UI", "场景对白由既有全量清单和独立程序集审计负责", "未添加字体字形、Wwise标识或Rewired第三方硬件数据库作为翻译源"]}
    (OUT / "resource-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ["audited_occurrences", "decisions", "coverage", "unique_candidates", "candidate_categories", "candidate_suggestions"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()

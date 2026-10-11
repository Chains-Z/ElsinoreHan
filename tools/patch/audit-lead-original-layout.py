"""只读核查原游戏任务预制体字号和祖先CanvasScaler；不启动游戏。"""
import hashlib
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'runtime/build/font-audit-deps'))
import UnityPy
from UnityPy.classes import PPtr

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--game-data', type=Path, default=Path('D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data'))
parser.add_argument('--output', type=Path, default=ROOT / 'runtime/build/lead-original-resource-audit.json')
args = parser.parse_args()
GAME = args.game_data
environment = UnityPy.load(*(str(GAME / n) for n in (
    'level1', 'sharedassets1.assets', 'globalgamemanagers.assets', 'sharedassets0.assets')))

def pointer(obj, offset):
    file_id, path_id = struct.unpack_from('<iq', obj.get_raw_data(), offset)
    return PPtr(m_FileID=file_id, m_PathID=path_id, assetsfile=obj.assets_file)

def script_name(obj):
    try:
        return obj.read(check_read=False).m_Script.read().m_ClassName
    except Exception:
        return None

def identity(obj):
    return {'asset': obj.assets_file.name, 'path_id': obj.path_id,
            'raw_sha256': hashlib.sha256(obj.get_raw_data()).hexdigest()}

def text_data(obj):
    """按本游戏DLL的序列化字段顺序读至字号；校验空事件与字段边界。"""
    raw = obj.get_raw_data()
    # MonoBehaviour头32，Graphic的Material12、Color16、RaycastTarget4。
    assert struct.unpack_from('<i', raw, 64)[0] == 0, 'Cull事件存在持久监听，不能使用此固定前缀'
    length = struct.unpack_from('<i', raw, 68)[0]
    text = raw[72:72+length].decode('utf-8')
    start = (72+length+3)//4*4
    offset = start
    fields = {}
    sizes = [('m_isRightToLeft',4),('m_fontAsset',12),('m_sharedMaterial',12)]
    for name, size in sizes:
        fields[name] = offset
        offset += size
    count = struct.unpack_from('<i',raw,offset)[0]
    offset += 4 + count*12
    offset += 12  # m_fontMaterial。
    count = struct.unpack_from('<i',raw,offset)[0]
    offset += 4 + count*12
    # Color32、Color、顶点渐变开关、ColorMode、四角颜色、渐变预设、sprite、两开关、两Color32。
    offset += 4+16+4+4+64+12+12+4+4+4+4
    result = identity(obj)
    result.update(text=text, font_size_offset=offset,
                  font_size=struct.unpack_from('<f',raw,offset)[0],
                  font_size_base=struct.unpack_from('<f',raw,offset+4)[0],
                  font_weight=struct.unpack_from('<i',raw,offset+8)[0],
                  enable_auto_sizing=bool(struct.unpack_from('<i',raw,offset+12)[0]),
                  font_size_min=struct.unpack_from('<f',raw,offset+16)[0],
                  font_size_max=struct.unpack_from('<f',raw,offset+20)[0],
                  enable_word_wrapping=bool(struct.unpack_from('<i',raw,offset+56)[0]),
                  overflow_mode=struct.unpack_from('<i',raw,offset+64)[0])
    font = pointer(obj,fields['m_fontAsset']).deref()
    result['font_asset'] = identity(font)
    result['font_name'] = font.read_typetree(check_read=False)['m_Name']
    return result

def ancestry(go):
    result=[]
    while go:
        game_object=go.read()
        row=identity(go)
        row['name']=game_object.m_Name
        transform=None
        components=[]
        for pair in game_object.m_Component:
            obj=pair.component.deref()
            name=script_name(obj) if obj.type.name=='MonoBehaviour' else obj.type.name
            components.append(name)
            if obj.type.name in ('RectTransform','Transform'):
                transform=obj.read()
                if obj.type.name=='RectTransform':
                    row['rect_transform']=obj.read_typetree()
            if name=='CanvasScaler':
                raw=obj.get_raw_data()
                row['canvas_scaler']=dict(identity(obj),
                    ui_scale_mode=struct.unpack_from('<i',raw,32)[0],
                    reference_pixels_per_unit=struct.unpack_from('<f',raw,36)[0],
                    scale_factor=struct.unpack_from('<f',raw,40)[0],
                    reference_resolution=struct.unpack_from('<ff',raw,44),
                    screen_match_mode=struct.unpack_from('<i',raw,52)[0],
                    match_width_or_height=struct.unpack_from('<f',raw,56)[0])
            if name=='SplotchGenerator':
                raw=obj.get_raw_data()
                row['splotch_generator']=dict(identity(obj),
                    extrusion=struct.unpack_from('<ff',raw,48),
                    mode=struct.unpack_from('<i',raw,56)[0],
                    color_palette=struct.unpack_from('<i',raw,60)[0])
        row['components']=components
        result.append(row)
        if transform is None or not transform.m_Father.m_PathID:
            break
        go=transform.m_Father.read().m_GameObject.deref()
    return result

items=[]
for obj in list(environment.objects):
    if obj.type.name!='MonoBehaviour' or script_name(obj)!='JournalLeadsTab':
        continue
    prefab=pointer(obj,32).deref()
    text=pointer(prefab,32).deref()
    items.append({'journal_leads_tab':identity(obj),'lead_prefab':identity(prefab),
                  'text':text_data(text),'text_ancestry':ancestry(text.read(check_read=False).m_GameObject.deref()),
                  'prefab_ancestry':ancestry(prefab.read(check_read=False).m_GameObject.deref()),
                  'scene_ancestry':ancestry(obj.read(check_read=False).m_GameObject.deref())})
report={'method':'原始level1中JournalLeadsTab的LeadSelectionPrefab引用，沿LeadItem.Text读取原生序列化值；未启动游戏',
        'assets_sha256':{n:hashlib.sha256((GAME/n).read_bytes()).hexdigest() for n in ('level1','sharedassets1.assets')},
        'items':items}
output=args.output
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'items': len(items), 'font_sizes': [item['text']['font_size'] for item in items],
                  'fonts': [item['text']['font_name'] for item in items], 'output': str(output)}, ensure_ascii=False))

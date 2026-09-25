from flask import Flask, request, send_file
import requests
from PIL import Image
from io import BytesIO
import os

fallback_ids = ["211000000", "214000000", "208000000", "203000000", "204000000", "205000000", "212000000"]
DEFAULT_ID = "710034057"

app = Flask(__name__)
session = requests.Session()

API_KEY = "M7MAD"
BACKGROUND_FILENAME = "outfit.png"
ICON_SIZE = (95, 95)

# ✅ API Games Kinbo (اللي في البوت)
INFO_API_URL = "https://api.gameskinbo.com/ff-info/get"
INFO_API_KEY = "CZwkGnWw0TzJqqfU9RqV_dQ7SBZkmUxCZzABO38rQ7k"

HEX_POSITIONS = {
    "mask": (990, 420),
    "shirt": (190, 90),
    "pants": (40, 420),
    "shoes": (840, 90),
    "emote": (40, 230),
    "armor": (990, 230),
    "character": (600, 390),
    "weapon": (190, 560),
    "pet": (840, 560)
}

def fetch_icon(icon_id):
    ids_to_try = []
    if icon_id and str(icon_id) != "0":
        ids_to_try.append(str(icon_id))
    for fid in fallback_ids:
        if fid not in ids_to_try:
            ids_to_try.append(fid)
    for i in ids_to_try:
        try:
            url = f"https://iconapi.wasmer.app/{i}"
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                img = Image.open(BytesIO(r.content)).convert("RGBA")
                return img.resize(ICON_SIZE, Image.Resampling.LANCZOS)
        except:
            continue
    return None

@app.route('/outfit-image', methods=['GET'])
def outfit_image():
    uid = request.args.get('uid')
    key = request.args.get('key')
    
    if key != API_KEY:
        return {"error": "Key Error"}, 401
    
    # ✅ جلب البيانات من Games Kinbo API
    try:
        api_url = f"{INFO_API_URL}?uid={uid}"
        headers = {"x-api-key": INFO_API_KEY}
        resp = session.get(api_url, headers=headers, timeout=30)
        data = resp.json()
    except Exception as e:
        return {"error": f"API Down: {str(e)}"}, 500
    
    if not data or not data.get("AccountInfo"):
        return {"error": "Player not found"}, 404
    
    # ✅ استخراج الحقول الجديدة
    equipped = data.get("EquippedItemsInfo", {})
    pet_info = data.get("PetInfo", {})
    
    # ✅ Outfit list (من الرد الجديد)
    clothes = equipped.get("EquippedOutfit") or []
    
    # ✅ Avatar ID
    avatar_id = equipped.get("EquippedAvatarId")
    
    # ✅ Pet Skin
    pet_skin = pet_info.get("skinId")
    
    # ✅ Weapon
    weapons = equipped.get("EquippedWeapon") or []
    weapon_skin = weapons[0] if weapons else None
    
    # ✅ ترتيب القطع (6 قطع)
    draw_tasks = {
        "mask": clothes[0] if len(clothes) > 0 else None,
        "shirt": clothes[1] if len(clothes) > 1 else None,
        "pants": clothes[2] if len(clothes) > 2 else None,
        "shoes": clothes[3] if len(clothes) > 3 else None,
        "emote": clothes[4] if len(clothes) > 4 else None,
        "armor": clothes[5] if len(clothes) > 5 else None,
        "weapon": weapon_skin,
        "pet": pet_skin
    }
    
    # ✅ Avatar كـ character
    if avatar_id:
        draw_tasks["character"] = avatar_id
    
    if not os.path.exists(BACKGROUND_FILENAME):
        return "File Not Found", 500
    
    try:
        canvas = Image.open(BACKGROUND_FILENAME).convert("RGBA")
        
        for slot, item_id in draw_tasks.items():
            if not item_id:
                continue
            
            icon_img = fetch_icon(item_id)
            if not icon_img:
                continue
            
            if slot == "character":
                icon_img = icon_img.resize((480, 480), Image.Resampling.LANCZOS)
                x, y = HEX_POSITIONS["character"]
                w, h = icon_img.size
                pos = (x - w // 2, y - h // 2)
            else:
                pos = HEX_POSITIONS.get(slot)
            
            if not pos:
                continue
            
            canvas.paste(icon_img, pos, icon_img)
        
        img_io = BytesIO()
        canvas.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

# ✅ Vercel handler
handler = app
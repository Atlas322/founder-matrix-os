# Set this device's Discord bot avatar (🖥️ PC = blue monitor, 🍎 Mac = black apple-ish). Run once per device.
import base64, io, pathlib, sys, requests
from PIL import Image, ImageDraw

mac = sys.platform == "darwin"
S = 512
im = Image.new("RGB", (S, S), (20, 20, 20) if mac else (27, 92, 255))
d = ImageDraw.Draw(im)
if mac:
    d.ellipse([136, 170, 376, 410], fill="white")          # apple body
    d.ellipse([300, 230, 400, 330], fill=(20, 20, 20))     # bite
    d.ellipse([236, 100, 300, 170], fill="white")          # leaf
else:
    d.rounded_rectangle([96, 120, 416, 330], 28, fill="white")
    d.rounded_rectangle([120, 144, 392, 306], 14, fill=(27, 92, 255))
    d.rectangle([236, 330, 276, 386], fill="white")
    d.rounded_rectangle([170, 384, 342, 408], 12, fill="white")
buf = io.BytesIO(); im.save(buf, "PNG")
tok = (pathlib.Path.home() / ".fmos_discord_token").read_text().strip()
r = requests.patch("https://discord.com/api/v10/users/@me", headers={"Authorization": f"Bot {tok}"},
                   json={"avatar": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()})
print(r.status_code, r.json().get("username"))

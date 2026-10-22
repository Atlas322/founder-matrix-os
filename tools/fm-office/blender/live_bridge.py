"""Live bridge: таны нээлттэй Blender дотор Claude-ийн командыг шууд ажиллуулна (Figma bridge-тэй ижил санаа).

Хэрэглэх: Blender → Scripting таб → Open → энэ файл → ▶ Run Script (нэг удаа). Зогсоох: доорх STOP файл үүсгэх эсвэл Blender-ийг хаах.
Ажиллах зарчим: секунд тутам ~/.fmos/blender-inbox/*.py файлыг шалгаж, байвал ажиллуулаад done/ руу зөөнө.
Үр дүн/алдаа нь ~/.fmos/blender-inbox/log.txt-д бичигдэнэ. Зөвхөн энэ хавтсанд бичигдсэн файлыг л ажиллуулна.
"""
import bpy, traceback, time
from pathlib import Path

INBOX = Path.home() / ".fmos" / "blender-inbox"
DONE = INBOX / "done"
INBOX.mkdir(parents=True, exist_ok=True); DONE.mkdir(exist_ok=True)
LOG = INBOX / "log.txt"


def log(msg):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def tick():
    if (INBOX / "STOP").exists():
        log("bridge зогслоо"); return None
    for f in sorted(INBOX.glob("*.py")):
        try:
            code = f.read_text(encoding="utf-8")
            exec(compile(code, str(f), "exec"), {"bpy": bpy, "__name__": "__live__", "__file__": str(f)})
            log(f"OK {f.name}")
        except Exception:
            log(f"ERR {f.name}\n{traceback.format_exc()}")
        f.replace(DONE / f"{time.strftime('%H%M%S')}_{f.name}")
    return 1.0


if not bpy.app.timers.is_registered(tick):
    bpy.app.timers.register(tick, first_interval=1.0, persistent=True)
log("bridge асав: " + bpy.data.filepath)
print("FM live bridge асав →", INBOX)

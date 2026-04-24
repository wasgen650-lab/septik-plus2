import os
import shutil
import asyncio
from pathlib import Path
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_DIR = os.getenv("BASE_DIR", "")
WORK_DIR = BASE_DIR if BASE_DIR else os.path.expanduser("~")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_current_path = {}

class FileActions(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_copy_path = State()
    waiting_for_move_path = State()
    waiting_for_new_folder = State()

def get_safe_path(user_id, requested_path=None):
    current = user_current_path.get(user_id, WORK_DIR)
    if requested_path:
        if requested_path == "..":
            parent = str(Path(current).parent)
            if WORK_DIR and not Path(parent).resolve().is_relative_to(Path(WORK_DIR).resolve()):
                return current
            return parent
        new_path = os.path.abspath(os.path.join(current, requested_path))
        if WORK_DIR and not Path(new_path).resolve().is_relative_to(Path(WORK_DIR).resolve()):
            return current
        return new_path
    return os.path.abspath(current)

def get_icon(path):
    if os.path.isdir(path): return "📁"
    ext = Path(path).suffix.lower()
    return {'.txt':'📄','.py':'🐍','.exe':'⚙️','.jpg':'🖼️','.jpeg':'🖼️','.png':'🖼️',
            '.mp3':'🎵','.mp4':'🎬','.zip':'🗜️','.docx':'📃','.xlsx':'📊',
            '.pdf':'📕','.json':'🔧','.sh':'⚡','.md':'📝'}.get(ext,'📎')

def fmt_size(b):
    for u in ['B','KB','MB','GB']:
        if b < 1024: return f"{b:.1f}{u}"
        b /= 1024
    return f"{b:.1f}TB"

async def send_dir(message, uid, path, edit=False):
    if not os.path.exists(path) or not os.path.isdir(path):
        await message.answer("❌ Папка не существует"); return
    user_current_path[uid] = path
    try: items = os.listdir(path)
    except PermissionError:
        await message.answer("🚫 Нет доступа"); return

    folders = sorted([i for i in items if os.path.isdir(os.path.join(path,i))], key=str.lower)
    files   = sorted([i for i in items if os.path.isfile(os.path.join(path,i))], key=str.lower)

    kb = []
    if Path(path).resolve() != Path(WORK_DIR).resolve():
        kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:..")])
    for f in folders[:20]:
        kb.append([InlineKeyboardButton(text=f"📁 {f}", callback_data=f"open:{f}")])
    for f in files[:30]:
        fp = os.path.join(path, f)
        sz = fmt_size(os.path.getsize(fp))
        ico = get_icon(fp)
        lbl = f"{ico} {f[:24]}{'…' if len(f)>24 else ''} [{sz}]"
        kb.append([
            InlineKeyboardButton(text=lbl, callback_data=f"file:{f}"),
            InlineKeyboardButton(text="✏️", callback_data=f"rename:{f}"),
            InlineKeyboardButton(text="🗑️", callback_data=f"delreq:{f}"),
        ])
    kb.append([
        InlineKeyboardButton(text="➕ Папка", callback_data="action:newfolder"),
        InlineKeyboardButton(text="📋 Копировать сюда", callback_data="action:copyhere"),
    ])
    kb.append([
        InlineKeyboardButton(text="✂️ Переместить сюда", callback_data="action:movehere"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="action:refresh"),
    ])
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    text = f"📂 `{path}`\n📁 {len(folders)} папок  |  📄 {len(files)} файлов"
    if edit:
        try:
            await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown"); return
        except: pass
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("🗂️ *Файловый менеджер бот*\n/menu — открыть папку\n/settings — настройки", parse_mode="Markdown")
    await send_dir(message, message.from_user.id, WORK_DIR)

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    await send_dir(message, message.from_user.id, WORK_DIR)

@dp.message(Command("settings"))
async def cmd_settings(message: Message):
    import platform
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ℹ️ Инфо о системе", callback_data="settings:sysinfo")],
        [InlineKeyboardButton(text="🧹 Сбросить путь", callback_data="settings:clearhistory")],
    ])
    await message.answer(f"⚙️ *Настройки*\n📂 Рабочая папка: `{WORK_DIR}`", reply_markup=kb, parse_mode="Markdown")

@dp.callback_query()
async def handle_callback(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    data = callback.data

    if data.startswith("open:"):
        await send_dir(callback.message, uid, get_safe_path(uid, data[5:]), edit=True)
    elif data.startswith("nav:"):
        await send_dir(callback.message, uid, get_safe_path(uid, data[4:]), edit=True)
    elif data.startswith("file:"):
        fname = data[5:]
        fp = get_safe_path(uid, fname)
        if os.path.isfile(fp):
            try: await callback.message.answer_document(types.FSInputFile(fp), caption=f"📎 {fname}")
            except Exception as e: await callback.message.answer(f"❌ Не удалось: {e}")
        else:
            await callback.message.answer("❌ Файл не найден")
    elif data.startswith("delreq:"):
        fname = data[7:]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delconfirm:{fname}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="action:refresh")],
        ])
        await callback.message.answer(f"⚠️ Удалить `{fname}` безвозвратно?", reply_markup=kb, parse_mode="Markdown")
    elif data.startswith("delconfirm:"):
        fname = data[11:]
        cur = user_current_path.get(uid, WORK_DIR)
        fp = os.path.join(cur, fname)
        try:
            if os.path.isfile(fp): os.remove(fp)
            elif os.path.isdir(fp): shutil.rmtree(fp)
            await callback.message.answer(f"✅ Удалено: `{fname}`", parse_mode="Markdown")
        except Exception as e:
            await callback.message.answer(f"❌ Ошибка: {e}")
        await send_dir(callback.message, uid, cur)
    elif data.startswith("rename:"):
        fname = data[7:]
        await state.update_data(rename_file=fname)
        await state.set_state(FileActions.waiting_for_new_name)
        await callback.message.answer(f"✏️ Новое имя для `{fname}`:", parse_mode="Markdown")
    elif data == "action:newfolder":
        await state.set_state(FileActions.waiting_for_new_folder)
        await callback.message.answer("📁 Имя новой папки:")
    elif data == "action:copyhere":
        await state.set_state(FileActions.waiting_for_copy_path)
        await callback.message.answer("📋 Полный путь к источнику для копирования:")
    elif data == "action:movehere":
        await state.set_state(FileActions.waiting_for_move_path)
        await callback.message.answer("✂️ Полный путь к источнику для перемещения:")
    elif data == "action:refresh":
        await send_dir(callback.message, uid, user_current_path.get(uid, WORK_DIR), edit=True)
    elif data == "settings:sysinfo":
        import platform
        await callback.message.answer(f"💻 {platform.system()} {platform.release()}\n📂 `{WORK_DIR}`", parse_mode="Markdown")
    elif data == "settings:clearhistory":
        user_current_path.pop(uid, None)
        await callback.message.answer("🧹 Путь сброшен")

    await callback.answer()

@dp.message(FileActions.waiting_for_new_name)
async def process_rename(message: Message, state: FSMContext):
    d = await state.get_data()
    old, new = d.get("rename_file"), message.text.strip()
    cur = user_current_path.get(message.from_user.id, WORK_DIR)
    try:
        os.rename(os.path.join(cur, old), os.path.join(cur, new))
        await message.answer(f"✅ Переименован в `{new}`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()
    await send_dir(message, message.from_user.id, cur)

@dp.message(FileActions.waiting_for_new_folder)
async def process_new_folder(message: Message, state: FSMContext):
    name = message.text.strip()
    cur = user_current_path.get(message.from_user.id, WORK_DIR)
    try:
        os.mkdir(os.path.join(cur, name))
        await message.answer(f"✅ Папка `{name}` создана", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()
    await send_dir(message, message.from_user.id, cur)

@dp.message(FileActions.waiting_for_copy_path)
async def process_copy(message: Message, state: FSMContext):
    src = message.text.strip()
    dst = user_current_path.get(message.from_user.id, WORK_DIR)
    try:
        if os.path.isdir(src): shutil.copytree(src, os.path.join(dst, os.path.basename(src)), dirs_exist_ok=True)
        else: shutil.copy2(src, dst)
        await message.answer(f"✅ Скопировано в `{dst}`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()
    await send_dir(message, message.from_user.id, dst)

@dp.message(FileActions.waiting_for_move_path)
async def process_move(message: Message, state: FSMContext):
    src = message.text.strip()
    dst = user_current_path.get(message.from_user.id, WORK_DIR)
    try:
        shutil.move(src, dst)
        await message.answer(f"✅ Перемещено в `{dst}`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()
    await send_dir(message, message.from_user.id, dst)

@dp.message()
async def unknown(message: Message):
    await message.answer("❗ Используй кнопки или /menu")

async def main():
    print(f"🚀 Бот запущен. Рабочая папка: {WORK_DIR}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

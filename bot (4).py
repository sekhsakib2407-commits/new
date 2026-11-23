# -*- coding: utf-8 -*-
"""
SK SUPPORT VIP BOT  (Python version)

Run:
    pip install requests
    python bot.py

Notes:
  * Raw Telegram Bot API use kora hoyeche (long polling), tai premium emoji,
    button style (success/primary/danger), icon_custom_emoji_id, copy_text sob kaj korbe.
  * Data "bot_data.json" file e save hoy (user list, block list, auto message setting).
  * Bots.Business er webhook ei bot start holei remove hoye jabe. Dui jaygay ekshathe cholbe na.
"""

import json
import os
import random
import sys
import re
import string
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import requests

# =====================================================================
#  SETTINGS  (ekhane edit korba)
# =====================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "9266771423:AAFHz3cfB2unNab9IeJaJQNYMMbj-ZGjKlI"   # <-- REAL BOT TOKEN ekhane boshao

ADMINS = ["8873502591", "6645919031"]

CREATE_ACCOUNT_LINK = "https://broker-qx.pro/sign-up/?lid=1209415"
FOREX_CREATE_LINK = "https://one.exnessonelink.com/a/a16d50an4d"
LEARN_VIDEO_LINK = "https://youtu.be/lB4HnJevqes?si=hieXC4_rZCmZ6nLZ"
TUTORIAL_LINK = "https://youtube.com/@sktraderasif?si=kO_ddZ31po58mYBb"
BASIC_CLASS_LINK = "https://t.me/+tm9pPP1tJWI1NTM9"
OWNER_LINK = "https://t.me/SKTRADERASIF786"

# user jei VIP theke UID submit korbe, approve/verified korle oi VIP er link jabe
VIP_LINK = {
    "normal": "https://t.me/+RNlT0qFQjlw4ZmM5",
    "advanced": "https://t.me/+Yzhzx_cFgRIwNjUx",
    "personal": "https://t.me/+FXWfsIiqHvI2YTVh",
    "tournament": "https://t.me/+kX34Wk_rycI5NTgx",
    "forex": "https://t.me/+YMTvjr86YSQ5N2Zl",   # <-- FOREX VIP group er link
    "learn": "https://t.me/+YMTvjr86YSQ5N2Zl",
}

DATA_FILE = "bot_data.json"

# =====================================================================
#  CORE
# =====================================================================
API = "https://api.telegram.org/bot" + BOT_TOKEN + "/"


# ---------- storage ----------
class Store:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.d = {"bot": {}, "users": {}}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.d = json.load(f)
            except Exception:
                pass
        self.d.setdefault("bot", {})
        self.d.setdefault("users", {})

    def _save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.d, f, ensure_ascii=False)
        os.replace(tmp, self.path)

    def bget(self, k, default=None):
        with self.lock:
            v = self.d["bot"].get(k)
            return default if v is None else v

    def bset(self, k, v):
        with self.lock:
            self.d["bot"][k] = v
            self._save()

    def uget(self, uid, k, default=None):
        with self.lock:
            v = self.d["users"].get(str(uid), {}).get(k)
            return default if v is None else v

    def uset(self, uid, k, v):
        with self.lock:
            self.d["users"].setdefault(str(uid), {})[k] = v
            self._save()


store = Store(DATA_FILE)


# =====================================================================
#  EDITABLE LINKS  (admin panel theke bodlano jay: /admin -> ⚙️ লিংক সেটিংস)
#  Upore je link gulo ache oigulo "default". Admin panel theke bodlale
#  bot_data.json e save hoy, ar bot oi notun link-i use kore.
# =====================================================================
# key: (label, default, kind)   kind = url | video | code
LINK_ITEMS = {
    "vip_normal":     ("NORMAL VIP group", VIP_LINK["normal"], "url"),
    "vip_advanced":   ("ADVANCED VIP group", VIP_LINK["advanced"], "url"),
    "vip_personal":   ("PERSONAL VIP group", VIP_LINK["personal"], "url"),
    "vip_tournament": ("TOURNAMENT GROUP", VIP_LINK["tournament"], "url"),
    "vip_forex":      ("FOREX VIP group", VIP_LINK["forex"], "url"),
    "vip_learn":      ("TRADING CLASS group (Verified Now)", VIP_LINK["learn"], "url"),
    "basic_class":    ("TRADING BASIC CLASS group", BASIC_CLASS_LINK, "url"),
    "channel":        ("MAIN CHANNEL", "https://t.me/+smY7ym2ijiozNTY1", "url"),
    "learn_video":    ("HOW CAN I LEARN TRADING - video", LEARN_VIDEO_LINK, "video"),
    "tutorial_video": ("TUTORIAL (WATCH NOW) - video", LEARN_VIDEO_LINK, "video"),
    "vip_video":      ("VIP screen TUTORIAL VIDEO", TUTORIAL_LINK, "video"),
    "create_account": ("CREATE ACCOUNT (Quotex)", CREATE_ACCOUNT_LINK, "url"),
    "forex_create":   ("FOREX CREATE ACCOUNT (Exness)", FOREX_CREATE_LINK, "url"),
    "forex_code":     ("FOREX পার্টনার কোড", "a16d50an4d", "code"),
    "owner":          ("OWNER", OWNER_LINK, "url"),
    "youtube":        ("YOUTUBE", "https://youtube.com/@sktraderasif?si=kO_ddZ31po58mYBb", "url"),
    "facebook":       ("FACEBOOK", "https://www.facebook.com/share/v/1A5LeGfyjr/", "url"),
    "tiktok1":        ("TIKTOK 1", "https://www.tiktok.com/@sktraderasif?_r=1&_t=ZS-9BcYBvnRjxy", "url"),
    "tiktok2":        ("TIKTOK 2", "https://www.tiktok.com/@sktraderfx108?_r=1&_t=ZS-9BcmukziWKD", "url"),
}

LINK_CATS = [
    ("vip", "👥 VIP / Group link",
     ["vip_normal", "vip_advanced", "vip_personal", "vip_tournament", "vip_forex", "vip_learn", "basic_class", "channel"]),
    ("video", "🎥 Video link",
     ["learn_video", "tutorial_video", "vip_video"]),
    ("acc", "🔗 Account link ও Code",
     ["create_account", "forex_create", "forex_code"]),
    ("social", "📱 Social ও Owner",
     ["owner", "youtube", "facebook", "tiktok1", "tiktok2"]),
]


def L(key):
    """key er current link (admin bodlale notun, na bodlale default). Video bondho thakle khali ''."""
    item = LINK_ITEMS.get(key)
    if not item:
        return ""
    v = store.bget("lnk_" + key)
    if v == "-":
        return ""
    return v or item[1]


def vip_link(typ, fallback="normal"):
    return L("vip_" + str(typ)) or L("vip_" + fallback)


# ---------- telegram api ----------
def api(method, **params):
    try:
        r = requests.post(API + method, json=params, timeout=65)
        return r.json()
    except Exception as ex:
        return {"ok": False, "description": str(ex)}


def _kb(markup):
    return {"inline_keyboard": markup}


def send(chat_id, text, markup=None, html=False, **kw):
    p = {"chat_id": chat_id, "text": text}
    if html:
        p["parse_mode"] = "HTML"
    if markup:
        p["reply_markup"] = _kb(markup)
    p.update(kw)
    return api("sendMessage", **p)


def photo(chat_id, url, caption=None, markup=None, **kw):
    p = {"chat_id": chat_id, "photo": url}
    if caption:
        p["caption"] = caption
        p["parse_mode"] = "HTML"
    if markup:
        p["reply_markup"] = _kb(markup)
    p.update(kw)
    return api("sendPhoto", **p)


def copy_msg(to, from_chat, mid, markup=None):
    """returns (ok, error_description)"""
    p = {"chat_id": to, "from_chat_id": from_chat, "message_id": mid}
    if markup:
        p["reply_markup"] = _kb(markup)
    for _ in range(2):
        r = api("copyMessage", **p)
        if r.get("ok"):
            return True, ""
        if r.get("error_code") == 429:
            time.sleep(int(r.get("parameters", {}).get("retry_after", 3)) + 1)
            continue
        return False, str(r.get("description", ""))
    return False, "flood"


def is_block_err(desc):
    low = str(desc).lower()
    for w in ("blocked", "deactivated", "chat not found", "forbidden", "403"):
        if w in low:
            return True
    return False


# ---------- small helpers ----------
def e(eid, fallback):
    return '<tg-emoji emoji-id="' + eid + '">' + fallback + '</tg-emoji>'


def esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def bold(s):
    out = []
    for c in str(s):
        if "A" <= c <= "Z":
            out.append(chr(0x1D5D4 + ord(c) - 65))   # 𝗔 .. 𝗭
        else:
            out.append(c)
    return "".join(out)


def ib(text, data, style=None):
    d = {"text": text, "callback_data": data}
    if style:
        d["style"] = style
    return d


def eb(text, emoji, data, style=None):
    """callback button + premium emoji icon"""
    d = {"text": text, "callback_data": data, "icon_custom_emoji_id": emoji}
    if style:
        d["style"] = style
    return d


def ub(text, url, emoji=None, style=None):
    """url button"""
    d = {"text": text, "url": url}
    if emoji:
        d["icon_custom_emoji_id"] = emoji
    if style:
        d["style"] = style
    return d


def copy_btn(text, value, style="primary"):
    return {"text": text, "copy_text": {"text": str(value)}, "style": style}


BN = ["০", "১", "২", "৩", "৪", "৫", "৬", "৭", "৮", "৯"]


def bnum(s):
    return "".join(BN[int(c)] if c.isdigit() else c for c in str(s))


def fmt(minutes):
    h = minutes // 60
    m = minutes % 60
    if h < 4:
        per = "রাত"
    elif h < 12:
        per = "সকাল"
    elif h < 15:
        per = "দুপুর"
    elif h < 18:
        per = "বিকেল"
    elif h < 20:
        per = "সন্ধ্যা"
    else:
        per = "রাত"
    h12 = 12 if h % 12 == 0 else h % 12
    return per + " " + bnum(h12) + (":" + bnum("%02d" % m) if m else "টা")


def times_text(arr):
    return ", ".join(fmt(x) for x in arr) if arr else "কিছু নেই"


def bd_now():
    return datetime.now(timezone.utc) + timedelta(hours=6)


# ---------- user list / block ----------
def is_blocked(uid):
    return bool(store.bget("blk_" + str(uid)))


def get_users():
    return store.bget("users_list", [])


def save_user(user):
    with store.lock:
        lst = get_users()
        uid = str(user["id"])
        for it in lst:
            if it[0] == uid:
                return
        name = ((user.get("first_name") or "") + " " + (user.get("last_name") or "")).strip()
        lst.append([uid, name, user.get("username") or ""])
        store.bset("users_list", lst)


# ---------- context ----------
class Ctx:
    def __init__(self, user, chat_id, msg=None, is_cb=False):
        self.user = user
        self.uid = str(user["id"])
        self.chat_id = chat_id
        self.msg = msg
        self.is_cb = is_cb

    def get(self, k, default=None):
        return store.uget(self.uid, k, default)

    def set(self, k, v):
        store.uset(self.uid, k, v)

    def delete_old(self):
        if self.is_cb and self.msg:
            api("deleteMessage", chat_id=self.chat_id, message_id=self.msg["message_id"])

    def send(self, text, markup=None, html=False, **kw):
        return send(self.chat_id, text, markup, html, **kw)

    def photo(self, url, caption=None, markup=None, **kw):
        return photo(self.chat_id, url, caption, markup, **kw)


# =====================================================================
#  /start
# =====================================================================
def cmd_start(ctx, params):
    ctx.delete_old()
    save_user(ctx.user)
    store.bset("blk_" + ctx.uid, "")      # abar start dile block theke ber

    text = (
        e("6204263074354960916", "✨") + "━━━━━━━━━━━━━━━" + e("6204263074354960916", "✨") + "\n" +
        e("6172730949181116567", "🌐") + " <b>CHOOSE YOUR LANGUAGE</b>\n" +
        e("6204263074354960916", "✨") + "━━━━━━━━━━━━━━━" + e("6204263074354960916", "✨") + "\n\n" +
        e("5449492820568057365", "🇬🇧") + " <b>Please select your language</b>\n" +
        e("6273868559894449417", "🇧🇩") + " <b>আপনার ভাষা বেছে নিন</b>\n\n" +
        e("5231102735817918643", "👇") + " <b>Tap a button below</b>"
    )
    ctx.photo(
        "https://i.ibb.co.com/RTq00RHP/file-000000007c50820ba66ae667988dae8e.png",
        text,
        [[
            {"text": "English", "callback_data": "/menu en",
             "icon_custom_emoji_id": "5449492820568057365", "style": "primary"},
            {"text": "বাংলা", "callback_data": "/menu bn",
             "icon_custom_emoji_id": "6273868559894449417", "style": "success"},
        ]],
    )


# =====================================================================
#  /menu
# =====================================================================
def cmd_menu(ctx, params):
    ctx.delete_old()
    save_user(ctx.user)

    if params in ("en", "bn"):
        ctx.set("lang", params)
    bn = ctx.get("lang") == "bn"

    # ----- HOW CAN I LEARN TRADING -----
    if params == "learn":
        PHOTO = ""   # <-- photo link ekhane boshao (khali thakle shudhu lekha jabe)
        text = (
            e("5222444124698853913", "🔖") + " <b>TRADING কীভাবে শিখবেন?</b>\n\n" +
            e("5274080935950688944", "🏹") + " <b>TRADING শেখার জন্য CREATE ACCOUNT-এ ক্লিক করুন।</b>\n\n" +
            e("6267115986541877538", "⛓") + " <b>Account কীভাবে করবেন?</b>\n\n" +
            "<b>নিচের VIDEO-তে ক্লিক করে Account Create করার নিয়ম দেখে নিন।</b>\n\n" +
            e("6276090299232031662", "✅") + " <b>Account Create করার পর UID SUBMIT-এ ক্লিক করুন।</b>\n\n" +
            e("5190637009948944938", "👥") + " <b>এরপর আপনাকে CLASS GROUP-এ ADD করে দেওয়া হবে।</b>\n\n" +
            e("6062159640370617498", "✈️") + " <b>তারপর Step-by-Step PROPERLY TRADING শিখতে পারবেন।</b>"
        )
        kb = [
            [ub(bold("CREATE ACCOUNT"), L("create_account"), "6174602232072246502", "success"),
             eb(bold("UID SUBMIT"), "6120832956673040895", "/vip uid learn", "primary")],
        ]
        if L("learn_video"):
            kb.append([ub(bold("TUTORIAL VIDEO"), L("learn_video"), "6120724289705483505", "danger")])
        kb.append([eb(bold("BACK"), "6084901676886526521", "/menu", "danger")])
        if PHOTO:
            ctx.photo(PHOTO, text, kb)
        else:
            ctx.send(text, kb, html=True)
        return

    # ----- VIP SERVICES -----
    if params == "services":
        text = (
            "<blockquote>" +
            e("6062407228055364999", "💎") + " <b>VIP SERVICE</b>\n\n" +
            e("5357585725934029727", "❓") + " <b>কেন আমাদের VIP-তে JOIN করবেন?</b>\n\n" +
            e("6122793239876477886", "👤") + " <b>প্রতিটি Member-কে দেওয়া হয় Personal Guide & Support</b>\n\n" +
            e("5251203410396458957", "🛡") + " <b>Loss হলে 100% Refund-এর সুযোগ</b>\n\n" +
            e("6154680928212884347", "🏆") + " <b>প্রতি সপ্তাহে TOURNAMENT আয়োজন</b>\n\n" +
            e("5409048419211682843", "💵") + " <b>Balance Double Opportunity</b>\n\n" +
            e("5282950412784117735", "📈") + " <b>প্রতিদিন LIVE NON-MTG SIGNAL</b>\n" +
            e("6172660614796677391", "🔥") + " <b>তাহলে আর দেরি কেন?</b>\n\n" +
            e("6276279784599196845", "🚀") + " <b>আজই আমাদের VIP-তে JOIN করুন!</b>" +
            "</blockquote>"
        )
        ctx.photo("https://i.ibb.co.com/fGxvnfjb/1795404979993.jpg", text,
                  [[eb(bold("BACK"), "6084901676886526521", "/menu", "danger")]])
        return

    # ----- FOREX VIP -----
    if params == "forex":
        text = (
            e("6174870736247723056", "📊") + " <b>FOREX VIP</b>\n\n" +
            e("5411225014148014586", "🔴") + " <b>আমাদের FOREX VIP-তে পাচ্ছেন</b>\n\n" +
            e("6062279465663209430", "🎯") + " <b>HIGH-ACCURACY SIGNAL</b>\n\n" +
            e("6174640225352947165", "📈") + " <b>200–300 PIP পর্যন্ত Signal</b>\n" +
            e("6237550621382153460", "📅") + " <b>সপ্তাহে ৫ দিন নিয়মিত Signal দেওয়া হয়।</b>\n" +
            e("6062159640370617498", "✈️") + " <b>JOIN করতে নিচের লিংকে ক্লিক করুন</b>\n\n" +
            e("5206607081334906820", "✔️") + " <b>এরপর UID SUBMIT করুন।</b>"
        )
        ctx.photo("https://i.ibb.co.com/RnbjPrJ/1795405541419.jpg", text, [
            [ub(bold("CREATE ACCOUNT"), L("forex_create"), "6174602232072246502", "success"),
             eb(bold("UID SUBMIT"), "6120832956673040895", "/vip uid forex", "primary")],
            [copy_btn("✓ পার্টনার কোড : " + L("forex_code"), L("forex_code"), "success")],
            [eb(bold("BACK"), "6084901676886526521", "/menu", "danger")],
        ])
        return

    # ----- Main menu -----
    kb = [
        [eb(bold("আমি কিভাবে TRADING শিখতে পারি?" if bn else "HOW CAN I LEARN TRADING?"),
            "5283055978785285857", "/menu learn", "danger")],
        [eb(bold("JOIN VIP"), "6172443349581043038", "/vip", "success"),
         eb(bold("MAIN CHANNEL"), "6301084698202349045", "/channel", "primary")],
        [eb(bold("SOCIAL MEDIA"), "6172730949181116567", "/social", "primary"),
         eb(bold("VIP SERVICES"), "5222444124698853913", "/menu services", "success")],
        [eb(bold("TUTORIAL"), "6062359768666742847", "/tutorial", "danger"),
         eb(bold("FOREX VIP"), "6012529369119987828", "/menu forex", "primary")],
        [ub(bold("CONTACT OWNER"), L("owner"), "5335018876839141938", "success"),
         eb(bold("LANGUAGE"), "6172730949181116567", "/start", "primary")],
    ]
    ctx.photo("https://i.ibb.co.com/XZsMsXsN/file-0000000039c882129cdff034566b5c1b.png", None, kb)


# =====================================================================
#  /vip
# =====================================================================
def vip_buttons(typ):
    kb = [
        [ub("CREATE ACCOUNT", L("create_account"), "6174602232072246502", "success"),
         eb("UID SUBMIT", "6120832956673040895", "/vip uid " + typ, "primary")],
    ]
    if L("vip_video"):
        kb.append([ub("TUTORIAL VIDEO", L("vip_video"), "6120724289705483505", "danger")])
    kb.append([eb("BACK", "6084901676886526521", "/vip", "danger")])
    return kb


def cmd_vip(ctx, params):
    # ===== UID SUBMIT (message delete hobe na) =====
    if params.startswith("uid"):
        parts = params.split(" ")
        vip_type = parts[1] if len(parts) > 1 else ""

        # ---- FOREX VIP : UID wait korbe na, Owner er kache pathabe ----
        if vip_type == "forex":
            ftext = (
                e("6122776992015195934", "📢") + " <b>অনুগ্রহ করে উপরের ছবিটি অনুসরণ করুন।</b>\n\n" +
                e("6300926170959453705", "✅") + " <b>আপনি exness থেকে আমাদের দেওয়া লিংকের মাধ্যমে অ্যাকাউন্ট খুলে থাকলে উপরের ছবির নির্দেশনা অনুযায়ী FULLY VERIFIED করুন।</b>\n\n" +
                "<b>এরপর নিচের SUBMIT বাটনে ক্লিক করে আপনার PROFILE PHOTO OWNER কে পাঠিয়ে দিন।</b>\n\n" +
                "<b>ধন্যবাদ</b> " + e("6253254714033441566", "❤️")
            )
            ctx.photo("https://i.ibb.co.com/1YTzfJd9/Screenshot-20261123-113846.jpg", ftext,
                      [[ub("OWNER", L("owner"), "6300926170959453705", "success")]])
            return

        ctx.set("waiting_uid", vip_type)
        text = (
            e("6123201184460185867", "📣") + " <b>জরুরি নির্দেশনা</b>\n\n" +
            e("6174769598357836625", "⚠️") + " <b>নামের আগে SK VIP না থাকলে Join Request গ্রহণ করা হবে না।</b>\n\n" +
            e("6276090299232031662", "✅") + " <b>Example :</b> <code>SK SAKIB VIP</code>\n\n" +
            "<blockquote>" + e("5348373562249980047", "❤️") + " <b>কোনো সমস্যা হলে Personally Message করুন।</b></blockquote>\n" +
            e("6062271116246785577", "📌") + " <b>ওপরের স্কিনসট অনুসরণ করে অথবা Profile থেকে আপনার UID Copy করুন।</b>\n\n" +
            e("6172607709389526352", "✉️") + " <b>এখানে আপনার UID Send করুন</b>\n\n" +
            e("5399850755337240950", "⏳") + " <b>WAITING FOR YOUR UID...</b>"
        )
        ctx.photo("https://i.ibb.co.com/8nbxBmHP/IMG-20261122-235201-765.jpg", text)
        return

    ctx.delete_old()

    # ===== NORMAL VIP =====
    if params == "normal":
        text = (
            e("6291653658689937558", "📊") + " <b>NORMAL VIP</b>\n\n" +
            "<b>মাত্র 30$ Deposit করে</b>\n\n" +
            "<b>সহজেই VIP-তে JOIN করতে পারবেন।</b>\n" +
            e("5244837092042750681", "📈") + " <b>প্রতিদিন LIVE NON-MTG SIGNAL</b>\n\n" +
            e("5274080935950688944", "🏹") + " <b>ছোট Amount কে Double করার সুযোগ</b>\n\n" +
            e("6276090299232031662", "✅") + " <b>নিচের লিংক থেকে নতুন ACCOUNT করে UID SUBMIT এ ক্লিক করুন</b>"
        )
        ctx.photo("https://i.ibb.co.com/Q1DYkGK/1795363168171.jpg", text, vip_buttons("normal"))
        return

    # ===== ADVANCED VIP =====
    if params == "advanced":
        text = (
            e("6061894189916889620", "📊") + " <b>ADVANCED VIP</b>\n\n" +
            e("6172449173556695219", "💵") + " <b>মাত্র $150 Deposit করলেই ADVANCED VIP-তে JOIN!</b>\n\n" +
            e("5244837092042750681", "📈") + " <b>যেখানে প্রতিদিন LIVE HIGH-ACCURACY NON-MTG SIGNAL</b>\n\n" +
            e("6062307249806646997", "🛡") + " <b>Loss হলে 100% Refund-এর সুযোগ</b>\n\n" +
            e("6172443349581043038", "🔥") + " <b>তাহলে আর দেরি কিসের?</b>\n\n" +
            e("6300926170959453705", "✅") + " <b>নিচের লিংক থেকে NEW ACCOUNT করুন</b>\n" +
            e("6120832956673040895", "🛫") + " <b>UID SUBMIT-এ ক্লিক করুন</b>"
        )
        ctx.photo("https://i.ibb.co.com/0jfLtcHM/1795364082609.jpg", text, vip_buttons("advanced"))
        return

    # ===== PERSONAL VIP =====
    if params == "personal":
        text = (
            e("6172613073803678489", "💎") + " <b>PERSONAL VIP</b>\n\n" +
            e("6122702482922546607", "💰") + " <b>মাত্র $500–$1,000 Deposit করেই</b>\n\n" +
            "<b>PERSONAL VIP-তে JOIN করুন।</b>\n\n" +
            e("5244837092042750681", "📈") + " <b>আপনার Trading জীবন এরন সব Loss Recovery + Profit- 100%</b>\n\n" +
            e("6062307249806646997", "🛡") + " <b>Loss হলে 100% Refund-এর সুযোগ</b>\n" +
            e("6276090299232031662", "✅") + " <b>তো আর দেরি কেন?</b>\n\n" +
            e("6174602232072246502", "🔗") + " <b>নিচের CREATE ACCOUNT-এ ক্লিক করে</b>\n" +
            e("6120832956673040895", "🛫") + " <b>UID SUBMIT-এ ক্লিক করুন।</b>"
        )
        ctx.photo("https://i.ibb.co.com/wN2F4Bdt/1795365227020.jpg", text, vip_buttons("personal"))
        return

    # ===== TOURNAMENT GROUP =====
    if params == "tournament":
        text = (
            e("6062358205298648147", "🏆") + " <b>TOURNAMENT GROUP</b>\n\n" +
            e("6172443349581043038", "🔥") + " <b>প্রতি সপ্তাহে TOURNAMENT আয়োজন করা হয়</b>\n\n" +
            e("6174548278693073988", "💰") + " <b>$50 → $200</b>\n\n" +
            e("6174548278693073988", "💰") + " <b>$100 → $500 — Risk-Free সুযোগ</b>\n" +
            e("6172449173556695219", "💵") + " <b>Minimum $50 Deposit করে</b>\n\n" +
            e("6120832956673040895", "🛫") + " <b>নিচের UID-তে SUBMIT করুন।</b>"
        )
        ctx.photo("https://i.ibb.co.com/wFg1qrTg/1795368594801.jpg", text, vip_buttons("tournament"))
        return

    # ===== TRADING BASIC CLASS =====
    if params == "basic":
        text = (
            e("5312508296110813938", "📚") + " <b>TRADING BASIC CLASS</b>\n\n" +
            "<b>আপনি TRADING-এ নতুন হন অথবা পুরোনো,</b>\n\n" +
            "<b>নিচের লিংকে JOIN করুন।</b> " + e("6122996348879904468", "👇") + "\n" +
            e("5222444124698853913", "🔖") + " <b>এখানে TRADING BASIC থেকে</b>\n\n" +
            e("5244837092042750681", "📈") + " <b>নতুন নতুন STRATEGY শেখানো হয়।</b>\n" +
            e("6172443349581043038", "🔥") + " <b>শিখুন • বুঝুন • তারপর TRADE করুন</b>"
        )
        ctx.photo("https://i.ibb.co.com/cSGLnz1x/1795369388830.jpg", text, [
            [ub("JOIN NOW", L("basic_class"), "6300926170959453705", "success")],
            [eb("BACK", "6084901676886526521", "/vip", "danger")],
        ])
        return

    # ===== VIP list =====
    kb = [
        [eb("NORMAL VIP", "5071491301443110142", "/vip normal", "primary")],
        [eb("ADVANCED VIP", "6174640225352947165", "/vip advanced", "success")],
        [eb("PERSONAL VIP", "6174550374637114687", "/vip personal", "danger")],
        [eb("TOURNAMENT GROUP", "6174659690144731736", "/vip tournament", "success")],
        [eb("TRADING BASIC CLASS", "5283055978785285857", "/vip basic", "primary")],
        [eb("BACK", "6084901676886526521", "/menu", "danger")],
    ]
    ctx.photo("https://i.ibb.co.com/kgm2S4h5/1795360290662.jpg", None, kb)


# =====================================================================
#  /channel  /social  /tutorial
# =====================================================================
def cmd_channel(ctx, params):
    ctx.delete_old()
    ctx.photo("https://i.ibb.co.com/V0MbqKB7/1795361158548.jpg", None, [
        [ub("JOIN NOW", L("channel"), "5332355889741442089", "success")],
        [eb("BACK", "6084901676886526521", "/menu", "danger")],
    ])


def cmd_social(ctx, params):
    ctx.delete_old()
    ctx.photo("https://i.ibb.co.com/TM1g1nLN/1795361782673.jpg", None, [
        [ub("YOUTUBE", L("youtube"), "5341357385279612709", "danger")],
        [ub("FACEBOOK", L("facebook"), "6138685684023562338", "primary")],
        [ub("TIKTOK 1", L("tiktok1"), "6131898226946607046", "success"),
         ub("TIKTOK 2", L("tiktok2"), "6131898226946607046", "success")],
        [eb("BACK", "6084901676886526521", "/menu", "danger")],
    ])


def cmd_tutorial(ctx, params):
    ctx.delete_old()
    text = (
        e("5312508296110813938", "📚") + " <b>কীভাবে সঠিক নিয়মে একটি QUOTEX ACCOUNT করবেন এবং VIP-তে JOIN করবেন?</b>\n\n" +
        e("6062359768666742847", "🎥") + " <b>নিচের VIDEO-তে CLICK করে খুব সহজেই পুরো প্রক্রিয়াটি দেখে নিন।</b>\n\n" +
        e("6122793239876477886", "⚠️") + " <b>VIDEO-টি সম্পূর্ণ দেখবেন, যাতে কোনো ধাপ মিস না হয়।</b>\n\n" +
        e("6255692391441763151", "👤") + " <b>আপনি নতুন হন বা পুরাতন, সবার জন্যই এই TUTORIALটি গুরুত্বপূর্ণ।</b> ❤️"
    )
    kb = []
    if L("tutorial_video"):
        kb.append([ub("WATCH NOW", L("tutorial_video"), "5334885900356688822", "success")])
    kb.append([eb("BACK", "6084901676886526521", "/menu", "danger")])
    ctx.photo("https://i.ibb.co.com/whW7Mfnt/1795375267981.jpg", text, kb)


# =====================================================================
#  BROADCAST / AUTO MESSAGE  (background)
# =====================================================================
def broadcast(from_chat, mid, markup=None, notify=None):
    def run():
        ok_c = 0
        blk_c = 0
        for it in list(get_users()):
            uid = it[0]
            if is_blocked(uid):
                continue
            ok, err = copy_msg(uid, from_chat, mid, markup)
            if ok:
                ok_c += 1
            elif is_block_err(err):
                store.bset("blk_" + uid, "1")
                blk_c += 1
            time.sleep(0.05)
        if notify:
            send(notify, "✅ ব্রডকাস্ট শেষ।\n\n📨 সফল: " + str(ok_c) + "\n🚫 ব্লক/ব্যর্থ: " + str(blk_c))
    threading.Thread(target=run, daemon=True).start()


def markup_from(btns):
    out = []
    for b in btns:
        o = {"text": b["text"], "url": b["url"]}
        if b.get("emoji"):
            o["icon_custom_emoji_id"] = b["emoji"]
        if b.get("color"):
            o["style"] = b["color"]
        out.append([o])
    return out


def scheduler():
    """auto message: protidin set kora somoy e shobaike pathay (Bangladesh time)"""
    while True:
        try:
            cfg = store.bget("auto_cfg")
            if cfg and cfg.get("on"):
                now = bd_now()
                cur = now.hour * 60 + now.minute
                today = now.strftime("%Y-%m-%d")
                last = store.bget("auto_last", [])
                for t in cfg.get("times", []):
                    key = today + "-" + str(t)
                    if t <= cur < t + 10 and key not in last:
                        last.append(key)
                        store.bset("auto_last", last[-30:])
                        btns = cfg.get("btns") or []
                        broadcast(cfg["draft"]["chat"], cfg["draft"]["msg"],
                                  markup_from(btns) if btns else None)
                        for a in ADMINS:
                            send(a, "📢 অটো মেসেজ সবার কাছে পাঠানো শুরু হয়েছে।")
        except Exception:
            traceback.print_exc()
        time.sleep(20)


# =====================================================================
#  /admin
# =====================================================================
def show_panel(ctx):
    users = get_users()
    blocked = sum(1 for u in users if is_blocked(u[0]))
    ctx.send(
        "🛠 <b>অ্যাডমিন প্যানেল</b>\n\n" +
        "👥 মোট ইউজার: <b>" + str(len(users)) + "</b>\n" +
        "✅ অ্যাক্টিভ: <b>" + str(len(users) - blocked) + "</b>\n" +
        "🚫 বট ব্লক করেছে: <b>" + str(blocked) + "</b>\n\n" +
        "📨 ব্রডকাস্ট মেসেজ যারা বটে স্টার্ট দিয়েছে তাদের সবার কাছে যাবে।",
        [
            [ib("📨 সবাইকে মেসেজ পাঠাও", "/admin send", "primary")],
            [ib("⏰ অটো মেসেজ", "/admin auto", "success")],
            [ib("⚙️ লিংক সেটিংস", "/admin links", "primary")],
            [ib("✉️ একজনকে মেসেজ (ID দিয়ে)", "/admin dm", "success")],
            [ib("👥 ইউজার লিস্ট", "/admin users 0", "primary"),
             ib("🚫 ব্লক লিস্ট", "/admin blocked 0", "danger")],
            [ib("🔄 রিফ্রেশ", "/admin panel", "success")],
        ], html=True)


def show_times(ctx):
    n = int(ctx.get("auto_n", 1))
    sel = ctx.get("auto_times", [])
    PRESETS = [480, 720, 960, 1200, 1320]
    kb = []
    row = []
    for m in PRESETS:
        on = m in sel
        row.append(ib(("✅ " if on else "") + fmt(m), "/admin autot " + str(m), "success" if on else "primary"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([ib("✏️ নিজে টাইম লিখব", "/admin autotype", "primary")])
    if len(sel) == n:
        kb.append([ib("➡️ পরের ধাপ", "/admin autopost", "success")])
    kb.append([ib("🔙 পেছনে", "/admin auto", "danger")])
    ctx.send(
        "⏰ <b>অটো মেসেজ</b>\n\n" +
        "দিনে <b>" + bnum(n) + "</b> বার পাঠানো হবে।\n" +
        "নিচ থেকে <b>" + bnum(n) + "</b> টা সময় বেছে নাও, অথবা নিজে লিখে দাও।\n\n" +
        "🕒 বাছা হয়েছে (" + bnum(len(sel)) + "/" + bnum(n) + "): <b>" + times_text(sel) + "</b>",
        kb, html=True)


def show_color(ctx):
    ctx.send("🎨 Button এর color বেছে নাও:", [
        [ib("🔵 নীল", "/admin autobcol primary", "primary"), ib("🟢 সবুজ", "/admin autobcol success", "success")],
        [ib("🔴 লাল", "/admin autobcol danger", "danger"), ib("⚪ ডিফল্ট", "/admin autobcol none", "primary")],
        [ib("❌ বাতিল", "/admin cancel", "danger")],
    ])


def link_cat_of(key):
    for cid, title, keys in LINK_CATS:
        if key in keys:
            return cid
    return "vip"


def link_state(key):
    if store.bget("lnk_" + key) == "-":
        return "🚫 বাটন বন্ধ"
    return L(key) or "—"


def show_links_home(ctx):
    rows = [[ib(title, "/admin lnks " + cid, "primary")] for cid, title, keys in LINK_CATS]
    rows.append([ib("🔙 প্যানেল", "/admin panel", "danger")])
    ctx.send("⚙️ <b>লিংক সেটিংস</b>\n\nকোন ধরনের লিংক বদলাবে? ⬇️\n\n"
             "এখানে যা বদলাবে সেটাই বটের সব জায়গায় সঙ্গে সঙ্গে কাজ করবে।", rows, html=True)


def show_links_cat(ctx, cid):
    cat = None
    for c in LINK_CATS:
        if c[0] == cid:
            cat = c
    if not cat:
        show_links_home(ctx)
        return
    lines = []
    rows = []
    for key in cat[2]:
        label = LINK_ITEMS[key][0]
        lines.append("• <b>" + esc(label) + "</b>\n   <code>" + esc(link_state(key)) + "</code>")
        rows.append([ib("✏️ " + label, "/admin lnk " + key, "success")])
    rows.append([ib("🔙 পেছনে", "/admin links", "danger")])
    ctx.send(cat[1] + "\n\n" + "\n\n".join(lines) + "\n\nযেটা বদলাতে চাও সেটার বাটনে চাপো।", rows, html=True)


def show_link_item(ctx, key):
    item = LINK_ITEMS.get(key)
    if not item:
        show_links_home(ctx)
        return
    label, default, kind = item
    ctx.set("admin_mode", "set_link")
    ctx.set("link_key", key)
    rows = []
    if kind == "video":
        rows.append([ib("🗑 বাটন বন্ধ করো (লুকাও)", "/admin lnkoff " + key, "danger")])
    rows.append([ib("♻️ ডিফল্টে ফিরাও", "/admin lnkreset " + key, "primary")])
    rows.append([ib("🔙 পেছনে", "/admin lnks " + link_cat_of(key), "danger")])
    what = "কোড" if kind == "code" else "লিংক"
    ctx.send("✏️ <b>" + esc(label) + "</b>\n\n"
             "এখনকার: <code>" + esc(link_state(key)) + "</code>\n\n"
             "👇 নতুন " + what + " এখানে পাঠাও।", rows, html=True)


CANCEL_KB = [[ib("❌ বাতিল", "/admin cancel", "danger")]]


def cmd_admin(ctx, params):
    if ctx.uid not in ADMINS:
        return

    p = params.strip().split(" ")
    action = p[0] if len(p) > 0 else ""
    target = p[1] if len(p) > 1 else None
    typ = p[2] if len(p) > 2 else None
    sid = p[3] if len(p) > 3 else None

    # ===== প্যানেল =====
    if action in ("", "panel"):
        ctx.delete_old()
        ctx.set("admin_mode", "")
        show_panel(ctx)
        return

    # ===== অটো মেসেজ: প্রথম স্ক্রিন =====
    if action == "auto":
        ctx.delete_old()
        ctx.set("admin_mode", "")
        cfg = store.bget("auto_cfg")
        status = "এখনো সেট করা নেই।"
        if cfg:
            status = (("🟢 <b>চালু আছে</b>" if cfg.get("on") else "🔴 <b>বন্ধ আছে</b>") +
                      "\n🕒 সময়: <b>" + times_text(cfg.get("times", [])) + "</b>" +
                      "\n🔘 Button: <b>" + bnum(len(cfg.get("btns") or [])) + "</b> টা")
        kb = [[ib(str(i), "/admin autocnt " + str(i), "primary") for i in range(1, 6)]]
        if cfg:
            kb.append([ib("⏸ বন্ধ করো", "/admin autooff", "danger") if cfg.get("on")
                       else ib("▶️ চালু করো", "/admin autoon", "success")])
        kb.append([ib("🔙 প্যানেল", "/admin panel", "danger")])
        ctx.send("⏰ <b>অটো মেসেজ</b>\n\n" + status + "\n\n" +
                 "নতুন করে সেট করতে বেছে নাও, দিনে কতবার সবার কাছে মেসেজ যাবে? ⬇️", kb, html=True)
        return

    if action == "autocnt":
        ctx.delete_old()
        try:
            n = min(5, max(1, int(target)))
        except Exception:
            n = 1
        ctx.set("auto_n", n)
        ctx.set("auto_times", [])
        show_times(ctx)
        return

    if action == "autot":
        ctx.delete_old()
        n = int(ctx.get("auto_n", 1))
        sel = ctx.get("auto_times", [])
        try:
            m = int(target)
        except Exception:
            m = None
        if m is not None:
            if m in sel:
                sel.remove(m)
            elif len(sel) < n:
                sel.append(m)
                sel.sort()
        ctx.set("auto_times", sel)
        show_times(ctx)
        return

    if action == "autotype":
        ctx.delete_old()
        n = int(ctx.get("auto_n", 1))
        ctx.set("admin_mode", "auto_times")
        ctx.send(
            "✏️ <b>" + bnum(n) + "</b> টা সময় লিখে পাঠাও (২৪ ঘণ্টার হিসাবে, স্পেস দিয়ে)।\n\n" +
            "যেমন: <code>10 11</code>\n" +
            "মিনিটসহ: <code>9:30 14 22</code>\n\n" +
            "মনে রেখো: রাত ১০টা = <code>22</code>",
            [[ib("🔙 পেছনে", "/admin autocnt " + str(n), "danger")]], html=True)
        return

    if action == "autopost":
        ctx.delete_old()
        n = int(ctx.get("auto_n", 1))
        if len(ctx.get("auto_times", [])) != n:
            show_times(ctx)
            return
        ctx.set("admin_mode", "auto_msg")
        ctx.send("✍️ যে মেসেজটা অটো পাঠাতে চাও সেটা এখানে পাঠাও (টেক্সট, ছবি, ভিডিও, যেকোনো কিছু)।\n\n"
                 "⚠️ পাঠানো মেসেজটা এই চ্যাট থেকে ডিলিট করো না, ডিলিট করলে অটো মেসেজ যাবে না।", CANCEL_KB)
        return

    if action == "autobadd":
        ctx.delete_old()
        ctx.set("admin_mode", "ab_text")
        ctx.send("✍️ Button এ কী লেখা থাকবে? লেখাটা পাঠাও।", CANCEL_KB)
        return

    if action == "autobskip":
        ctx.delete_old()
        cur = ctx.get("ab_cur", {})
        cur["emoji"] = ""
        ctx.set("ab_cur", cur)
        ctx.set("admin_mode", "")
        show_color(ctx)
        return

    if action == "autobcol":
        ctx.delete_old()
        cur = ctx.get("ab_cur", {})
        cur["color"] = "" if target == "none" else target
        ctx.set("ab_cur", cur)
        ctx.set("admin_mode", "ab_url")
        ctx.send("🔗 Button এর link পাঠাও (https://... বা t.me/...)", CANCEL_KB)
        return

    if action == "autosave":
        ctx.delete_old()
        draft = ctx.get("auto_draft")
        times = ctx.get("auto_times", [])
        if not draft or not times:
            ctx.send("সেটআপ অসম্পূর্ণ। /admin দিয়ে আবার চেষ্টা করো।")
            return
        cfg = {"on": True, "times": times, "draft": draft, "btns": ctx.get("auto_btns", [])}
        store.bset("auto_cfg", cfg)
        store.bset("auto_last", [])
        ctx.set("admin_mode", "")
        ctx.send(
            "✅ <b>অটো মেসেজ চালু হয়েছে!</b>\n\n" +
            "🕒 প্রতিদিন পাঠানো হবে: <b>" + times_text(times) + "</b>\n" +
            "🔘 Button: <b>" + bnum(len(cfg["btns"])) + "</b> টা\n\n" +
            "ঐ সময়ে বটে যারা স্টার্ট দিয়েছে সবার কাছে যাবে (বাংলাদেশ সময়)।",
            [[ib("🔙 প্যানেল", "/admin panel", "primary")]], html=True)
        return

    if action in ("autooff", "autoon"):
        ctx.delete_old()
        cfg = store.bget("auto_cfg")
        if not cfg:
            show_panel(ctx)
            return
        cfg["on"] = (action == "autoon")
        store.bset("auto_cfg", cfg)
        ctx.send("▶️ অটো মেসেজ আবার চালু হয়েছে।" if cfg["on"] else "⏸ অটো মেসেজ বন্ধ করা হয়েছে।",
                 [[ib("🔙 অটো মেসেজ", "/admin auto", "primary")]])
        return

    # ===== ইউজার লিস্ট / ব্লক লিস্ট =====
    if action in ("users", "blocked"):
        ctx.delete_old()
        only_blocked = (action == "blocked")
        try:
            page = int(target)
        except Exception:
            page = 0
        size = 10
        lst = [u for u in get_users() if (not only_blocked or is_blocked(u[0]))]
        total = len(lst)
        lines = []
        kb = []
        for i in range(page * size, min(total, (page + 1) * size)):
            u = lst[i]
            blk = " 🚫" if is_blocked(u[0]) else ""
            nm = esc(u[1]) or "নাম নেই"
            un = " (@" + esc(u[2]) + ")" if u[2] else ""
            lines.append(str(i + 1) + ". " + nm + un + blk + "\n    🆔 <code>" + u[0] + "</code>")
            short = str(u[1] or u[0])[:18]
            kb.append([copy_btn("📋 " + short, u[0], "primary"),
                       ib("✉️ মেসেজ", "/admin dm " + u[0], "success")])
        nav = []
        if page > 0:
            nav.append(ib("⬅️ আগের", "/admin " + action + " " + str(page - 1), "primary"))
        if (page + 1) * size < total:
            nav.append(ib("পরের ➡️", "/admin " + action + " " + str(page + 1), "primary"))
        if nav:
            kb.append(nav)
        kb.append([ib("🔙 প্যানেল", "/admin panel", "danger")])
        title = "🚫 <b>ব্লক লিস্ট</b>" if only_blocked else "👥 <b>ইউজার লিস্ট</b>"
        ctx.send(title + " (মোট " + str(total) + " জন)\n\n" +
                 ("\n".join(lines) if lines else "কেউ নেই।") +
                 "\n\n📋 বাটনে চাপলে ID কপি হবে, ✉️ চাপলে ওই ইউজারকে মেসেজ পাঠানো যাবে।", kb, html=True)
        return

    # ===== একজনকে মেসেজ =====
    if action == "dm":
        ctx.delete_old()
        if target:
            ctx.set("dm_target", str(target))
            ctx.set("admin_mode", "dm_msg")
            ctx.send("✉️ ইউজার <code>" + esc(target) + "</code> কে যে মেসেজটা পাঠাতে চাও সেটা এখানে পাঠাও (টেক্সট, ছবি, ভিডিও, যেকোনো কিছু)।",
                     CANCEL_KB, html=True)
        else:
            ctx.set("admin_mode", "dm_id")
            ctx.send("🆔 যাকে মেসেজ পাঠাতে চাও তার ইউজার ID পাঠাও।", CANCEL_KB)
        return

    # ===== ব্রডকাস্ট =====
    if action == "send":
        ctx.delete_old()
        ctx.set("admin_mode", "bc_msg")
        ctx.send("✍️ এখন যে মেসেজটা সবাইকে পাঠাতে চাও সেটা এখানে পাঠাও (টেক্সট, ছবি, ভিডিও, যেকোনো কিছু)।", CANCEL_KB)
        return

    if action == "cancel":
        ctx.delete_old()
        ctx.set("admin_mode", "")
        ctx.set("bc_draft", None)
        ctx.set("dm_target", "")
        ctx.set("link_key", "")
        show_panel(ctx)
        return

    if action == "confirm":
        d = ctx.get("bc_draft")
        if not d:
            ctx.delete_old()
            ctx.send("ড্রাফট পাওয়া যায়নি। /admin দিয়ে আবার চেষ্টা করো।")
            return
        ctx.set("bc_draft", None)
        broadcast(d["chat"], d["msg"], None, notify=ctx.chat_id)
        ctx.delete_old()
        ctx.send("⏳ সবাইকে পাঠানো শুরু হয়েছে।\n\nশেষ হলে এখানে জানিয়ে দেবো। প্যানেলে 🔄 রিফ্রেশ চাপলে কতজন ব্লক করেছে সেটাও দেখতে পাবে।",
                 [[ib("🔙 প্যানেল", "/admin panel", "primary")]])
        return

    # ===== ⚙️ লিংক সেটিংস =====
    if action == "links":
        ctx.delete_old()
        ctx.set("admin_mode", "")
        show_links_home(ctx)
        return

    if action == "lnks":
        ctx.delete_old()
        ctx.set("admin_mode", "")
        show_links_cat(ctx, target or "")
        return

    if action == "lnk":
        ctx.delete_old()
        show_link_item(ctx, target or "")
        return

    if action in ("lnkreset", "lnkoff"):
        ctx.delete_old()
        ctx.set("admin_mode", "")
        item = LINK_ITEMS.get(target or "")
        if not item:
            show_links_home(ctx)
            return
        if action == "lnkoff" and item[2] == "video":
            store.bset("lnk_" + target, "-")
            msg = "🗑 <b>" + esc(item[0]) + "</b> এর বাটন এখন বটে দেখাবে না।"
        else:
            store.bset("lnk_" + target, "")
            msg = "♻️ <b>" + esc(item[0]) + "</b> ডিফল্ট লিংকে ফিরেছে:\n<code>" + esc(item[1]) + "</code>"
        ctx.send(msg, [
            [ib("✏️ আরেকটা বদলাও", "/admin lnks " + link_cat_of(target), "primary")],
            [ib("🔙 প্যানেল", "/admin panel", "danger")],
        ], html=True)
        return

    # ===== UID: APPROVE / REJECT / DP / VERIFIED =====
    if action == "done" or not target:
        return

    st = None
    if sid:
        st = store.bget("s_" + sid)
        if st and st.get("by"):
            ctx.send("ℹ️ এই UID আগেই হ্যান্ডেল করা হয়েছে (" + st["by"] + ")।")
            return
    admin_name = str(ctx.user.get("first_name") or "Admin")
    if st:
        st["by"] = admin_name
        store.bset("s_" + sid, st)

    status = ""

    # ----- APPROVE : notun message + photo -----
    if action == "approve":
        text = (
            e("6253780692908378898", "✅") + " <b>Alhamdulillah, আপনার UID Verified হয়েছে।</b>\n\n" +
            e("5231102735817918643", "👇") + e("5231102735817918643", "👇") +
            " <b>এখন অনুগ্রহ করে নিচের JOIN বাটনে ক্লিক করে JOIN করুন।</b> " +
            e("6276279784599196845", "🚀")
        )
        photo(target, "https://i.ibb.co.com/zWStMLZD/1795409950919.jpg", text,
              [[ub("JOIN NOW", vip_link(typ, "normal"), "6300926170959453705", "success")]])
        status = "✅ অনুমোদিত"

    # ----- REJECT : ager message + upore photo -----
    if action == "reject":
        text = (
            e("6111390866209775225", "😐") + " <b>UID ভেরিফাই হয়নি!</b>\n\n" +
            e("6172385702529996210", "⚠️") + " <b>আপনি আমাদের লিংক থেকে অ্যাকাউন্ট খুলেননি।</b>\n\n" +
            e("6061927682071863597", "🔗") + " <b>নিচের লিংকে ক্লিক করে সঠিকভাবে অ্যাকাউন্ট খুলুন।</b>\n\n" +
            e("6253749674654566975", "⭐") + " <b>অ্যাকাউন্ট খোলার পর আপনার UID এখানে Submit করুন।</b>\n\n" +
            e("6300926170959453705", "✅") + " <b>সবকিছু ঠিক থাকলে সাথে সাথেই VIP-তে প্রবেশ করতে পারবেন।</b>"
        )
        photo(target, "https://i.ibb.co.com/Wv43QKMT/1795410371159.jpg", text, [[
            ub("CREATE ACCOUNT", L("forex_create") if typ == "forex" else L("create_account"),
               "6174602232072246502", "success"),
            eb("UID CHECK", "6120832956673040895", "/vip uid " + str(typ), "primary"),
        ]])
        status = "❌ রিজেক্ট"

    # ----- DP -----
    if action == "dp":
        text = (
            e("5357584845465730934", "🌸") + " <b>প্রিয় ভাই, আপনার ACCOUNT সফলভাবে তৈরি করা হয়েছে।</b>\n\n" +
            e("5409048419211682843", "💵") + " <b>অনুগ্রহ করে DEPOSIT সম্পন্ন করুন এবং DEPOSIT করার পর আপনার UID আবার SUBMIT করুন।</b>"
        )
        send(target, text, [[eb("UID SUBMIT", "6120832956673040895", "/vip uid " + str(typ), "primary")]], html=True)
        status = "💵 ডিপোজিট মেসেজ পাঠানো হয়েছে"

    # ----- VERIFIED NOW (trading class) -----
    if action == "verified":
        text = (
            e("6280469078519845663", "✅") + " <b>Alhamdulillah, আপনার Account Full Complete হয়েছে।</b>\n\n" +
            e("6122996348879904468", "👇") + " <b>অনুগ্রহ করে নিচের JOIN বাটনে ক্লিক করে Join করুন এবং</b>\n\n" +
            e("5222444124698853913", "🔖") + " <b>Properভাবে Trading শিখুন।</b>"
        )
        send(target, text, [[ub("JOIN NOW", vip_link(typ, "learn"), "6300926170959453705", "success")]], html=True)
        status = "🗝 ভেরিফাই, লিংক পাঠানো হয়েছে"

    # ----- admin er message e status + COPY UID -----
    try:
        rows = []
        if st and st.get("uid"):
            rows.append([copy_btn("COPY UID", st["uid"], "primary")])
        rows.append([{"text": status + " — " + admin_name, "callback_data": "/admin done"}])
        api("editMessageReplyMarkup", chat_id=ctx.chat_id, message_id=ctx.msg["message_id"],
            reply_markup=_kb(rows))
    except Exception:
        pass


# =====================================================================
#  NORMAL MESSAGE  (admin mode  +  UID capture)
# =====================================================================
def send_auto_menu(ctx, head):
    draft = ctx.get("auto_draft")
    btns = ctx.get("auto_btns", [])
    if draft:
        copy_msg(ctx.chat_id, draft["chat"], draft["msg"], markup_from(btns) if btns else None)
    ctx.send(head + "\n\n🔘 এখনকার Button: " + bnum(len(btns)) + " টা", [
        [ib("➕ Button যোগ করো", "/admin autobadd", "primary")],
        [ib("✅ সেভ করো ও চালু করো", "/admin autosave", "success")],
        [ib("❌ বাতিল", "/admin cancel", "danger")],
    ])


def on_message(ctx, m):
    is_admin = ctx.uid in ADMINS
    mode = ctx.get("admin_mode") if is_admin else ""
    txt = (m.get("text") or "").strip()
    mid = m["message_id"]
    cid = ctx.chat_id

    if mode:
        # --- ⚙️ লিংক সেটিংস: নতুন লিংক/কোড সেভ ---
        if mode == "set_link":
            key = ctx.get("link_key")
            item = LINK_ITEMS.get(key)
            if not item:
                ctx.set("admin_mode", "")
                ctx.send("কিছু একটা গোলমাল হয়েছে। /admin দিয়ে আবার চেষ্টা করো।")
                return
            v = txt
            if item[2] == "code":
                if not re.match(r"^[0-9A-Za-z_-]{3,40}$", v):
                    ctx.send("⚠️ কোডটা ঠিক না (৩-৪০ অক্ষর, শুধু ইংরেজি অক্ষর/সংখ্যা)। আবার পাঠাও।", [
                        [ib("🔙 পেছনে", "/admin lnks " + link_cat_of(key), "danger")]])
                    return
            else:
                if re.match(r"^(t\.me|telegram\.me)/\S+$", v):
                    v = "https://" + v
                if not re.match(r"^https?://\S+$", v):
                    ctx.send("⚠️ লিংকটা ঠিক না। https://... বা t.me/... দিয়ে পাঠাও।", [
                        [ib("🔙 পেছনে", "/admin lnks " + link_cat_of(key), "danger")]])
                    return
            store.bset("lnk_" + key, v)
            ctx.set("admin_mode", "")
            ctx.send("✅ <b>" + esc(item[0]) + "</b> সেভ হয়েছে:\n<code>" + esc(v) + "</code>\n\n"
                     "এখন থেকে বটের সব জায়গায় এটাই কাজ করবে।", [
                [ib("✏️ আরেকটা বদলাও", "/admin lnks " + link_cat_of(key), "primary")],
                [ib("🔙 প্যানেল", "/admin panel", "danger")],
            ], html=True)
            return

        # --- সবাইকে মেসেজ: প্রিভিউ ---
        if mode == "bc_msg":
            ctx.set("bc_draft", {"chat": cid, "msg": mid})
            ctx.set("admin_mode", "")
            copy_msg(cid, cid, mid)
            ctx.send("👆 এটাই প্রিভিউ। সবাইকে পাঠাবো?", [
                [ib("✅ হ্যাঁ, সবাইকে পাঠাও", "/admin confirm", "success")],
                [ib("❌ বাতিল", "/admin cancel", "danger")],
            ])
            return

        # --- একজনকে মেসেজ: ID নেওয়া ---
        if mode == "dm_id":
            if not re.match(r"^\d{5,15}$", txt):
                ctx.send("⚠️ সঠিক ইউজার ID পাঠাও (শুধু সংখ্যা)।", CANCEL_KB)
                return
            ctx.set("dm_target", txt)
            ctx.set("admin_mode", "dm_msg")
            ctx.send("✉️ এবার যে মেসেজটা পাঠাতে চাও সেটা এখানে পাঠাও (টেক্সট, ছবি, ভিডিও, যেকোনো কিছু)।", CANCEL_KB)
            return

        # --- একজনকে মেসেজ: পাঠানো ---
        if mode == "dm_msg":
            t = ctx.get("dm_target")
            if not t:
                ctx.set("admin_mode", "")
                ctx.send("ইউজার ID পাওয়া যায়নি। /admin দিয়ে আবার চেষ্টা করো।")
                return
            ok, err = copy_msg(t, cid, mid)
            ctx.set("admin_mode", "")
            if ok:
                head = "✅ মেসেজ পাঠানো হয়েছে: <code>" + esc(t) + "</code>"
            else:
                if is_block_err(err):
                    store.bset("blk_" + str(t), "1")
                    head = "🚫 <code>" + esc(t) + "</code> কে মেসেজ পাঠানো যায়নি (বট ব্লক করেছে বা চ্যাট নেই)।"
                else:
                    head = "❌ পাঠানো যায়নি: <code>" + esc(t) + "</code>\n" + esc(err)
            ctx.send(head, [
                [ib("✉️ আরেকটা মেসেজ", "/admin dm " + str(t), "success")],
                [ib("🔙 প্যানেল", "/admin panel", "primary")],
            ], html=True)
            return

        # --- অটো মেসেজ: নিজে সময় লেখা ---
        if mode == "auto_times":
            n = int(ctx.get("auto_n", 1))
            toks = [x for x in re.split(r"[\s,]+", txt) if x]
            arr = []
            ok = len(toks) > 0
            for tk in toks:
                mm = re.match(r"^(\d{1,2})(?::(\d{2}))?$", tk)
                if not mm or int(mm.group(1)) > 23 or (mm.group(2) and int(mm.group(2)) > 59):
                    ok = False
                    break
                v = int(mm.group(1)) * 60 + (int(mm.group(2)) if mm.group(2) else 0)
                if v not in arr:
                    arr.append(v)
            if not ok or len(arr) != n:
                ctx.send("⚠️ ঠিক <b>" + bnum(n) + "</b> টা আলাদা সময় দাও। যেমন: <code>10 11</code>", CANCEL_KB, html=True)
                return
            arr.sort()
            ctx.set("auto_times", arr)
            ctx.set("admin_mode", "")
            ctx.send("✅ সময় সেট হয়েছে: <b>" + ", ".join(fmt(x) for x in arr) + "</b>", [
                [ib("➡️ পরের ধাপ", "/admin autopost", "success")],
                [ib("✏️ আবার লিখব", "/admin autotype", "primary")],
            ], html=True)
            return

        # --- অটো মেসেজ: পোস্ট নেওয়া ---
        if mode == "auto_msg":
            ctx.set("auto_draft", {"chat": cid, "msg": mid})
            ctx.set("auto_btns", [])
            ctx.set("admin_mode", "")
            send_auto_menu(ctx, "👆 এটাই অটো পোস্ট হবে। নিচে Button যোগ করতে পারো, না লাগলে সরাসরি সেভ করো।")
            return

        # --- Button: লেখা ---
        if mode == "ab_text":
            if not txt:
                ctx.send("Button এর লেখাটা টেক্সট হিসেবে পাঠাও।", CANCEL_KB)
                return
            ctx.set("ab_cur", {"text": txt[:60]})
            ctx.set("admin_mode", "ab_emoji")
            ctx.send("💎 Button এ Premium emoji বসাতে চাইলে emoji ID (শুধু সংখ্যা) পাঠাও।\n\nনা চাইলে Skip চাপো।", [
                [ib("⏭ Skip (emoji ছাড়া)", "/admin autobskip", "primary")],
                [ib("❌ বাতিল", "/admin cancel", "danger")],
            ])
            return

        # --- Button: emoji ID ---
        if mode == "ab_emoji":
            if not re.match(r"^\d{10,25}$", txt):
                ctx.send("⚠️ সঠিক emoji ID পাঠাও (শুধু সংখ্যা), অথবা Skip চাপো।", [
                    [ib("⏭ Skip (emoji ছাড়া)", "/admin autobskip", "primary")],
                    [ib("❌ বাতিল", "/admin cancel", "danger")],
                ])
                return
            cur = ctx.get("ab_cur", {})
            cur["emoji"] = txt
            ctx.set("ab_cur", cur)
            ctx.set("admin_mode", "")
            show_color(ctx)
            return

        # --- Button: link ---
        if mode == "ab_url":
            u = txt
            if re.match(r"^(t\.me|telegram\.me)/\S+$", u):
                u = "https://" + u
            if not re.match(r"^(https?|tg)://\S+$", u):
                ctx.send("⚠️ লিংকটা ঠিক না। https://... বা t.me/... দিয়ে পাঠাও।", CANCEL_KB)
                return
            cur = ctx.get("ab_cur", {})
            cur["url"] = u
            btns = ctx.get("auto_btns", [])
            btns.append(cur)
            ctx.set("auto_btns", btns)
            ctx.set("ab_cur", {})
            ctx.set("admin_mode", "")
            send_auto_menu(ctx, "✅ Button যোগ হয়েছে।")
            return

    # ===================== UID ধরা =====================
    vip_type = ctx.get("waiting_uid")
    if not vip_type:
        return
    uid = txt
    if not uid or uid.startswith("/"):
        return
    if not re.match(r"^[0-9A-Za-z]{4,25}$", uid):
        ctx.send("⚠️ সঠিক UID পাঠান।")
        return

    ctx.set("waiting_uid", "")

    LABEL = {
        "normal": "📊 NORMAL VIP USER",
        "advanced": "📈 ADVANCED VIP USER",
        "personal": "💎 PERSONAL VIP USER",
        "tournament": "🏆 TOURNAMENT GROUP USER",
        "forex": "📊 FOREX VIP USER",
        "learn": "📚 TRADING CLASS USER",
    }

    # ----- User ke prothom message -----
    if vip_type == "learn":
        ctx.send(
            e("6300926170959453705", "✅") + " <b>Alhamdulillah, আপনার Account Create করা হয়েছে।</b>\n" +
            "<b>অনুগ্রহ করে আপনার Accountটি Verify করে নিন।</b>\n\n" +
            e("5420094143089111506", "🗝") + " <b>Verify করার পর আবার UID SUBMIT করুন।</b>\n\n" +
            e("6255910249362885846", "⚠️") + " <b>Account Verify না করে UID SUBMIT করবেন না।</b>",
            [[eb("UID SUBMIT", "6120832956673040895", "/vip uid learn", "primary")]], html=True)
    else:
        ctx.send(e("5213452215527677338", "⏳") + " <b>আপনার UID চেক করা হচ্ছে... একটু অপেক্ষা করুন।</b>", html=True)

    # ----- Admin ke message -----
    name = esc(((ctx.user.get("first_name") or "") + " " + (ctx.user.get("last_name") or "")).strip())
    uname = "@" + esc(ctx.user["username"]) if ctx.user.get("username") else "নেই"
    now = bd_now()
    hh = now.hour
    time_str = "%d:%02d %s" % ((hh % 12) or 12, now.minute, "PM" if hh >= 12 else "AM")

    sid2 = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    store.bset("s_" + sid2, {"uid": uid, "by": ""})

    text = (
        "<b>" + LABEL.get(vip_type, "VIP USER") + "</b>\n\n" +
        "👤 <b>Name:</b> " + name + "\n" +
        "🔖 <b>Username:</b> " + uname + "\n" +
        "🆔 <b>User ID:</b> <code>" + ctx.uid + "</code>\n" +
        "🔢 <b>UID:</b> <code>" + esc(uid) + "</code>\n" +
        "🕒 <b>সময়:</b> " + time_str
    )

    if vip_type == "learn":
        last_row = [{"text": "VERIFIED NOW", "callback_data": "/admin verified " + ctx.uid + " learn " + sid2,
                     "icon_custom_emoji_id": "6253353798928959936", "style": "success"}]
    else:
        last_row = [{"text": "DP NOW", "callback_data": "/admin dp " + ctx.uid + " " + vip_type + " " + sid2,
                     "icon_custom_emoji_id": "5440660757194744323", "style": "primary"}]

    kb = [
        [copy_btn("COPY UID", uid, "primary")],
        [{"text": "REJECT", "callback_data": "/admin reject " + ctx.uid + " " + vip_type + " " + sid2,
          "icon_custom_emoji_id": "6253758805755038090", "style": "danger"},
         {"text": "APPROVE", "callback_data": "/admin approve " + ctx.uid + " " + vip_type + " " + sid2,
          "icon_custom_emoji_id": "6255591515544882364", "style": "success"}],
        last_row,
    ]
    for a in ADMINS:
        send(a, text, kb, html=True)


# =====================================================================
#  ROUTER + POLLING
# =====================================================================
COMMANDS = {
    "start": cmd_start,
    "menu": cmd_menu,
    "vip": cmd_vip,
    "channel": cmd_channel,
    "social": cmd_social,
    "tutorial": cmd_tutorial,
    "admin": cmd_admin,
}


def route(ctx, text):
    parts = text.strip().split(" ", 1)
    cmd = parts[0][1:].split("@")[0].lower()
    params = parts[1].strip() if len(parts) > 1 else ""
    fn = COMMANDS.get(cmd)
    if fn:
        fn(ctx, params)
        return True
    return False


def handle_update(u):
    try:
        if "callback_query" in u:
            cq = u["callback_query"]
            api("answerCallbackQuery", callback_query_id=cq["id"])
            msg = cq.get("message")
            data = cq.get("data") or ""
            if not msg or not data.startswith("/"):
                return
            ctx = Ctx(cq["from"], msg["chat"]["id"], msg, True)
            route(ctx, data)

        elif "message" in u:
            m = u["message"]
            if m["chat"].get("type") != "private":
                return
            ctx = Ctx(m["from"], m["chat"]["id"], m, False)
            text = m.get("text") or ""
            if text.startswith("/") and route(ctx, text):
                return
            on_message(ctx, m)
    except Exception:
        traceback.print_exc()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if "EKHANE_BOSHAO" in BOT_TOKEN:
        print("ERROR: bot.py er line 33 e BOT_TOKEN ta boshano hoyni. Real token boshiye abar upload koro.")
        return
    me = api("getMe")
    if not me.get("ok"):
        print("BOT_TOKEN ভুল বা কাজ করছে না! bot.py er BOT_TOKEN ta thik korun.")
        print(me)
        return
    print("Bot started: @" + me["result"]["username"])

    api("deleteWebhook")   # Bots.Business webhook thakle remove hobe

    # 3 dot menu
    api("setMyCommands", commands=[{"command": "start", "description": "Start"}])
    for a in ADMINS:
        api("setMyCommands",
            commands=[{"command": "start", "description": "Start"},
                      {"command": "admin", "description": "অ্যাডমিন প্যানেল"}],
            scope={"type": "chat", "chat_id": int(a)})

    threading.Thread(target=scheduler, daemon=True).start()

    pool = ThreadPoolExecutor(max_workers=16)
    offset = None
    while True:
        try:
            p = {"timeout": 50, "allowed_updates": ["message", "callback_query"]}
            if offset:
                p["offset"] = offset
            r = api("getUpdates", **p)
            if not r.get("ok"):
                print("getUpdates error:", r.get("description"))
                time.sleep(3)
                continue
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                pool.submit(handle_update, u)
        except KeyboardInterrupt:
            print("Stopped.")
            break
        except Exception:
            traceback.print_exc()
            time.sleep(3)


if __name__ == "__main__":
    main()

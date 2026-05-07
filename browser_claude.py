"""Generate articles by automating claude.ai in a browser (no API key needed)."""
import json
import os
import time
from pathlib import Path

from rich.console import Console

console = Console()

SESSIONS_DIR = Path("sessions")
COOKIES_FILE = SESSIONS_DIR / "claude_cookies.json"

_CHROMIUM_CANDIDATES = [
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
    "/usr/bin/google-chrome",
]


def _find_chromium() -> str | None:
    for path in _CHROMIUM_CANDIDATES:
        if Path(path).exists():
            return path
    return None


def _has_display() -> bool:
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


PROMPT_TEMPLATE = """「{topic}」について最新情報をウェブで検索・リサーチして、
noteに掲載できる高品質なまとめ記事を作成してください。

必ず以下のJSON形式のみで出力してください（前後に説明文は不要）:

{{
  "title": "記事タイトル（30字以内、クリックしたくなる魅力的な内容）",
  "subtitle": "SEO向けサブタイトル（60字以内）",
  "intro": "導入文（150〜200字、読者の興味を引く問いかけや驚きの情報で始める）",
  "sections": [
    {{"heading": "セクション見出し1", "content": "本文300〜500字（具体的な数字・事例を含む）"}},
    {{"heading": "セクション見出し2", "content": "本文300〜500字"}},
    {{"heading": "セクション見出し3", "content": "本文300〜500字"}},
    {{"heading": "セクション見出し4", "content": "本文300〜500字"}},
    {{"heading": "セクション見出し5", "content": "本文300〜500字"}}
  ],
  "conclusion": "まとめと考察（200〜300字）",
  "action": "読者へのアクション提案（50〜100字）",
  "hashtags": ["ハッシュタグ1", "ハッシュタグ2", "ハッシュタグ3", "ハッシュタグ4"],
  "key_points": ["ポイント1（30字以内）", "ポイント2（30字以内）", "ポイント3（30字以内）"]
}}"""


def _save_cookies(context):
    SESSIONS_DIR.mkdir(exist_ok=True)
    COOKIES_FILE.write_text(json.dumps(context.cookies(), ensure_ascii=False))


def _load_cookies(context) -> bool:
    if COOKIES_FILE.exists():
        try:
            context.add_cookies(json.loads(COOKIES_FILE.read_text()))
            return True
        except Exception:
            pass
    return False


def _is_logged_in(page) -> bool:
    try:
        page.wait_for_selector('div[contenteditable="true"]', timeout=6000)
        # If we see the input box we're on the chat page = logged in
        if "claude.ai" in page.url and "login" not in page.url:
            return True
    except Exception:
        pass
    return False


def _find_input(page):
    for selector in [
        'div[contenteditable="true"][data-placeholder]',
        'div.ProseMirror[contenteditable="true"]',
        'div[contenteditable="true"]',
    ]:
        loc = page.locator(selector)
        if loc.count() > 0:
            return loc.first
    raise RuntimeError("入力欄が見つかりません")


def _type_prompt(page, prompt: str, headless: bool):
    input_box = _find_input(page)
    input_box.click()
    time.sleep(0.3)

    if headless:
        # In headless mode inject text directly via JS into ProseMirror
        page.evaluate("""(text) => {
            const el = document.querySelector('div[contenteditable="true"]');
            if (!el) return;
            el.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, text);
        }""", prompt)
    else:
        # Headed: use clipboard paste (most reliable for Japanese)
        page.evaluate(f"navigator.clipboard.writeText({json.dumps(prompt)})")
        page.keyboard.press("Control+v")

    time.sleep(0.5)
    page.keyboard.press("Enter")


def _wait_for_completion(page, timeout: int = 300) -> str:
    console.print("  [dim]生成中[/dim]", end="")
    time.sleep(5)

    last_text = ""
    stable_count = 0
    deadline = time.time() + timeout

    while time.time() < deadline:
        text = ""
        for selector in [
            '[data-message-author-role="assistant"]',
            '[data-testid="message-content"]',
            '.font-claude-message',
        ]:
            els = page.locator(selector)
            if els.count() > 0:
                text = els.last.inner_text()
                break

        if text and text == last_text:
            stable_count += 1
            if stable_count >= 6:
                console.print(" [green]完了[/green]")
                return text
        else:
            stable_count = 0
            last_text = text
            console.print(".", end="", flush=True)

        time.sleep(0.5)

    console.print(" [yellow]タイムアウト[/yellow]")
    return last_text


def _parse_article(text: str, topic: str) -> dict:
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start:end])
            if all(k in data for k in ["title", "intro", "sections"]):
                return data
        except json.JSONDecodeError:
            pass
    return {
        "title": f"【{topic}】最新まとめ",
        "subtitle": f"{topic}の最新情報と解説",
        "intro": f"今回は「{topic}」について最新情報をまとめました。",
        "sections": [{"heading": "記事内容", "content": text[:3000]}],
        "conclusion": "以上が最新情報のまとめです。",
        "action": "ぜひnoteをフォローして最新情報をお届けします。",
        "hashtags": [topic, "まとめ", "ニュース", "情報収集"],
        "key_points": [],
    }


def generate_article(topic: str) -> dict:
    """Open claude.ai in a browser, send the prompt, and return the parsed article dict."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("pip install playwright && python -m playwright install chromium")

    headless = not _has_display()

    if headless and not COOKIES_FILE.exists():
        raise RuntimeError(
            "ヘッドレス環境ではログイン済みクッキーが必要です。\n"
            "  python main.py login  を実行してセットアップしてください。"
        )

    prompt = PROMPT_TEMPLATE.format(topic=topic)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            executable_path=_find_chromium(),
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            ignore_https_errors=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/141.0.0.0 Safari/537.36"
            ),
        )
        _load_cookies(context)

        page = context.new_page()
        page.goto("https://claude.ai/new", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        if not headless and not _is_logged_in(page):
            console.print(
                "\n[bold yellow]Claude にログインしてください。[/bold yellow]\n"
                "ブラウザでログインが完了したら [bold]Enter[/bold] を押してください... "
            )
            input()
            _save_cookies(context)
            page.goto("https://claude.ai/new", wait_until="domcontentloaded")
            time.sleep(2)

        _type_prompt(page, prompt, headless=headless)
        response_text = _wait_for_completion(page)
        _save_cookies(context)
        browser.close()

    return _parse_article(response_text, topic)

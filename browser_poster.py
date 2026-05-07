"""Post to X (Twitter) and note.com via browser automation (no API key needed)."""
import json
import os
import time
from pathlib import Path

from rich.console import Console

console = Console()

SESSIONS_DIR = Path("sessions")

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


def _launch_browser(p):
    headless = not _has_display()
    return p.chromium.launch(
        headless=headless,
        executable_path=_find_chromium(),
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
    ), headless


def _new_context(browser):
    return browser.new_context(
        ignore_https_errors=True,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/141.0.0.0 Safari/537.36"
        ),
    )


def _save_cookies(context, name: str):
    SESSIONS_DIR.mkdir(exist_ok=True)
    (SESSIONS_DIR / f"{name}_cookies.json").write_text(
        json.dumps(context.cookies(), ensure_ascii=False)
    )


def _load_cookies(context, name: str) -> bool:
    path = SESSIONS_DIR / f"{name}_cookies.json"
    if path.exists():
        try:
            context.add_cookies(json.loads(path.read_text()))
            return True
        except Exception:
            pass
    return False


def _require_cookies(name: str):
    path = SESSIONS_DIR / f"{name}_cookies.json"
    if not path.exists():
        raise RuntimeError(
            f"ヘッドレス環境では {name} のログイン済みクッキーが必要です。\n"
            "  python main.py login  を実行してセットアップしてください。"
        )


def _x_is_logged_in(page) -> bool:
    try:
        page.wait_for_selector('[data-testid="SideNav_AccountSwitcher_Button"]', timeout=5000)
        return True
    except Exception:
        return False


def _x_compose_tweet(page, text: str) -> str:
    page.click('[data-testid="SideNav_NewTweet_Button"]')
    time.sleep(1)
    compose = page.locator('[data-testid="tweetTextarea_0"]')
    compose.wait_for(timeout=8000)
    compose.click()
    compose.fill(text)
    time.sleep(0.5)
    post_btn = page.locator('[data-testid="tweetButton"]')
    post_btn.wait_for(state="enabled", timeout=5000)
    post_btn.click()
    time.sleep(3)
    try:
        href = page.locator('a[href*="/status/"]').first.get_attribute("href")
        return f"https://x.com{href}" if href and href.startswith("/") else href or ""
    except Exception:
        return ""


def _x_reply_to(page, tweet_url: str, text: str) -> str:
    page.goto(tweet_url, wait_until="domcontentloaded")
    time.sleep(2)
    page.locator('[data-testid="reply"]').first.wait_for(timeout=8000)
    page.locator('[data-testid="reply"]').first.click()
    time.sleep(1)
    compose = page.locator('[data-testid="tweetTextarea_0"]')
    compose.wait_for(timeout=5000)
    compose.click()
    compose.fill(text)
    time.sleep(0.5)
    page.locator('[data-testid="tweetButton"]').wait_for(state="enabled", timeout=5000)
    page.locator('[data-testid="tweetButton"]').click()
    time.sleep(3)
    try:
        href = page.locator('a[href*="/status/"]').nth(1).get_attribute("href")
        return f"https://x.com{href}" if href and href.startswith("/") else href or ""
    except Exception:
        return ""


def post_x_thread(x_post: str) -> list[str]:
    """Post an X thread. Returns list of tweet URLs."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("pip install playwright && python -m playwright install chromium")

    headless = not _has_display()
    if headless:
        _require_cookies("x")

    tweets = [t.strip() for t in x_post.split("---") if t.strip()]

    with sync_playwright() as p:
        browser, headless = _launch_browser(p)
        context = _new_context(browser)
        _load_cookies(context, "x")

        page = context.new_page()
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)

        if not headless and not _x_is_logged_in(page):
            console.print(
                "\n[bold yellow]X (Twitter) にログインしてください。[/bold yellow]\n"
                "ブラウザでログインが完了したら [bold]Enter[/bold] を押してください... "
            )
            input()
            _save_cookies(context, "x")

        urls = []
        prev_url = None
        for i, tweet in enumerate(tweets):
            if len(tweet) > 280:
                tweet = tweet[:277] + "…"
            console.print(f"  ツイート {i+1}/{len(tweets)} を投稿中...")
            url = _x_reply_to(page, prev_url, tweet) if prev_url else _x_compose_tweet(page, tweet)
            urls.append(url)
            prev_url = url or prev_url
            time.sleep(2)

        _save_cookies(context, "x")
        browser.close()

    return urls


def _note_is_logged_in(page) -> bool:
    try:
        page.wait_for_selector('[data-e2e="header-user-icon"]', timeout=5000)
        return True
    except Exception:
        pass
    try:
        page.wait_for_selector('a[href*="/settings"]', timeout=3000)
        return True
    except Exception:
        return False


def post_note_article(title: str, body: str, price: int, publish: bool = False) -> str:
    """Create a note article via browser. Returns the article URL."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("pip install playwright && python -m playwright install chromium")

    headless = not _has_display()
    if headless:
        _require_cookies("note")

    with sync_playwright() as p:
        browser, headless = _launch_browser(p)
        context = _new_context(browser)
        _load_cookies(context, "note")

        page = context.new_page()
        page.goto("https://note.com", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)

        if not headless and not _note_is_logged_in(page):
            console.print(
                "\n[bold yellow]note.com にログインしてください。[/bold yellow]\n"
                "ブラウザでログインが完了したら [bold]Enter[/bold] を押してください... "
            )
            input()
            _save_cookies(context, "note")

        page.goto("https://note.com/notes/new", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        title_input = page.locator('[placeholder="記事タイトル"]')
        if title_input.count() == 0:
            title_input = page.locator('input[type="text"]').first
        title_input.click()
        title_input.fill(title)
        time.sleep(0.5)

        body_area = page.locator('.ProseMirror[contenteditable="true"]')
        if body_area.count() == 0:
            body_area = page.locator('[contenteditable="true"]').last
        body_area.click()
        time.sleep(0.3)

        if headless:
            page.evaluate("""(text) => {
                const el = document.querySelector('.ProseMirror[contenteditable="true"]')
                    || document.querySelector('[contenteditable="true"]');
                if (el) { el.focus(); document.execCommand('insertText', false, text); }
            }""", body)
        else:
            context.grant_permissions(["clipboard-read", "clipboard-write"])
            page.evaluate(f"navigator.clipboard.writeText({json.dumps(body)})")
            page.keyboard.press("Control+v")
        time.sleep(1)

        try:
            settings_btn = page.locator(
                'button:has-text("販売設定"), button:has-text("有料"), [aria-label*="設定"]'
            ).first
            if settings_btn.count() > 0:
                settings_btn.click()
                time.sleep(1)
                price_input = page.locator('input[type="number"], input[name*="price"]').first
                if price_input.count() > 0:
                    price_input.fill(str(price))
                    time.sleep(0.3)
                confirm = page.locator(
                    'button:has-text("設定"), button:has-text("OK"), button:has-text("確定")'
                ).last
                if confirm.count() > 0:
                    confirm.click()
                    time.sleep(0.5)
        except Exception as e:
            console.print(f"  [yellow]⚠️  価格設定をスキップ: {e}[/yellow]")

        if publish:
            page.locator('button:has-text("公開"), button:has-text("投稿")').first.wait_for(timeout=8000)
            page.locator('button:has-text("公開"), button:has-text("投稿")').first.click()
            time.sleep(1)
            confirm_pub = page.locator('button:has-text("公開する"), button:has-text("投稿する")').first
            if confirm_pub.count() > 0:
                confirm_pub.click()
                time.sleep(3)
        else:
            draft_btn = page.locator('button:has-text("下書き保存"), button:has-text("保存")').first
            if draft_btn.count() > 0:
                draft_btn.click()
                time.sleep(2)

        article_url = page.url
        _save_cookies(context, "note")
        browser.close()

    return article_url

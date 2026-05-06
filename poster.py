"""Post articles to X (Twitter) and note.com."""
import time
import requests
from rich.console import Console

console = Console()


class XPoster:
    def __init__(self, api_key: str, api_secret: str, access_token: str, access_token_secret: str):
        try:
            import tweepy
        except ImportError:
            raise RuntimeError("tweepy が未インストールです: pip install tweepy")

        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )

    def post_thread(self, x_post: str) -> list[str]:
        """Post X thread. Returns list of tweet URLs."""
        tweets = [t.strip() for t in x_post.split("---") if t.strip()]
        tweet_ids = []

        for i, tweet_text in enumerate(tweets):
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "…"

            kwargs = {"text": tweet_text}
            if tweet_ids:
                kwargs["in_reply_to_tweet_id"] = tweet_ids[-1]

            resp = self.client.create_tweet(**kwargs)
            tweet_ids.append(resp.data["id"])

            if i < len(tweets) - 1:
                time.sleep(1)  # rate limit buffer

        return [f"https://x.com/i/web/status/{tid}" for tid in tweet_ids]


class NotePoster:
    """Post to note.com via unofficial API (may change without notice)."""

    BASE = "https://note.com"

    def __init__(self, email: str, password: str):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://note.com/",
        })
        self._login(email, password)

    def _login(self, email: str, password: str):
        resp = self.session.post(
            f"{self.BASE}/api/v1/sessions",
            json={"login": email, "password": password},
            timeout=30,
        )
        if resp.status_code == 401:
            raise RuntimeError("note.com ログイン失敗: メールアドレスまたはパスワードが正しくありません")
        resp.raise_for_status()

    def create_article(self, title: str, body: str, price: int, publish: bool = False) -> str:
        """Create a paid article. Returns URL of the created note."""
        status = "published" if publish else "draft"
        resp = self.session.post(
            f"{self.BASE}/api/v2/text_notes",
            json={
                "name": title,
                "body": body,
                "price": price,
                "status": status,
                "publish_at": None,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        key = data.get("data", {}).get("key", "")
        return f"{self.BASE}/n/{key}" if key else f"{self.BASE}/notes"

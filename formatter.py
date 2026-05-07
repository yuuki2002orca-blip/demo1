"""Format articles for X (Twitter) and note.com."""
from datetime import datetime


class ArticleFormatter:
    def __init__(self, note_price: int = 1980, subscription_price: int = 980):
        self.note_price = note_price
        self.subscription_price = subscription_price

    def format_x_post(self, article: dict) -> str:
        title = article.get("title", "")
        intro = article.get("intro", "")
        key_points = article.get("key_points", [])
        hashtags = article.get("hashtags", [])

        parts = []

        tweet1 = f"【{title}】\n\n"
        if intro:
            tweet1 += intro[:180] + ("…" if len(intro) > 180 else "")
        parts.append(tweet1)

        if key_points:
            tweet2 = "📌 この記事のポイント\n\n"
            for i, point in enumerate(key_points[:3], 1):
                tweet2 += f"{i}. {point}\n"
            parts.append(tweet2)

        tweet3 = (
            f"✨ 詳細はnoteで解説中！\n\n"
            f"📖 有料記事（¥{self.note_price:,}）で全内容を公開\n"
            f"📚 月額¥{self.subscription_price:,}のサブスクなら読み放題\n\n"
            f"👉 プロフィールのリンクからチェック！"
        )
        if hashtags:
            tweet3 += "\n\n" + " ".join(f"#{tag}" for tag in hashtags[:4])
        parts.append(tweet3)

        return "\n\n---\n\n".join(parts)

    def format_note_article(self, article: dict) -> str:
        title = article.get("title", "")
        subtitle = article.get("subtitle", "")
        intro = article.get("intro", "")
        sections = article.get("sections", [])
        conclusion = article.get("conclusion", "")
        action = article.get("action", "")
        hashtags = article.get("hashtags", [])

        today = datetime.now().strftime("%Y年%m月%d日")
        lines = []

        lines += [f"# {title}", "", f"_{subtitle}_" if subtitle else "", "", f"更新日：{today}", "", "---", ""]
        lines += ["## はじめに", "", intro, ""]

        if sections:
            s = sections[0]
            lines += [f"## {s['heading']}", "", s["content"], ""]

        lines += [
            "---", "",
            f"> ### 💎 ここから先は有料コンテンツです",
            f">",
            f"> **¥{self.note_price:,}** で購入するか、**月額¥{self.subscription_price:,}** のサブスクに登録すると読み放題になります。",
            "", "---", "",
        ]

        for s in sections[1:]:
            lines += [f"## {s['heading']}", "", s["content"], ""]

        if conclusion:
            lines += ["## まとめ", "", conclusion, ""]
        if action:
            lines += ["## 次のステップ", "", action, ""]

        lines += [
            "---", "",
            "## 📚 過去記事もまとめて読む", "",
            f"このnoteをフォロー（月額 **¥{self.subscription_price:,}**）すると、",
            "過去の全記事が読み放題になります。", "",
            "毎週新しいまとめ記事を配信中！お見逃しなく。", "",
        ]

        if hashtags:
            lines += ["---", "", " ".join(f"#{tag}" for tag in hashtags)]

        return "\n".join(lines)

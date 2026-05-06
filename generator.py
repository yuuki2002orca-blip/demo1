"""Article generation using Claude API with web search."""
import json
import anthropic
from rich.console import Console

console = Console()

SYSTEM_PROMPT = """あなたは日本語コンテンツのプロのライターです。
ウェブで最新情報をリサーチして、読者を引き込む高品質なまとめ記事を作成します。

執筆の指針:
- 読みやすく、分かりやすい日本語で書く
- 具体的な数字やデータを積極的に引用する
- 読者が「シェアしたい」「保存したい」と思う情報価値を提供する
- SEOを意識したキーワードを自然に含める
- 各セクションに具体的な事例や引用を盛り込む"""


def generate_article(topic: str, client: anthropic.Anthropic, model: str) -> dict:
    """Research and generate a complete article. Returns structured dict."""

    prompt = f"""「{topic}」について最新情報をウェブで検索・リサーチして、
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

    full_text = ""

    with client.messages.stream(
        model=model,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            full_text += text
            print(text, end="", flush=True)

    print()
    return _parse_article(full_text, topic)


def _parse_article(text: str, topic: str) -> dict:
    """Parse JSON response with fallback structure."""
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

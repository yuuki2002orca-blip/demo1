#!/usr/bin/env python3
"""
AI Content Monetization Tool
AIでニュースをリサーチしてnote記事を量産し、Xで集客するシステム

みかみおすすめマネタイズ方法:
  ①AIに様々なニュースをリサーチさせてそのまとめ記事を量産させる
  ②まとめ記事の途中までをXに上げて続きをnoteで読める様にする
  ③noteは1つ1980円ぐらいに設定
  ④過去の記事が読めるサブスクも設ける
"""
import os
import sys
from pathlib import Path
from datetime import datetime

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()
console = Console()


@click.group()
def cli():
    """🤖 AI Content Monetization Tool

    AIでニュースをリサーチしてnote記事を量産し、Xで集客するシステム
    """
    pass


@cli.command()
@click.argument("topic")
@click.option("--model", default="claude-opus-4-7", show_default=True, help="使用するClaudeモデル")
@click.option("--output-dir", default="articles", show_default=True, help="出力ディレクトリ")
@click.option("--note-price", default=1980, show_default=True, help="noteの有料記事価格（円）")
@click.option("--sub-price", default=980, show_default=True, help="noteのサブスク月額（円）")
def generate(topic, model, output_dir, note_price, sub_price):
    """TOPICについてAIが記事を生成し、X用とnote用に出力します

    例: python main.py generate "AI最新動向"
    """
    import anthropic
    from generator import generate_article
    from formatter import ArticleFormatter

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]❌ ANTHROPIC_API_KEY が設定されていません[/red]")
        console.print("  .env ファイルに ANTHROPIC_API_KEY=sk-... を追加してください")
        sys.exit(1)

    console.print(Panel(
        f"[bold cyan]トピック:[/bold cyan] {topic}\n"
        f"[bold cyan]モデル:[/bold cyan] {model}\n"
        f"[bold cyan]note価格:[/bold cyan] ¥{note_price:,} / サブスク ¥{sub_price:,}/月",
        title="[bold]🤖 AI記事生成システム[/bold]",
        border_style="cyan",
    ))

    client = anthropic.Anthropic(api_key=api_key)

    console.print("\n[bold yellow]📰 ニュースをリサーチ中...[/bold yellow]\n")

    article = generate_article(topic=topic, client=client, model=model)

    formatter = ArticleFormatter(note_price=note_price, subscription_price=sub_price)
    x_post = formatter.format_x_post(article)
    note_content = formatter.format_note_article(article)

    # Save to files
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic)[:30]
    base = f"{timestamp}_{safe_topic}"

    x_file = output_path / f"{base}_x.txt"
    note_file = output_path / f"{base}_note.md"

    x_file.write_text(x_post, encoding="utf-8")
    note_file.write_text(note_content, encoding="utf-8")

    # Display summary
    console.print("\n[bold green]✅ 生成完了！[/bold green]\n")

    table = Table(title="出力ファイル", show_header=True, header_style="bold cyan")
    table.add_column("プラットフォーム", style="cyan", min_width=16)
    table.add_column("ファイル", style="green")
    table.add_column("用途", style="white")

    table.add_row("X (旧Twitter)", str(x_file), "無料ティーザー投稿でnoteへ誘導")
    table.add_row("note", str(note_file), f"有料記事 ¥{note_price:,} / サブスク ¥{sub_price:,}/月")

    console.print(table)

    console.print("\n[bold]📱 X投稿プレビュー（1ツイート目）:[/bold]")
    first_tweet = x_post.split("---")[0].strip()
    console.print(Panel(first_tweet, border_style="cyan", width=64))


@cli.command()
@click.argument("topics_file", type=click.Path(exists=True))
@click.option("--model", default="claude-opus-4-7", show_default=True, help="使用するClaudeモデル")
@click.option("--output-dir", default="articles", show_default=True, help="出力ディレクトリ")
@click.option("--note-price", default=1980, show_default=True, help="noteの有料記事価格（円）")
@click.option("--sub-price", default=980, show_default=True, help="noteのサブスク月額（円）")
def batch(topics_file, model, output_dir, note_price, sub_price):
    """TOPICS_FILEに記載されたトピック一覧で記事を一括生成します（1行1トピック）

    例: python main.py batch topics_example.txt
    """
    import anthropic
    from generator import generate_article
    from formatter import ArticleFormatter

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]❌ ANTHROPIC_API_KEY が設定されていません[/red]")
        sys.exit(1)

    topics = [
        line.strip()
        for line in Path(topics_file).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

    if not topics:
        console.print("[red]❌ トピックが見つかりません（# から始まる行はコメントとして無視されます）[/red]")
        sys.exit(1)

    console.print(Panel(
        f"[bold]{len(topics)}件のトピックを処理します[/bold]\n\n"
        + "\n".join(f"  • {t}" for t in topics[:5])
        + (f"\n  ... 他 {len(topics) - 5} 件" if len(topics) > 5 else ""),
        title="[bold]🚀 バッチ記事生成[/bold]",
        border_style="blue",
    ))

    client = anthropic.Anthropic(api_key=api_key)
    formatter = ArticleFormatter(note_price=note_price, subscription_price=sub_price)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    success, failed = 0, 0

    for i, topic in enumerate(topics, 1):
        console.print(f"\n[bold blue]({i}/{len(topics)}) 「{topic}」を生成中...[/bold blue]")

        try:
            article = generate_article(topic=topic, client=client, model=model)

            x_post = formatter.format_x_post(article)
            note_content = formatter.format_note_article(article)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = "".join(c if c.isalnum() or c in "-_" else "_" for c in topic)[:30]
            base = f"{timestamp}_{safe_topic}"

            (output_path / f"{base}_x.txt").write_text(x_post, encoding="utf-8")
            (output_path / f"{base}_note.md").write_text(note_content, encoding="utf-8")

            console.print(f"  [green]✅ 完了: {article.get('title', topic)}[/green]")
            success += 1

        except Exception as e:
            console.print(f"  [red]❌ エラー: {e}[/red]")
            failed += 1

    console.print(f"\n[bold green]🎉 バッチ処理完了！[/bold green]")
    console.print(f"  成功: {success}件 / 失敗: {failed}件")
    console.print(f"  出力先: {output_dir}/")


if __name__ == "__main__":
    cli()

# tor-selenium-x

最もシンプルで再現性の高いTor + Selenium + Docker構成によるウェブスクレーピングプロジェクト

## 🎯 特徴

- **シンプル**: 無駄のない最小構成
- **再現性**: Dockerによる環境の完全一致
- **匿名性**: Tor経由でのアクセス
- **DuckDuckGo**: プライバシー重視の検索エンジンを使用
- **モダンな開発環境**: UV、Python 3.12、最新のSelenium

参考記事:
- [PythonでSeleniumとTorの合わせ技](https://qiita.com/kawagoe6884/items/381a938dd3d8744f29d4)
- [【悪用禁止】Torで匿名性を確保しながらSeleniumでスクレイピングする](https://zenn.dev/harurow/articles/7b845931350cb8)

## 🚀 クイックスタート

### 必要な環境

- Docker & Docker Compose
- Make (オプション)

### 実行

```bash
# リポジトリをクローン
git clone <repository-url>
cd tor-selenium-x

# Docker経由で実行
make run

# または
docker-compose up --build tor-scraper
```

これだけで、Tor経由でDuckDuckGoにアクセスし、匿名でウェブスクレーピングが実行されます。

## 📦 コマンド一覧

```bash
# ヘルプ表示
make help

# Tor Scraperを実行
make run

# 開発モードで実行
make dev

# コンテナ内でシェルを開く
make shell

# ログを確認
make logs

# 停止
make stop

# クリーンアップ
make clean
```

## 🏗️ プロジェクト構成

```
tor-selenium-x/
├── src/
│   ├── __init__.py
│   ├── main.py            # メインエントリーポイント
│   └── tor_scraper.py     # Torスクレーパークラス
├── tests/
│   ├── __init__.py
│   └── test_tor_scraper.py
├── docker/
│   ├── Dockerfile         # Docker設定
│   ├── docker-compose.yml # Docker Compose設定
│   └── docker-entrypoint.sh # コンテナ起動スクリプト
├── scripts/
│   └── setup.sh          # セットアップスクリプト
├── .vscode/
│   └── settings.json     # VS Code設定
├── pyproject.toml        # Python依存関係・ツール設定
├── uv.lock              # 依存関係ロックファイル
├── Makefile             # 開発用コマンド
└── README.md
```

## 🛠️ 技術スタック

- **Python 3.12**: 最新のPython
- **UV**: 高速なPythonパッケージマネージャー
- **Selenium 4.15+**: ウェブブラウザ自動化
- **Tor**: 匿名ネットワーク
- **Chromium/Firefox**: ヘッドレスブラウザ
- **Docker**: コンテナ化
- **Ruff**: 統合開発ツール（フォーマッター + リンター）
- **Pylance**: 型チェック・IntelliSense

## 🧪 開発環境セットアップ

### ローカル開発

```bash
# UV環境のセットアップ
uv init --python 3.12
uv sync --all-extras

# 仮想環境の有効化
source .venv/bin/activate

# 開発用コマンド
make install   # 依存関係インストール
make format    # コードフォーマット (Ruff)
make lint      # リンター実行 (Ruff)
make fix       # 自動修正 (Ruff)
make test      # テスト実行 (pytest)
make check     # lint + test
```

### VS Code設定

プロジェクトには以下が設定済み：
- **Ruff**: 統合フォーマッター・リンター・インポート整理
- **Pylance**: 型チェック・IntelliSense
- **pytest**: テスト実行

必要な拡張機能（推奨）：
- Python (`ms-python.python`)
- Pylance (`ms-python.pylance`)
- Ruff (`charliermarsh.ruff`)

## 🔧 カスタマイズ

### 検索クエリの変更

`src/main.py`でメインロジックを変更できます：

```python
# DuckDuckGoで検索
scraper.search_duckduckgo("Your search query here")
```

### 他のサイトへのアクセス

`src/tor_scraper.py`の`TorScraper`クラスにメソッドを追加してカスタマイズ可能：

```python
def visit_site(self, url: str) -> None:
    """任意のサイトにアクセス"""
    self.driver.get(url)
    # スクレーピングロジック
```

## 🐳 Docker環境

### 設定詳細

- **ベースイメージ**: Python 3.12-slim
- **Tor**: SocksPort 9050, ControlPort 9051
- **Chrome**: Stable版 + webdriver-manager
- **UV**: 依存関係管理

### Docker コマンド

```bash
# ビルド
docker build -f docker/Dockerfile -t tor-selenium-x .

# 実行
docker run --rm tor-selenium-x

# 開発モード
docker run --rm -v $(pwd)/src:/app/src tor-selenium-x
```

## 📊 動作確認

実行すると以下の流れでスクレーピングが行われます：

1. 🚀 Torサービス起動
2. 🔍 Tor接続確認 (httpbin.org)
3. 🌐 匿名IPアドレス表示
4. 🦆 DuckDuckGoで検索実行
5. 📝 検索結果の取得・表示

## 🧪 テスト

```bash
# 全テスト実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=src --cov-report=html

# 特定のテスト
uv run pytest tests/test_tor_scraper.py::test_specific_function
```

## 🤝 トラブルシューティング

### よくある問題

**Tor接続に失敗する**
```bash
# コンテナのログを確認
make logs

# コンテナを再起動
make stop && make run
```

**ChromeDriverエラー**
- webdriver-managerが自動で最新版をダウンロードします
- コンテナを再ビルドしてください: `make clean && make build`

**依存関係の問題**
```bash
# ロックファイルの更新
uv lock --upgrade

# 環境の再構築
rm -rf .venv && uv sync --all-extras
```

## 🔒 セキュリティと注意事項

- **合法的な使用のみ**: スクレーピング対象サイトの利用規約を必ず確認
- **レート制限**: 過度なアクセスは避け、適切な間隔を設ける
- **robots.txt**: サイトのrobot.txt を尊重する
- **匿名性**: 完全な匿名性は保証されません

## 📄 ライセンス

MIT License

---

**⚠️ 免責事項**: このツールは教育目的で作成されています。スクレーピングは法的制限や利用規約に従って実行してください。

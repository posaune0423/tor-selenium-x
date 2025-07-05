# Tor Selenium X

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-green.svg)](https://www.docker.com/)

X (Twitter) スクレイパー - Tor Browser と tbselenium を使用してプライバシーと信頼性を確保

## 特徴

- **プライバシー第一**: Tor Browser を使用した匿名スクレイピング
- **安定したアーキテクチャ**: tbselenium ライブラリで構築
- **Docker 対応**: 開発環境と本番環境を提供
- **型安全**: 完全な型ヒントと包括的なテスト
- **ログイン機能**: X (Twitter) への認証対応
- **データ管理**: 構造化されたデータ保存とセッション管理
- **検出回避**: 人間らしい動作シミュレーションとBot検知対策

## クイックスタート

### Docker 使用（推奨）

```bash
# リポジトリをクローン
git clone https://github.com/your-username/tor-selenium-x.git
cd tor-selenium-x

# 開発環境を開始（2FA入力対応）
make dev

# ログを表示
make logs
```

### ローカル開発

```bash
# 依存関係をインストール
uv sync

# スクレイパーを実行
uv run python src/main.py
```

## 使用方法

### 基本的なスクレイピング

```python
from src.x_scraper import XScraper

# スクレイパーを初期化
scraper = XScraper(
    tbb_path="/opt/torbrowser",
    headless=True,
    socks_port=9150,  # 標準化されたポート
    control_port=9151,
)

try:
    # 開始と接続
    scraper.start()
    scraper.navigate_to_x()
    
    # ツイートを検索
    tweets = scraper.search_tweets("Python programming", max_tweets=10)
    
    # ユーザープロフィールを取得
    profile = scraper.get_user_profile("username")
    
    # データを保存
    scraper.save_tweets_to_json(tweets, "tweets")
    scraper.save_profile_to_json(profile, "profile")
    
finally:
    scraper.close()
```

### ログイン機能付きスクレイピング

```python
from src.x_scraper import XScraper

# スクレイパーを初期化（認証情報は環境変数から自動取得）
scraper = XScraper()

try:
    # 開始と接続
    scraper.start()
    
    # X にログイン（2FA 対応）
    if scraper.login():
        print("ログイン成功！")
        
        # 認証が必要な機能を使用
        tweets = scraper.search_tweets("限定公開アカウント", max_tweets=10)
        
    else:
        print("ログインに失敗しました")
        
finally:
    scraper.close()
```

## プロジェクト構造

```
src/
├── main.py              # エントリーポイント
├── x_scraper.py         # メインスクレイパークラス
├── models.py            # データモデル
├── constants.py         # 定数定義
└── utils/               # ユーティリティパッケージ
    ├── __init__.py      # パッケージ初期化と全エクスポート
    ├── logger.py        # ログ設定
    ├── selenium_helpers.py  # Selenium ヘルパー関数
    ├── tor_helpers.py   # Tor ブラウザ初期化と接続確認
    ├── human_simulation.py # 人間らしい動作シミュレーション
    ├── cookies.py       # クッキー管理
    ├── data_storage.py  # データ保存ユーティリティ
    ├── text_processing.py # テキスト処理ユーティリティ
    ├── x_helpers.py     # X (Twitter) 固有ヘルパー
    ├── anti_detection.py # 検出回避機能
    ├── selectors.py     # 要素セレクターユーティリティ
    └── decorators.py    # ユーティリティデコレーター

docker/
├── development/         # 開発環境
└── production/          # 本番環境

data/                    # データ出力ディレクトリ（自動作成）
├── scraping_results/    # スクレイピング結果
├── screenshots/         # デバッグ用スクリーンショット
├── logs/               # ログファイル
├── cookies/            # セッションクッキー
└── coverage/           # テストカバレッジ
```

## コマンド

### 開発コマンド

```bash
# 開発環境
make dev                # 開発モードで実行（2FA入力対応）
make dev-rebuild        # 強制リビルドして実行
make dev-background     # バックグラウンドで実行
make test-docker        # Docker環境でテストを実行
make test-permissions   # Docker権限テストを実行

# ローカル開発
make test              # テストを実行
make lint              # コードリンティング
make format            # コードフォーマット
make fix               # 自動修正
make check             # リント + テスト

# データ管理
make clean-data        # データディレクトリをクリア
make reset-data        # データディレクトリを再作成
```

### 本番コマンド

```bash
make build-prod        # 本番用イメージをビルド
make run-prod          # 本番環境で実行
make prod              # ビルド + 実行（エイリアス）
```

## 設定

### 環境変数

`.env` ファイルをプロジェクトルートに作成：

```env
# X (Twitter) スクレイパー設定
# Tor Browser 設定
TOR_BROWSER_PATH=/Applications/Tor Browser.app
# プラットフォーム別の例:
# Linux: TOR_BROWSER_PATH=/opt/torbrowser
# macOS: TOR_BROWSER_PATH=/Applications/Tor Browser.app
# Docker: TOR_BROWSER_PATH=/opt/torbrowser

# X (Twitter) ログイン認証情報（オプション）
# ログイン機能を使用する場合のみ設定
X_EMAIL=your-email@example.com
X_PASSWORD=your-password
X_USERNAME=your-username

# ログ設定（オプション）
LOG_LEVEL=INFO
# オプション: DEBUG, INFO, WARNING, ERROR, CRITICAL

# スクレイパー設定（オプション）
HEADLESS=true
USE_STEM=false
SOCKS_PORT=9150    # 標準化されたポート
CONTROL_PORT=9151  # 標準化されたポート
```

### 複数アカウント設定

JSON形式での複数アカウント設定：

```env
# 複数アカウント設定（JSON形式）
X_ACCOUNTS_JSON='[
  {
    "email": "account1@example.com",
    "username": "user1",
    "password": "password1"
  },
  {
    "email": "account2@example.com", 
    "username": "user2",
    "password": "password2"
  }
]'
```

### Tor Browser パス

スクレイパーは一般的な場所で Tor Browser を自動検索します：

- **Linux**: `/opt/torbrowser`, `/usr/local/bin/tor-browser`
- **macOS**: `/Applications/Tor Browser.app`
- **Windows**: `C:\Users\{user}\Desktop\Tor Browser`
- **Docker**: `/opt/torbrowser`

## 機能詳細

### ログイン機能

- **マルチステップログインフロー**: ユーザー名/メール → 異常なアクティビティ確認 → パスワード → 2FA
- **二要素認証対応**: メール認証とアプリ認証の両方をサポート
- **セッション管理**: クッキーの永続化で再ログインを回避
- **エラーハンドリング**: 包括的なリトライ機構

### 検出回避機能

- **人間らしい入力**: 文字毎のタイピング遅延
- **ランダム遅延**: アクション間の自然な間隔
- **User-Agent ローテーション**: 検出を回避
- **JavaScriptによる要素操作**: 無効化された要素への対応

### データ管理

- **構造化保存**: データタイプ別の自動分類
- **メタデータ追跡**: スクレイピングセッションの詳細記録
- **バックアップ機能**: 重要なデータの自動バックアップ
- **Cookie管理**: セッション状態の永続化

## トラブルシューティング

### よくある問題

#### 1. Tor 接続エラー

```bash
# Tor の状態を確認
make shell
curl --socks5 localhost:9150 http://httpbin.org/ip
```

#### 2. ファイル権限エラー

```bash
# 権限テストを実行
make test-permissions

# データディレクトリをリセット
make reset-data
```

#### 3. 2FA 入力の問題

```bash
# インタラクティブモードで実行
make dev
```

#### 4. ログイン失敗

- **CAPTCHA**: 手動ログインフローを使用
- **認証情報確認**: 環境変数の設定を確認
- **レート制限**: 適切な間隔を空けて再試行

### デバッグ機能

- **自動スクリーンショット**: エラー時の画面キャプチャ
- **HTMLソース保存**: デバッグ用のページソース
- **詳細ログ**: 各ステップの詳細な実行ログ
- **メタデータ記録**: エラー発生時の詳細情報

## 要件

- Python 3.12+
- Docker & Docker Compose
- 1GB RAM 最小（2GB 推奨）
- Tor Browser（ローカル実行時）

## Contributing

1. リポジトリをフォーク
2. 機能ブランチを作成
3. 変更を実装
4. テストとリンティングを実行
5. プルリクエストを提出

## ライセンス

MIT License

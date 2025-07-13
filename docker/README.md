# Docker 環境での Tor-Selenium-X

## 🔧 基本使用方法

```bash
# 開発モードで実行（2FA入力対応）
make dev

# テストを実行
make test-docker

# 権限テストを実行
make test-permissions
```

> **注意**: ファイル権限とディレクトリ作成は自動処理されます。

## 📁 ディレクトリ構造

```
tor-selenium-x/
├── data/                       # データ出力（自動作成）
│   ├── scraping_results/       # JSON ファイル
│   ├── logs/                   # ログファイル
│   ├── screenshots/            # スクリーンショット
│   └── cookies/                # セッションクッキー
```

## 🐳 よく使うコマンド

| コマンド | 説明 |
|---------|------|
| `make dev` | 開発モード実行 |
| `make test-docker` | テスト実行 |
| `make shell` | コンテナ内シェル |
| `make logs` | ログ表示 |
| `make clean` | クリーンアップ |

## 🔍 トラブルシューティング

**2FA 入力の問題**: `make dev` でインタラクティブモード実行

**ファイル保存エラー**: `make test-permissions` で権限確認

**Tor 接続問題**: `make shell` → `curl --socks5 localhost:9150 http://httpbin.org/ip`

## 📋 環境変数

```bash
# Tor Browser パス（自動設定）
TOR_BROWSER_PATH=/opt/torbrowser

# X ログイン情報（オプション）
X_EMAIL=your_email@example.com
X_USERNAME=your_username  
X_PASSWORD=your_password
```
 

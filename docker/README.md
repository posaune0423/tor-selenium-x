# Docker 環境での Tor-Selenium-X

## 概要

このプロジェクトは、Tor Browser と Selenium を使用したプライベートな X (Twitter) スクレイピングツールです。Docker を使用して、一貫性のある実行環境を提供します。

## Docker 環境の種類

### 開発環境 (Development)
- **用途**: 開発・デバッグ・テスト
- **特徴**: ソースコードをボリュームマウント、インタラクティブ対応
- **場所**: `docker/development/`

### 本番環境 (Production)  
- **用途**: 実際のデータ収集・運用
- **特徴**: 最適化されたイメージ、セキュリティ強化
- **場所**: `docker/production/`

## 🔧 使用方法

### 基本的な実行方法

```bash
# 開発モードで実行（2FA入力対応）
make dev

# バックグラウンドで実行
make dev-background

# テストを実行
make test-docker

# 権限テストを実行
make test-permissions
```

> **注意**: ファイル権限とディレクトリ作成は自動で処理されます。

## 📁 ファイル保存について

### 自動解決される権限問題

以前のバージョンで発生していた以下のエラーは自動で解決されます：

```
Failed to save tweets: [Errno 2] No such file or directory: 'data/scraping_results/search_results_Python_programming.json'
```

**解決方法**:
1. **XScraperでの自動ディレクトリ作成**: 保存メソッド内で`self.data_dir.mkdir(parents=True, exist_ok=True)`を実行
2. **Makefileでの事前ディレクトリ作成**: Docker実行前に`mkdir -p data/scraping_results`を実行
3. **Docker権限の自動設定**: 実行時に`USER_ID`と`GROUP_ID`を自動設定

### ディレクトリ構造

```
tor-selenium-x/
├── data/                       # データ出力ディレクトリ（自動作成）
│   ├── data/                   # JSON ファイル保存先
│   ├── logs/                   # ログファイル
│   ├── screenshots/            # スクリーンショット
│   └── coverage/               # テストカバレッジ
```

## 🐳 Docker コマンド一覧

### 開発環境

| コマンド | 説明 |
|---------|------|
| `make build` | Docker イメージをビルド |
| `make dev` | 開発モードで実行（2FA入力対応） |
| `make dev-rebuild` | 強制リビルドして実行 |
| `make dev-background` | バックグラウンドで実行 |
| `make test-docker` | Docker環境でテストを実行 |
| `make test-permissions` | 権限テストを実行 |
| `make logs` | コンテナのログを表示 |
| `make shell` | コンテナ内でシェルを開く |
| `make stop` | 実行中のコンテナを停止 |
| `make clean` | イメージとコンテナを削除 |

### 本番環境

| コマンド | 説明 |
|---------|------|
| `make build-prod` | 本番用イメージをビルド |
| `make run-prod` | 本番環境で実行 |
| `make logs-prod` | 本番環境のログを表示 |
| `make shell-prod` | 本番環境でシェルを開く |

## 🔍 トラブルシューティング

### 1. ファイル保存エラー（稀なケース）

**エラー**: `Failed to save tweets: [Errno 2] No such file or directory`

**解決手順**:
```bash
# 1. 権限テストを実行
make test-permissions

# 2. 再ビルドして実行
make dev-rebuild
```

### 2. 2FA 入力の問題

**問題**: Two-Factor Authentication (2FA) の入力ができない

**解決策**: 
```bash
# インタラクティブモードで実行
make dev
```

### 3. Tor 接続の問題

**問題**: Tor接続が確立できない

**解決策**:
```bash
# コンテナ内でTor状態を確認
make shell
curl --socks5 localhost:9050 http://httpbin.org/ip
```

## 🧪 テスト

### 権限テスト

Docker環境での**ファイル保存と権限**をテストする専用テストが用意されています：

```bash
# 権限テストを実行
make test-permissions

# 個別のテストを実行（ローカル環境）
pytest tests/test_docker_file_permissions.py -v
```

**テスト内容**:
- ディレクトリ作成権限
- ファイル書き込み権限  
- ボリュームマウントの動作
- ユーザー権限の確認
- XScraper のファイル保存機能

## 📋 環境変数

### 必須の環境変数

```bash
# Tor Browser パス（Docker内では自動設定）
export TOR_BROWSER_PATH=/opt/torbrowser

# X (Twitter) ログイン情報（オプション）
export X_EMAIL=your_email@example.com
export X_USERNAME=your_username  
export X_PASSWORD=your_password
```

### Docker 内部環境変数（自動設定）

```bash
# Python 関連
PYTHONUNBUFFERED=1
PYTHONPATH=/app

# Tor Browser 関連
TBB_PATH=/opt/torbrowser
TBSELENIUM_TBB_PATH=/opt/torbrowser

# ディスプレイ設定
DISPLAY=:99

# 権限設定（自動）
USER_ID=<host user id>
GROUP_ID=<host group id>
```

## 🔒 セキュリティ

### データ保護

- **Tor ネットワーク**: すべての通信が Tor 経由で匿名化
- **コンテナ分離**: アプリケーションがホストから分離
- **権限最小化**: 非root ユーザーでアプリケーションを実行

### 注意事項

- `.env` ファイルには機密情報を含むため、バージョン管理に含めない
- X (Twitter) の利用規約を遵守してください
- レート制限を守り、適切な間隔でリクエストを送信してください

## 📚 参考情報

### 関連ファイル

- `docker/development/Dockerfile` - 開発環境 Docker 設定
- `docker/development/docker-compose.yml` - 開発環境 Compose 設定
- `docker/development/docker-entrypoint.sh` - コンテナ起動スクリプト
- `tests/test_docker_file_permissions.py` - 権限テストファイル

### プロジェクト構造

```
docker/
├── development/                # 開発環境
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-entrypoint.sh
├── production/                 # 本番環境
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-entrypoint.sh
└── README.md                   # このファイル
```

---

## 🆘 サポート

問題が発生した場合は、以下の順序で確認してください：

1. **権限設定**: `make setup-permissions` を実行
2. **環境変数**: `USER_ID` と `GROUP_ID` が設定されているか確認
3. **テスト実行**: `make test-permissions` で権限テストを実行
4. **ログ確認**: `make logs` でエラーログを確認
5. **シェル確認**: `make shell` でコンテナ内の状態を直接確認 

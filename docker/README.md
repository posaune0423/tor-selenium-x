# Docker環境でのTor Selenium X Scraper

このディレクトリには、Tor Selenium X Scraperをコンテナ環境で実行するためのDocker設定が含まれています。

## 🚀 新機能

- **tbselenium統合**: 安定性と保守性を向上させるためtbseleniumライブラリを使用
- **Tor Browser Bundle**: 実際のTor Browserを使用してより信頼性の高いスクレイピング
- **自動Tor管理**: tbseleniumが内部でTorプロセスを管理
- **ヘッドレス実行**: Xvfbを使用したGUIなし実行

## 📋 前提条件

- Docker 20.10+
- Docker Compose 2.0+
- 最低2GB RAM（推奨4GB）

## 🏗️ ビルドと実行

### 基本的な実行

```bash
# イメージをビルドして実行
docker-compose up --build

# バックグラウンドで実行
docker-compose up -d --build
```

### 開発環境での実行

```bash
# 開発用プロファイル（インタラクティブ）
docker-compose --profile dev up tor-scraper-dev

# または直接実行
docker-compose run --rm tor-scraper-dev
```

### テスト実行

```bash
# テストスイート実行
docker-compose --profile test up tor-scraper-test

# カバレッジレポート生成
docker-compose --profile test run --rm tor-scraper-test
```

### 一回限りのデータ収集

```bash
# 一回だけスクレイピング実行
docker-compose --profile once up tor-scraper-once
```

## 📁 ボリュームマウント

| ホストパス | コンテナパス | 説明 |
|-----------|------------|-----|
| `../data` | `/app/data` | スクレイピングデータの保存先 |
| `../logs` | `/app/logs` | ログファイルの出力先 |
| `../src` | `/app/src` | ソースコード（開発時） |
| `../tests` | `/app/tests` | テストファイル |
| `../htmlcov` | `/app/htmlcov` | カバレッジレポート |

## 🔧 環境変数

| 変数名 | デフォルト値 | 説明 |
|-------|------------|-----|
| `TBB_PATH` | `/opt/torbrowser/tor-browser` | Tor Browser Bundleのパス |
| `DISPLAY` | `:99` | Xvfbディスプレイ番号 |
| `PYTHONUNBUFFERED` | `1` | Pythonバッファリング無効化 |
| `PYTHONPATH` | `/app` | Pythonモジュール検索パス |
| `TBSELENIUM_TBB_PATH` | `/opt/torbrowser/tor-browser` | tbselenium用TBBパス |

## 🎯 使用例

### 1. 開発用途

```bash
# コンテナに入ってインタラクティブに開発
docker-compose run --rm tor-scraper-dev bash

# 特定のスクリプトを実行
docker-compose run --rm tor-scraper-dev uv run src/main.py
```

### 2. 自動化スクリプト

```bash
# crontabで定期実行する場合
0 */6 * * * cd /path/to/project && docker-compose --profile once up tor-scraper-once
```

### 3. CI/CD統合

```bash
# GitHub Actionsなどで使用
docker-compose --profile test run --rm tor-scraper-test
```

## 🔍 トラブルシューティング

### よくある問題

#### 1. Tor Browser Bundle のダウンロードに失敗

```bash
# 手動でTBBを配置する場合
mkdir -p /opt/torbrowser
# TBBを/opt/torbrowser/tor-browserに配置
```

#### 2. メモリ不足

```yaml
# docker-compose.ymlでメモリ制限を調整
mem_limit: 4g  # 2gから4gに増加
```

#### 3. 権限エラー

```bash
# ログとデータディレクトリの権限確認
sudo chown -R 1000:1000 data/ logs/
```

#### 4. tbseleniumエラー

```bash
# コンテナ内でTBBパスを確認
docker-compose run --rm tor-scraper-dev ls -la $TBB_PATH
```

### ログの確認

```bash
# リアルタイムログ
docker-compose logs -f tor-scraper

# 特定サービスのログ
docker-compose logs tor-scraper-dev

# ログファイル確認
ls -la logs/
```

### ヘルスチェック

```bash
# サービス状態確認
docker-compose ps

# ヘルスチェック詳細
docker inspect tor-selenium-scraper | jq '.[0].State.Health'
```

## 🚨 セキュリティ注意事項

1. **非rootユーザー**: コンテナは`appuser`（UID: 1000）で実行
2. **読み取り専用マウント**: 本番環境ではソースコードを`:ro`でマウント
3. **ネットワーク分離**: 必要に応じてDockerネットワークを分離
4. **シークレット管理**: API キーなどは環境変数やDocker secretsを使用

## 📊 モニタリング

### リソース使用量確認

```bash
# コンテナのリソース使用量
docker stats tor-selenium-scraper

# システムリソース確認
docker system df
```

### パフォーマンス調整

```yaml
# docker-compose.ymlでの調整例
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

## 🔄 更新とメンテナンス

```bash
# イメージ再ビルド
docker-compose build --no-cache

# 不要なイメージとボリューム削除
docker system prune -f

# 開発依存関係の更新
docker-compose run --rm tor-scraper-dev uv lock --upgrade
```

## 📈 スケーリング

複数インスタンスでの並列実行：

```bash
# 3つのインスタンスで並列実行
docker-compose up --scale tor-scraper=3
```

環境変数でインスタンス固有の設定：

```yaml
environment:
  - INSTANCE_ID=${INSTANCE_ID:-1}
  - SEARCH_QUERY=${SEARCH_QUERY:-Python}
``` 

.PHONY: help build run dev dev-rebuild dev-background dev-logs test test-docker clean logs shell stop install format lint fix check build-prod run-prod dev-prod logs-prod shell-prod stop-prod clean-prod

# デフォルトターゲット
help:
	@echo "Available commands:"
	@echo ""
	@echo "🐳 Docker Commands (Development):"
	@echo "  build          - Docker イメージをビルド (開発環境)"
	@echo "  run            - Tor Scraper を実行 (開発環境)"
	@echo "  dev            - 開発モードで実行（2FA入力対応）"
	@echo "  dev-rebuild    - 開発モードで実行（強制リビルド）"
	@echo "  dev-background - 開発モードで実行（バックグラウンド）"
	@echo "  dev-logs       - 開発モードで実行（ログ表示のみ）"
	@echo "  test-docker    - Docker環境でテストを実行"
	@echo "  logs           - コンテナのログを表示 (開発環境)"
	@echo "  shell          - コンテナ内でシェルを開く (開発環境)"
	@echo "  stop           - 実行中のコンテナを停止 (開発環境)"
	@echo "  clean          - Docker イメージとコンテナを削除 (開発環境)"
	@echo ""
	@echo "🚀 Docker Commands (Production):"
	@echo "  build-prod - Docker イメージをビルド (本番環境)"
	@echo "  run-prod   - Tor Scraper を実行 (本番環境)"
	@echo "  logs-prod  - コンテナのログを表示 (本番環境)"
	@echo "  shell-prod - コンテナ内でシェルを開く (本番環境)"
	@echo "  stop-prod  - 実行中のコンテナを停止 (本番環境)"
	@echo "  clean-prod - Docker イメージとコンテナを削除 (本番環境)"
	@echo ""
	@echo "🧪 Development Commands:"
	@echo "  install    - 依存関係をインストール"
	@echo "  test       - ローカルでテストを実行"
	@echo "  format     - コードをフォーマット (Ruff)"
	@echo "  lint       - リンターを実行 (Ruff)"
	@echo "  fix        - 自動修正を実行 (Ruff)"
	@echo "  check      - lint + test を実行"
	@echo ""
	@echo "💡 Usage Tips:"
	@echo "  - 2FA入力が必要な場合は 'make dev' を使用"
	@echo "  - バックグラウンド実行は 'make dev-background'"
	@echo "  - ログ確認のみは 'make dev-logs'"

# ====================
# Development Environment
# ====================

# Docker イメージをビルド (開発環境)
build:
	docker-compose -f docker/development/docker-compose.yml build

# Tor Scraper を実行 (開発環境)
run:
	docker-compose -f docker/development/docker-compose.yml up --build tor-scraper

# 開発モードで実行（インタラクティブ対応）
dev:
	docker-compose -f docker/development/docker-compose.yml --profile dev run --rm tor-scraper-dev

# 開発モードで実行（強制リビルド）
dev-rebuild:
	docker-compose -f docker/development/docker-compose.yml --profile dev run --rm --build tor-scraper-dev

# 開発モードで実行（バックグラウンド）
dev-background:
	docker-compose -f docker/development/docker-compose.yml --profile dev up -d tor-scraper-dev

# 開発モードで実行（ログ表示、インタラクティブなし）
dev-logs:
	docker-compose -f docker/development/docker-compose.yml --profile dev up tor-scraper-dev

# Docker環境でテストを実行
test-docker:
	docker-compose -f docker/development/docker-compose.yml --profile test up --build tor-scraper-test

# コンテナのログを表示 (開発環境)
logs:
	docker-compose -f docker/development/docker-compose.yml logs -f tor-scraper

# コンテナ内でシェルを開く (開発環境)
shell:
	docker-compose -f docker/development/docker-compose.yml exec tor-scraper /bin/bash

# 実行中のコンテナを停止 (開発環境)
stop:
	docker-compose -f docker/development/docker-compose.yml down

# Docker イメージとコンテナを削除 (開発環境)
clean:
	docker-compose -f docker/development/docker-compose.yml down --rmi all --volumes --remove-orphans
	docker system prune -f

# ====================
# Production Environment
# ====================

# Docker イメージをビルド (本番環境)
build-prod:
	docker-compose -f docker/production/docker-compose.yml build

# Tor Scraper を実行 (本番環境)
run-prod:
	docker-compose -f docker/production/docker-compose.yml up --build tor-scraper

# コンテナのログを表示 (本番環境)
logs-prod:
	docker-compose -f docker/production/docker-compose.yml logs -f tor-scraper

# コンテナ内でシェルを開く (本番環境)
shell-prod:
	docker-compose -f docker/production/docker-compose.yml exec tor-scraper /bin/bash

# 実行中のコンテナを停止 (本番環境)
stop-prod:
	docker-compose -f docker/production/docker-compose.yml down

# Docker イメージとコンテナを削除 (本番環境)
clean-prod:
	docker-compose -f docker/production/docker-compose.yml down --rmi all --volumes --remove-orphans

# ====================
# Local Development
# ====================

# ローカルでテストを実行
test:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# ローカル開発環境のセットアップ
install:
	uv sync --all-extras

# 開発用依存関係も含めてインストール
dev-install:
	uv sync --extra dev --extra selenium

# コードフォーマット
format:
	uv run ruff format src tests

# リンター実行
lint:
	uv run ruff check src tests

# 自動修正
fix:
	uv run ruff check --fix src tests

# すべてのチェックを実行
check: lint test

# 依存関係の更新
update:
	uv lock --upgrade
	uv sync --all-extras

# プロジェクトのクリーンアップ
clean-local:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .ruff_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Railway デプロイメント情報
railway-info:
	@echo ""
	@echo "🚂 Railway デプロイメント手順:"
	@echo ""
	@echo "1. GitHubリポジトリをRailwayに接続"
	@echo "2. 環境変数を設定:"
	@echo "   - TBB_PATH=/opt/torbrowser/tor-browser"
	@echo "   - DISPLAY=:99"
	@echo "   - PYTHONPATH=/app"
	@echo "3. 自動デプロイが開始されます"
	@echo ""
	@echo "📋 必要な環境変数:"
	@echo "   TBB_PATH, DISPLAY, PYTHONPATH"

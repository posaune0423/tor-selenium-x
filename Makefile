.PHONY: help build run dev test test-docker clean logs shell stop install format lint check

# デフォルトターゲット
help:
	@echo "Available commands:"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  build      - Docker イメージをビルド"
	@echo "  run        - Tor Scraper を実行"
	@echo "  dev        - 開発モードで実行"
	@echo "  test-docker- Docker環境でテストを実行"
	@echo "  logs       - コンテナのログを表示"
	@echo "  shell      - コンテナ内でシェルを開く"
	@echo "  stop       - 実行中のコンテナを停止"
	@echo "  clean      - Docker イメージとコンテナを削除"
	@echo ""
	@echo "🧪 Development Commands:"
	@echo "  install    - 依存関係をインストール"
	@echo "  test       - ローカルでテストを実行"
	@echo "  format     - コードをフォーマット"
	@echo "  lint       - リンターを実行"
	@echo "  check      - lint + test を実行"

# ログディレクトリを作成
logs-dir:
	mkdir -p logs

# Docker イメージをビルド
build: logs-dir
	docker-compose -f docker/docker-compose.yml build

# Tor Scraper を実行
run: logs-dir
	docker-compose -f docker/docker-compose.yml up --build tor-scraper

# 開発モードで実行
dev: logs-dir
	docker-compose -f docker/docker-compose.yml --profile dev up --build tor-scraper-dev

# Docker環境でテストを実行
test-docker: logs-dir
	docker-compose -f docker/docker-compose.yml --profile test up --build tor-scraper-test

# ローカルでテストを実行
test:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# コンテナのログを表示
logs:
	docker-compose -f docker/docker-compose.yml logs -f tor-scraper

# コンテナ内でシェルを開く
shell:
	docker-compose -f docker/docker-compose.yml exec tor-scraper /bin/bash

# 実行中のコンテナを停止
stop:
	docker-compose -f docker/docker-compose.yml down

# Docker イメージとコンテナを削除
clean:
	docker-compose -f docker/docker-compose.yml down --rmi all --volumes --remove-orphans
	docker system prune -f

# ローカル開発環境のセットアップ
install:
	uv sync --all-extras

# 開発用依存関係も含めてインストール
dev-install:
	uv sync --extra dev --extra selenium

# コードフォーマット
format:
	uv run black src tests
	uv run isort src tests

# リンター実行
lint:
	uv run ruff check src tests
	uv run mypy src

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
	rm -rf .mypy_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

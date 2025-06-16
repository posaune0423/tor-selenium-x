.PHONY: help build run dev test clean logs shell stop

# デフォルトターゲット
help:
	@echo "Available commands:"
	@echo "  build      - Docker イメージをビルド"
	@echo "  run        - Tor Scraper を実行"
	@echo "  dev        - 開発モードで実行"
	@echo "  test       - テストを実行"
	@echo "  clean      - Docker イメージとコンテナを削除"
	@echo "  logs       - コンテナのログを表示"
	@echo "  shell      - コンテナ内でシェルを開く"
	@echo "  stop       - 実行中のコンテナを停止"

# Docker イメージをビルド
build:
	docker-compose -f docker/docker-compose.yml build

# Tor Scraper を実行
run:
	docker-compose -f docker/docker-compose.yml up --build tor-scraper

# 開発モードで実行
dev:
	docker-compose -f docker/docker-compose.yml --profile dev up --build tor-scraper-dev

# テストを実行
test:
	uv run pytest

# Docker イメージとコンテナを削除
clean:
	docker-compose -f docker/docker-compose.yml down --rmi all --volumes --remove-orphans
	docker system prune -f

# コンテナのログを表示
logs:
	docker-compose -f docker/docker-compose.yml logs -f tor-scraper

# コンテナ内でシェルを開く
shell:
	docker-compose -f docker/docker-compose.yml exec tor-scraper /bin/bash

# 実行中のコンテナを停止
stop:
	docker-compose -f docker/docker-compose.yml down

# ローカル開発用
install:
	uv sync --extra dev --extra selenium

format:
	uv run black src tests
	uv run isort src tests

lint:
	uv run ruff check src tests
	uv run mypy src

# すべてのチェックを実行
check: lint test

# ログディレクトリを作成
logs-dir:
	mkdir -p logs
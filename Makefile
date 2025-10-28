.PHONY: build run stop logs shell login clean help check-env all

# Docker compose command
DOCKER_COMPOSE := docker-compose
SERVICE := userbot

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)╔═══════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║  Telegram Auto-Reaction Bot - Makefile Commands      ║$(NC)"
	@echo "$(BLUE)╚═══════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Installation:$(NC)"
	@echo "  make install       - Install Python dependencies locally"
	@echo ""
	@echo "$(GREEN)Docker Commands:$(NC)"
	@echo "  make build         - Build Docker image"
	@echo "  make run           - Start bot in background"
	@echo "  make stop          - Stop bot container"
	@echo "  make restart       - Restart bot"
	@echo "  make logs          - View bot logs (follow mode)"
	@echo "  make shell         - Open shell in container"
	@echo ""
	@echo "$(GREEN)Session Management:$(NC)"
	@echo "  make login         - Interactive Telegram login (first time setup)"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean         - Remove all Docker resources"
	@echo "  make clean-logs    - Clear Docker logs"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make dev           - Start bot in development mode (foreground)"
	@echo "  make format        - Format Python code with black"
	@echo "  make lint          - Lint code with pylint"
	@echo ""
	@echo "$(GREEN)Utils:$(NC)"
	@echo "  make check-env     - Verify .env file exists"
	@echo "  make info          - Show bot configuration"
	@echo "  make help          - Show this help message"
	@echo ""

# Installation
install:
	@echo "$(BLUE)📦 Installing Python dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed!$(NC)"

# Docker commands
build: check-env
	@echo "$(BLUE)🔨 Building Docker image...$(NC)"
	@$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✅ Image built successfully!$(NC)"

run: check-env
	@echo "$(BLUE)🚀 Starting bot...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Bot started! Run '$(YELLOW)make logs$(GREEN)' to view logs.$(NC)"

stop:
	@echo "$(BLUE)🛑 Stopping bot...$(NC)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Bot stopped!$(NC)"

restart: stop run
	@echo "$(GREEN)✅ Bot restarted!$(NC)"

logs:
	@echo "$(BLUE)📋 Following bot logs (Ctrl+C to exit)...$(NC)"
	@$(DOCKER_COMPOSE) logs -f $(SERVICE)

shell:
	@echo "$(BLUE)🐚 Opening shell in container...$(NC)"
	@$(DOCKER_COMPOSE) exec $(SERVICE) /bin/bash

# Session management
login: check-env
	@echo "$(BLUE)🔐 Starting Telegram login session...$(NC)"
	@echo "$(YELLOW)⚠️  This will create a new session file.$(NC)"
	@echo "$(YELLOW)⚠️  Enter your phone number when prompted.$(NC)"
	@$(DOCKER_COMPOSE) run --rm -it $(SERVICE) python -c "from telethon import TelegramClient; from src.config import *; import asyncio; TelegramClient(SESSION_NAME, API_ID, API_HASH).start(phone=PHONE_NUMBER); print('$(GREEN)✅ Session created!$(NC)')"

# Cleanup
clean: stop
	@echo "$(BLUE)🗑️  Cleaning Docker resources...$(NC)"
	@$(DOCKER_COMPOSE) down -v --rmi local
	@echo "$(GREEN)✅ Cleanup completed!$(NC)"

clean-logs:
	@echo "$(BLUE)🗑️  Clearing Docker logs...$(NC)"
	@docker system prune -f --filter "until=24h"
	@echo "$(GREEN)✅ Logs cleared!$(NC)"

# Development
dev: check-env
	@echo "$(BLUE)💻 Starting bot in development mode (foreground)...$(NC)"
	@$(DOCKER_COMPOSE) up $(SERVICE)

format:
	@echo "$(BLUE)✨ Formatting Python code...$(NC)"
	@black src/ main.py
	@echo "$(GREEN)✅ Code formatted!$(NC)"

lint:
	@echo "$(BLUE)🔍 Linting code...$(NC)"
	@pylint src/ main.py || true
	@echo "$(GREEN)✅ Lint complete!$(NC)"

# Utilities
check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)❌ Error: .env file not found!$(NC)"; \
		echo "$(YELLOW)📝 Please create .env file from .env example:$(NC)"; \
		echo "$(BLUE)   API_ID=your_api_id$(NC)"; \
		echo "$(BLUE)   API_HASH=your_api_hash$(NC)"; \
		echo "$(BLUE)   PHONE_NUMBER=+1234567890$(NC)"; \
		echo "$(BLUE)   CHAT_ID=-1002749060046$(NC)"; \
		echo "$(BLUE)   TOPIC_ID=2$(NC)"; \
		echo "$(BLUE)   SESSION_NAME=userbot$(NC)"; \
		exit 1; \
	fi

info:
	@echo "$(BLUE)ℹ️  Bot Configuration:$(NC)"
	@echo "$(GREEN)Session file directory:$(NC) sessions/"
	@echo "$(GREEN)Source directory:$(NC) src/"
	@echo "$(GREEN)Main file:$(NC) main.py"
	@echo "$(GREEN)Requirements:$(NC) requirements.txt"
	@echo ""
	@echo "$(BLUE)From .env file:$(NC)"
	@grep -v '^#' .env | grep -v '^$$' | sed 's/^/  /'

# Default action
.DEFAULT_GOAL := help

# Run all steps: check env, build, run
all: check-env build run
	@echo "$(GREEN)✅ All done! Bot is running!$(NC)"
	@echo "$(YELLOW)View logs with: make logs$(NC)"
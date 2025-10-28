.PHONY: build run stop logs shell login clean help check-env all install dev format lint info clean-logs restart enable disable status

# Docker compose command
DOCKER_COMPOSE := docker compose
SERVICE := telegram-bot-system

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
CYAN := \033[0;36m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)╔════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║  Telegram Auto-Reaction Bot System - Makefile         ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(CYAN)🚀 QUICK START:$(NC)"
	@echo "  make setup         - First time setup (build + login)"
	@echo "  make start         - Start the system"
	@echo ""
	@echo "$(GREEN)📦 Setup & Installation:$(NC)"
	@echo "  make install       - Install Python dependencies locally"
	@echo "  make check-env     - Verify .env file exists"
	@echo ""
	@echo "$(GREEN)🐳 Docker Commands:$(NC)"
	@echo "  make build         - Build Docker image"
	@echo "  make start         - Start bots (background)"
	@echo "  make stop          - Stop bots"
	@echo "  make restart       - Restart bots"
	@echo "  make logs          - View logs (follow mode)"
	@echo "  make shell         - Open shell in container"
	@echo ""
	@echo "$(GREEN)🔐 Session Management:$(NC)"
	@echo "  make login         - Interactive Telegram login (creates session)"
	@echo ""
	@echo "$(GREEN)🎮 Bot Control (via commands):$(NC)"
	@echo "  make bot-enable    - Enable userbot (send /enable to bot)"
	@echo "  make bot-disable   - Disable userbot (send /disable to bot)"
	@echo "  make bot-status    - Check userbot status (send /status to bot)"
	@echo ""
	@echo "$(GREEN)💻 Development:$(NC)"
	@echo "  make dev           - Start in development mode (foreground)"
	@echo "  make format        - Format Python code with black"
	@echo "  make lint          - Lint code with pylint"
	@echo ""
	@echo "$(GREEN)🗑️  Cleanup:$(NC)"
	@echo "  make clean         - Remove all Docker resources"
	@echo "  make clean-logs    - Clear Docker logs"
	@echo "  make clean-session - Remove session files (forces re-login)"
	@echo ""
	@echo "$(GREEN)ℹ️  Utils:$(NC)"
	@echo "  make info          - Show bot configuration"
	@echo "  make ps            - Show running containers"
	@echo "  make help          - Show this help message"
	@echo ""
	@echo "$(YELLOW)📝 SETUP STEPS:$(NC)"
	@echo "  1. Create .env file with your credentials"
	@echo "  2. Run: $(CYAN)make setup$(NC)"
	@echo "  3. Use /enable and /disable commands in bot"
	@echo ""

# Quick setup
setup: check-env build login start
	@echo ""
	@echo "$(GREEN)✅ Setup completed!$(NC)"
	@echo "$(CYAN)Your bot system is ready!$(NC)"
	@echo ""
	@echo "$(YELLOW)Send commands to your bot:$(NC)"
	@echo "  /enable  - Enable userbot (puts ❤️ reactions)"
	@echo "  /disable - Disable userbot"
	@echo "  /status  - Check current status"
	@echo ""

# Installation
install:
	@echo "$(BLUE)📦 Installing Python dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed!$(NC)"

# Docker commands
build: check-env
	@echo "$(BLUE)🔨 Building Docker image...$(NC)"
	@$(DOCKER_COMPOSE) build --no-cache
	@echo "$(GREEN)✅ Image built successfully!$(NC)"

start: check-env
	@echo "$(BLUE)🚀 Starting bot system...$(NC)"
	@$(DOCKER_COMPOSE) up -d $(SERVICE)
	@echo "$(GREEN)✅ Bot system started!$(NC)"
	@echo "$(CYAN)Available commands:$(NC)"
	@echo "  - make logs        View logs"
	@echo "  - make stop        Stop system"
	@echo "  - make shell       Open shell"

stop:
	@echo "$(BLUE)🛑 Stopping bot system...$(NC)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Bot system stopped!$(NC)"

restart: stop start
	@echo "$(GREEN)✅ Bot system restarted!$(NC)"

logs:
	@echo "$(BLUE)📋 Following bot logs (Ctrl+C to exit)...$(NC)"
	@$(DOCKER_COMPOSE) logs -f $(SERVICE)

shell:
	@echo "$(BLUE)🐚 Opening shell in container...$(NC)"
	@$(DOCKER_COMPOSE) exec $(SERVICE) /bin/bash

ps:
	@echo "$(BLUE)🔍 Running containers:$(NC)"
	@docker ps -f "name=$(SERVICE)"

# Session management - Interactive login in container
login: check-env build
	@echo "$(BLUE)🔐 Starting Telegram interactive login...$(NC)"
	@echo "$(YELLOW)⚠️  You will be prompted for your phone number and 2FA code.$(NC)"
	@echo "$(YELLOW)⚠️  This will create sessions/userbot file.$(NC)"
	@echo ""
	@$(DOCKER_COMPOSE) run --rm -it $(SERVICE) python -m src.login
	@echo ""
	@echo "$(GREEN)✅ Login successful! Session created.$(NC)"
	@echo "$(YELLOW)📌 Now run: make start$(NC)"

# Bot control (informational - actual control via Telegram bot)
bot-enable:
	@echo "$(CYAN)📤 To enable userbot:$(NC)"
	@echo "  Send /enable command to your Telegram bot"
	@echo ""

bot-disable:
	@echo "$(CYAN)📤 To disable userbot:$(NC)"
	@echo "  Send /disable command to your Telegram bot"
	@echo ""

bot-status:
	@echo "$(CYAN)📤 To check status:$(NC)"
	@echo "  Send /status command to your Telegram bot"
	@echo ""

# Cleanup
clean: stop
	@echo "$(BLUE)🗑️  Cleaning Docker resources...$(NC)"
	@$(DOCKER_COMPOSE) down -v --rmi local
	@echo "$(GREEN)✅ Cleanup completed!$(NC)"

clean-logs:
	@echo "$(BLUE)🗑️  Clearing Docker logs...$(NC)"
	@docker system prune -f --filter "until=24h"
	@echo "$(GREEN)✅ Logs cleared!$(NC)"

clean-session:
	@echo "$(BLUE)🗑️  Removing session files...$(NC)"
	@rm -rf sessions/
	@mkdir -p sessions/
	@echo "$(GREEN)✅ Session files removed! Will need to login again.$(NC)"

# Development
dev: check-env
	@echo "$(BLUE)💻 Starting bot system in development mode (foreground)...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	@echo ""
	@$(DOCKER_COMPOSE) up $(SERVICE)

format:
	@echo "$(BLUE)✨ Formatting Python code...$(NC)"
	@python -m black src/ main.py 2>/dev/null || echo "$(YELLOW)⚠️  Install black: pip install black$(NC)"
	@echo "$(GREEN)✅ Code formatted!$(NC)"

lint:
	@echo "$(BLUE)🔍 Linting code...$(NC)"
	@python -m pylint src/ main.py 2>/dev/null || echo "$(YELLOW)⚠️  Install pylint: pip install pylint$(NC)"
	@echo "$(GREEN)✅ Lint complete!$(NC)"

# Utilities
check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)❌ Error: .env file not found!$(NC)"; \
		echo ""; \
		echo "$(YELLOW)📝 Creating .env from template...$(NC)"; \
		echo "API_ID=YOUR_API_ID" > .env; \
		echo "API_HASH=YOUR_API_HASH" >> .env; \
		echo "PHONE_NUMBER=+1234567890" >> .env; \
		echo "BOT_TOKEN=YOUR_BOT_TOKEN" >> .env; \
		echo "CHAT_ID=-1002749060046" >> .env; \
		echo "TOPIC_ID=0" >> .env; \
		echo "SESSION_NAME=userbot" >> .env; \
		echo "IGNORE_OWN_MESSAGES=false" >> .env; \
		echo "IGNORE_BOT_MESSAGES=false" >> .env; \
		echo ""; \
		echo "$(GREEN)✅ .env created! Please edit it with your credentials:$(NC)"; \
		echo "$(CYAN)  nano .env$(NC)"; \
		echo ""; \
		echo "$(YELLOW)Required fields:$(NC)"; \
		echo "  - API_ID: Get from https://my.telegram.org"; \
		echo "  - API_HASH: Get from https://my.telegram.org"; \
		echo "  - PHONE_NUMBER: Your Telegram account phone"; \
		echo "  - BOT_TOKEN: Get from @BotFather"; \
		echo "  - CHAT_ID: Target chat ID"; \
		echo ""; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ .env file found!$(NC)"

info:
	@echo "$(BLUE)ℹ️  Bot System Configuration:$(NC)"
	@echo ""
	@echo "$(GREEN)📁 Project Structure:$(NC)"
	@echo "  main.py                - Entry point (runs both bots)"
	@echo "  src/bot.py             - Regular bot (control interface)"
	@echo "  src/userbot.py         - Userbot (reaction automation)"
	@echo "  src/config.py          - Configuration"
	@echo "  src/login.py           - Login utility"
	@echo "  sessions/              - Session files (persisted)"
	@echo ""
	@echo "$(GREEN)🔧 Environment Variables (.env):$(NC)"
	@grep -v '^#' .env 2>/dev/null | grep -v '^\s*$$' | sed 's/^/  /'
	@echo ""
	@echo "$(GREEN)🐳 Docker Info:$(NC)"
	@echo "  Service: $(SERVICE)"
	@echo "  Compose file: docker-compose.yml"
	@echo "  Dockerfile: Dockerfile"
	@echo ""
	@echo "$(CYAN)📊 Status:$(NC)"
	@$(DOCKER_COMPOSE) ps 2>/dev/null || echo "  $(YELLOW)No containers running$(NC)"

# Default action
.DEFAULT_GOAL := help

# Run all steps: check env, build, login, start
all: check-env build login start
	@echo ""
	@echo "$(GREEN)✅ All done! Bot system is running!$(NC)"
	@echo "$(YELLOW)📖 View logs with: make logs$(NC)"
	@echo "$(YELLOW)🛑 Stop with: make stop$(NC)"
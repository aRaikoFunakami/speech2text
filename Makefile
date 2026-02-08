.PHONY: setup setup-mac setup-linux test run clean help

# OS detection
UNAME_S := $(shell uname -s)

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Install system dependencies + Python packages (auto-detects OS)
ifeq ($(UNAME_S),Darwin)
	@$(MAKE) setup-mac
else ifeq ($(UNAME_S),Linux)
	@$(MAKE) setup-linux
else
	$(error Unsupported OS: $(UNAME_S). Please install ffmpeg and uv manually.)
endif
	@echo ""
	@echo "==> Installing Python dependencies..."
	uv sync
	@echo ""
	@echo "==> Setup complete!"
	@echo "    Set your API key: export OPENAI_API_KEY='your-key'"
	@echo "    Run: uv run speech2text --help"

setup-mac: ## Install system dependencies (macOS)
	@echo "==> macOS detected"
	@if ! command -v brew >/dev/null 2>&1; then \
		echo "Error: Homebrew is not installed. Install it from https://brew.sh"; \
		exit 1; \
	fi
	@if ! command -v ffmpeg >/dev/null 2>&1; then \
		echo "==> Installing ffmpeg..."; \
		brew install ffmpeg; \
	else \
		echo "==> ffmpeg already installed: $$(ffmpeg -version 2>&1 | head -1)"; \
	fi
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "==> Installing uv..."; \
		brew install uv; \
	else \
		echo "==> uv already installed: $$(uv --version)"; \
	fi

setup-linux: ## Install system dependencies (Linux)
	@echo "==> Linux detected"
	@if command -v apt-get >/dev/null 2>&1; then \
		echo "==> Using apt-get..."; \
		if ! command -v ffmpeg >/dev/null 2>&1; then \
			echo "==> Installing ffmpeg..."; \
			sudo apt-get update && sudo apt-get install -y ffmpeg; \
		else \
			echo "==> ffmpeg already installed: $$(ffmpeg -version 2>&1 | head -1)"; \
		fi; \
	elif command -v dnf >/dev/null 2>&1; then \
		echo "==> Using dnf..."; \
		if ! command -v ffmpeg >/dev/null 2>&1; then \
			echo "==> Installing ffmpeg..."; \
			sudo dnf install -y ffmpeg; \
		else \
			echo "==> ffmpeg already installed: $$(ffmpeg -version 2>&1 | head -1)"; \
		fi; \
	elif command -v pacman >/dev/null 2>&1; then \
		echo "==> Using pacman..."; \
		if ! command -v ffmpeg >/dev/null 2>&1; then \
			echo "==> Installing ffmpeg..."; \
			sudo pacman -S --noconfirm ffmpeg; \
		else \
			echo "==> ffmpeg already installed: $$(ffmpeg -version 2>&1 | head -1)"; \
		fi; \
	else \
		echo "Error: No supported package manager found (apt-get, dnf, pacman)."; \
		echo "       Please install ffmpeg manually."; \
		exit 1; \
	fi
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "==> Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	else \
		echo "==> uv already installed: $$(uv --version)"; \
	fi

test: ## Run tests
	uv run pytest -v

run: ## Run speech2text (usage: make run ARGS="input.mp4 -l ja")
	uv run speech2text $(ARGS)

clean: ## Remove build artifacts and temp files
	rm -rf dist/ build/ *.egg-info .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

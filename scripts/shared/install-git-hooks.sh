#!/bin/bash
# Install Git Hooks for Rezept-Tagebuch

echo "📦 Installing Git Hooks..."
echo ""

# Check if we're in a git repo
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository"
    echo "   Run this script from the project root"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy pre-commit hook
if [ -f ".git/hooks/pre-commit" ]; then
    echo "⚠️  Pre-commit hook already exists"
    echo "   Backing up to .git/hooks/pre-commit.backup"
    cp .git/hooks/pre-commit .git/hooks/pre-commit.backup
fi

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Git Pre-Commit Hook for Rezept-Tagebuch
# Runs pytest test suite before allowing commit

echo "🧪 Running tests before commit..."
echo ""

# Check if dev container is running
if ! podman ps | grep -q "seaser-rezept-tagebuch-dev"; then
    echo "⚠️  Dev container is not running"
    echo "   Tests cannot run without container"
    echo ""
    echo "Options:"
    echo "  1. Start container: ./scripts/deployment/build-dev.sh"
    echo "  2. Skip tests: git commit --no-verify"
    echo ""
    exit 1
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "⚠️  pytest is not installed"
    echo "   Installing pytest..."
    pip3 install pytest pytest-timeout --break-system-packages --quiet
fi

# Run tests
echo "Running pytest test suite..."
pytest -x -q

# Check test result
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
    echo "   Proceeding with commit..."
    echo ""
    exit 0
else
    echo ""
    echo "❌ Tests failed!"
    echo "   Commit aborted."
    echo ""
    echo "Options:"
    echo "  1. Fix failing tests"
    echo "  2. Skip tests: git commit --no-verify"
    echo ""
    exit 1
fi
EOF

# Make executable
chmod +x .git/hooks/pre-commit

echo "✅ Pre-commit hook installed successfully!"
echo ""
echo "The hook will:"
echo "  • Run pytest before every commit"
echo "  • Block commits if tests fail"
echo "  • Can be bypassed with: git commit --no-verify"
echo ""

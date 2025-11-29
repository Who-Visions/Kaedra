#!/bin/bash
# Cloud Shell First-Time Setup for Dav1d
# Run this once when you first open Cloud Shell

set -e  # Exit on any error

echo "🚀 Setting up Dav1d in Google Cloud Shell..."
echo ""

# 1. Configure Git Identity
echo "📝 Step 1: Configuring Git identity..."
read -p "Enter your name: " GIT_NAME
read -p "Enter your email: " GIT_EMAIL

git config --global user.name "$GIT_NAME"
git config --global user.email "$GIT_EMAIL"
echo "✅ Git identity configured"
echo ""

# 2. Generate SSH Key for GitHub
echo "🔑 Step 2: Generating SSH key for GitHub..."
if [ ! -f ~/.ssh/id_ed25519 ]; then
    ssh-keygen -t ed25519 -C "$GIT_EMAIL" -f ~/.ssh/id_ed25519 -N ""
    echo "✅ SSH key generated"
else
    echo "⚠️  SSH key already exists, skipping..."
fi
echo ""

# 3. Display public key
echo "📋 Step 3: Your GitHub SSH Public Key:"
echo "════════════════════════════════════════════════════════════════"
cat ~/.ssh/id_ed25519.pub
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📌 ACTION REQUIRED:"
echo "1. Copy the key above (triple-click to select all)"
echo "2. Go to: https://github.com/settings/ssh/new"
echo "3. Paste the key and save"
echo ""
read -p "Press Enter once you've added the key to GitHub..."

# 4. Test GitHub connection
echo "🧪 Step 4: Testing GitHub connection..."
ssh -T git@github.com 2>&1 | grep -q "successfully authenticated" && echo "✅ GitHub SSH working!" || echo "⚠️  GitHub SSH test inconclusive (this is normal)"
echo ""

# 5. Clone Dav1d repository
echo "📦 Step 5: Cloning Dav1d repository..."
read -p "Enter your GitHub username: " GITHUB_USER

if [ ! -d ~/Dav1d ]; then
    cd ~
    git clone git@github.com:$GITHUB_USER/Dav1d.git
    echo "✅ Repository cloned"
else
    echo "⚠️  Dav1d directory already exists, skipping clone..."
fi
echo ""

# 6. Install dependencies
echo "📚 Step 6: Installing Python dependencies..."
cd ~/Dav1d/dav1d\ brain
pip install --user -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# 7. Configure GCP project
echo "☁️  Step 7: Configuring GCP project..."
gcloud config set project gen-lang-client-0285887798
echo "✅ GCP project set"
echo ""

# 8. Create helper aliases
echo "⚡ Step 8: Creating helpful aliases..."
cat >> ~/.bashrc << 'EOF'

# Dav1d Aliases
alias dav1d='cd ~/Dav1d/dav1d\ brain && python dav1d.py'
alias dav1d-edit='cd ~/Dav1d/dav1d\ brain && cloudshell edit .'
alias dav1d-update='cd ~/Dav1d && git pull && cd dav1d\ brain && pip install --user -r requirements.txt --upgrade'
alias dav1d-push='cd ~/Dav1d && git add . && git commit && git push origin main'
alias dav1d-status='cd ~/Dav1d && git status'

# Quick navigation
alias d='cd ~/Dav1d/dav1d\ brain'
alias ui='cd ~/Dav1d/dav1d-ui'

EOF

# Reload bashrc
source ~/.bashrc
echo "✅ Aliases created"
echo ""

# 9. Create workflow scripts
echo "📝 Step 9: Creating workflow helper scripts..."

# Update script
cat > ~/update_dav1d.sh << 'EOFSCRIPT'
#!/bin/bash
cd ~/Dav1d/dav1d\ brain
echo "📥 Pulling latest changes..."
git pull origin main
echo "📦 Updating dependencies..."
pip install --user -r requirements.txt --upgrade
echo "✅ Dav1d updated!"
EOFSCRIPT
chmod +x ~/update_dav1d.sh

# Quick commit script
cat > ~/commit_push.sh << 'EOFSCRIPT'
#!/bin/bash
cd ~/Dav1d
echo "📊 Current status:"
git status
echo ""
read -p "Commit message: " COMMIT_MSG
git add .
git commit -m "$COMMIT_MSG"
git push origin main
echo "✅ Changes pushed!"
EOFSCRIPT
chmod +x ~/commit_push.sh

echo "✅ Helper scripts created"
echo ""

# 10. Final instructions
echo "═══════════════════════════════════════════════════════════════"
echo "🎉 Setup Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Quick Reference:"
echo "  dav1d        → Launch Dav1d"
echo "  dav1d-edit   → Open editor"
echo "  dav1d-update → Pull latest changes"
echo "  dav1d-push   → Quick commit & push"
echo "  dav1d-status → Git status"
echo ""
echo "Helper Scripts:"
echo "  ~/update_dav1d.sh   → Full update workflow"
echo "  ~/commit_push.sh    → Interactive commit & push"
echo ""
echo "📁 Dav1d location: ~/Dav1d/dav1d brain"
echo ""
echo "🚀 Launch Dav1d now with: dav1d"
echo "═══════════════════════════════════════════════════════════════"

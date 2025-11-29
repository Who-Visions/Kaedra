# ⚡ Cloud Shell Setup Instructions
**Get Dav1d running in Cloud Shell with SSH keys + workflows**

---

## 🎯 One-Command Setup

### Option 1: Automated Setup (Recommended)

1. **Open Cloud Shell:** https://shell.cloud.google.com

2. **Run the setup script:**
   ```bash
   curl -sL https://raw.githubusercontent.com/YOUR_USERNAME/Dav1d/main/dav1d%20brain/cloud_shell_setup.sh | bash
   ```

   Or if you prefer to review first:
   ```bash
   wget https://raw.githubusercontent.com/YOUR_USERNAME/Dav1d/main/dav1d%20brain/cloud_shell_setup.sh
   cat cloud_shell_setup.sh  # Review it
   bash cloud_shell_setup.sh
   ```

**That's it!** The script will:
- ✅ Configure Git identity
- ✅ Generate SSH keys
- ✅ Guide you through GitHub setup
- ✅ Clone the repository
- ✅ Install dependencies
- ✅ Create helpful aliases
- ✅ Set up workflow scripts

---

## 🔧 Option 2: Manual Setup

If you prefer step-by-step control:

### Step 1: Configure Git
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

### Step 2: Generate SSH Key
```bash
ssh-keygen -t ed25519 -C "your@email.com"
# Press Enter 3 times (accept defaults)
```

### Step 3: Add Key to GitHub
```bash
# Display your public key
cat ~/.ssh/id_ed25519.pub

# Copy the output, then:
# 1. Go to: https://github.com/settings/ssh/new
# 2. Paste the key
# 3. Click "Add SSH key"
```

### Step 4: Test GitHub Connection
```bash
ssh -T git@github.com
# Should see: "Hi USERNAME! You've successfully authenticated"
```

### Step 5: Clone Repository
```bash
cd ~
git clone git@github.com:YOUR_USERNAME/Dav1d.git
cd Dav1d/dav1d\ brain
```

### Step 6: Install Dependencies
```bash
pip install --user -r requirements.txt
```

### Step 7: Configure GCP Project
```bash
gcloud config set project gen-lang-client-0285887798
```

### Step 8: Add Helpful Aliases
```bash
cat >> ~/.bashrc << 'EOF'

# Dav1d Aliases
alias dav1d='cd ~/Dav1d/dav1d\ brain && python dav1d.py'
alias dav1d-edit='cd ~/Dav1d/dav1d\ brain && cloudshell edit .'
alias dav1d-update='cd ~/Dav1d && git pull && cd dav1d\ brain && pip install --user -r requirements.txt --upgrade'
alias dav1d-push='cd ~/Dav1d && git add . && git commit && git push origin main'
alias dav1d-status='cd ~/Dav1d && git status'
alias d='cd ~/Dav1d/dav1d\ brain'

EOF

# Reload
source ~/.bashrc
```

### Step 9: Test Launch
```bash
dav1d
```

---

## 🚀 Post-Setup: Using Your New Workflow

### Quick Commands

| Command | What It Does |
|---------|-------------|
| `dav1d` | Launch Dav1d instantly |
| `dav1d-edit` | Open Cloud Shell editor |
| `dav1d-update` | Pull latest & update deps |
| `dav1d-push` | Quick commit & push |
| `dav1d-status` | Check git status |
| `d` | Navigate to Dav1d directory |

### Example Workflow

```bash
# Morning: Pull latest changes
dav1d-update

# Make changes
dav1d-edit

# Test
dav1d

# Push changes
dav1d-push
# (Will prompt for commit message)
```

---

## 📝 Helper Scripts Created

The setup creates two helper scripts in your home directory:

### 1. `~/update_dav1d.sh`
Updates Dav1d with latest code and dependencies:
```bash
~/update_dav1d.sh
```

### 2. `~/commit_push.sh`
Interactive commit and push:
```bash
~/commit_push.sh
# Shows git status
# Prompts for commit message
# Commits all changes
# Pushes to GitHub
```

---

## 🔄 Common Workflows

### Quick Bug Fix
```bash
# Pull latest
dav1d-update

# Edit file
nano dav1d.py  # or cloudshell edit

# Test
python dav1d.py

# Push fix
git add dav1d.py
git commit -m "Fix: Description of fix"
git push origin main
```

### Add New Feature
```bash
# Create new branch (optional)
cd ~/Dav1d
git checkout -b feature/new-tool

# Edit in Cloud Shell editor
dav1d-edit

# Test thoroughly
cd dav1d\ brain
python dav1d.py

# Commit and push
git add .
git commit -m "Add: New semantic search tool"
git push origin feature/new-tool

# Create PR on GitHub
# https://github.com/YOUR_USERNAME/Dav1d/pulls
```

### Sync After Desktop Changes
```bash
# You made changes on your desktop and pushed
# Now in Cloud Shell:
dav1d-update

# Verify changes
dav1d-status
cat dav1d.py  # Review changes

# Test
dav1d
```

---

## 🔑 SSH Key Management

### View Your Public Key
```bash
cat ~/.ssh/id_ed25519.pub
```

### Regenerate Key (If Compromised)
```bash
# Backup old key
mv ~/.ssh/id_ed25519 ~/.ssh/id_ed25519.old
mv ~/.ssh/id_ed25519.pub ~/.ssh/id_ed25519.pub.old

# Generate new key
ssh-keygen -t ed25519 -C "your@email.com"

# Add new key to GitHub
cat ~/.ssh/id_ed25519.pub
# Copy and add at: https://github.com/settings/keys

# Test
ssh -T git@github.com
```

### Use Multiple GitHub Accounts
Create `~/.ssh/config`:
```bash
# Work account
Host github-work
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_work

# Personal account
Host github-personal
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_personal
```

Then clone with:
```bash
git clone git@github-work:company/repo.git
git clone git@github-personal:yourname/repo.git
```

---

## ⚙️ Customization

### Add More Aliases
Edit `~/.bashrc`:
```bash
nano ~/.bashrc

# Add custom aliases:
alias dav1d-logs='cat ~/.dav1d/logs/*.log'
alias dav1d-clean='cd ~/Dav1d && git clean -fd'
alias dav1d-reset='cd ~/Dav1d && git reset --hard origin/main'

# Save and reload
source ~/.bashrc
```

### Create Project-Specific Script
Example `~/quick_test.sh`:
```bash
#!/bin/bash
cd ~/Dav1d/dav1d\ brain

echo "🧪 Running quick tests..."

# Test imports
python -c "import dav1d; print('✅ Imports OK')"

# Test cloud tools
python -c "from tools.vector_store_bigquery import BigQueryVectorStore; print('✅ Cloud tools OK')"

# Run specific test
python -c "
from dav1d import ModelSelector
selector = ModelSelector()
print('✅ Model selector OK')
"

echo "✅ All tests passed!"
```

Make it executable:
```bash
chmod +x ~/quick_test.sh
```

---

## 🐛 Troubleshooting

### "Permission denied (publickey)"
SSH key not added to GitHub:
```bash
# Display your key
cat ~/.ssh/id_ed25519.pub

# Copy and add here:
# https://github.com/settings/ssh/new
```

### "fatal: could not read from remote repository"
Wrong remote URL or no SSH access:
```bash
# Check current remote
git remote -v

# If using HTTPS, switch to SSH:
git remote set-url origin git@github.com:YOUR_USERNAME/Dav1d.git

# Test connection
ssh -T git@github.com
```

### "pip: command not found"
Cloud Shell uses `pip3`:
```bash
# Use pip3 explicitly
pip3 install --user -r requirements.txt

# Or create alias
echo "alias pip=pip3" >> ~/.bashrc
source ~/.bashrc
```

### "python: command not found"
Cloud Shell uses `python3`:
```bash
# Use python3 explicitly
python3 dav1d.py

# Or create alias
echo "alias python=python3" >> ~/.bashrc
source ~/.bashrc
```

### Cloud Shell Session Expired
Your `$HOME` persists, but you need to reload:
```bash
# Reload your custom config
source ~/.bashrc

# Navigate back to project
cd ~/Dav1d/dav1d\ brain

# Continue working
dav1d
```

---

## 🎓 Pro Tips

### 1. Automatic Updates
Add to `~/.bashrc` to auto-update on login:
```bash
# Auto-update Dav1d on Cloud Shell start
if [ -d ~/Dav1d ]; then
    echo "📥 Checking for Dav1d updates..."
    cd ~/Dav1d && git pull --quiet && cd ~
fi
```

### 2. Custom Welcome Message
```bash
cat >> ~/.bashrc << 'EOF'

# Welcome message
echo ""
echo "🚀 Dav1d Cloud Shell Environment"
echo "Quick commands: dav1d | dav1d-edit | dav1d-update"
echo ""
EOF
```

### 3. Persistent Environment Variables
For project-specific env vars:
```bash
# Add to ~/.bashrc
export DAV1D_ENV="cloud-shell"
export GOOGLE_CLOUD_PROJECT="gen-lang-client-0285887798"
```

### 4. Pre-commit Hooks
Create `.git/hooks/pre-commit` in your repo:
```bash
#!/bin/bash
# Auto-format Python before commit
autopep8 --in-place --recursive dav1d\ brain/
```

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] `git config --list` shows your name/email
- [ ] `ssh -T git@github.com` authenticates successfully  
- [ ] `ls ~/Dav1d` shows your cloned repository
- [ ] `dav1d` launches without errors
- [ ] `dav1d-edit` opens Cloud Shell editor
- [ ] `git push` works without password prompt
- [ ] `gcloud config get-value project` shows correct project

---

## 🌟 Summary

**After setup, your Cloud Shell workflow is:**

1. **Open:** https://shell.cloud.google.com
2. **Update:** `dav1d-update`
3. **Edit:** `dav1d-edit`
4. **Test:** `dav1d`
5. **Push:** `dav1d-push`

**That's it!** Full development cycle in the browser. 🚀

---

## 📌 Bookmark These

**Cloud Shell Direct Link:**
```
https://shell.cloud.google.com/?project=gen-lang-client-0285887798
```

**One-Click Launch & Clone:**
```
https://shell.cloud.google.com/?project=gen-lang-client-0285887798&cloudshell_git_repo=git@github.com:YOUR_USERNAME/Dav1d.git&cloudshell_working_dir=dav1d%20brain
```

(Replace `YOUR_USERNAME` with your actual GitHub username)

---

**Questions? Issues?** Open an issue on GitHub or check the troubleshooting section above.

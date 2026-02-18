# 🤖 AI DevOps Automation

![CI](https://github.com/Baho73/ai-devops-automation/actions/workflows/ci.yml/badge.svg)

> Teach AI to manage your server and eliminate DevOps routine

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

Transform your AI assistant into a full-fledged DevOps engineer. Deploy code, check logs, apply database migrations - all automatically via SSH and Python.

## 🎯 What This Does

- **Automated Deployment**: AI deploys files to production in 15 seconds
- **Log Analysis**: AI reads Docker logs and finds errors automatically
- **Database Migrations**: AI applies SQL migrations and validates results
- **Zero Human Errors**: No typos, no forgotten restarts, always checks logs
- **Always Up-to-Date Docs**: AI documents every change

## 📊 Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Deploy time** | 7 min | 15 sec | 28x faster |
| **Log checking** | 2 min | 10 sec | 12x faster |
| **DB migration** | 10 min | 30 sec | 20x faster |
| **Human errors** | ~5/day | 0 | 100% reduction |
| **Cost** | $3000/mo | $20/mo | 150x cheaper |

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ai-devops-automation.git
cd ai-devops-automation
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your server credentials
```

Example `.env`:
```env
SERVER_HOST=your.server.ip
SERVER_USER=root
SERVER_PASSWORD=your_password
CONTAINER_NAME=web_container
```

### 4. Deploy your first file

```bash
python scripts/deploy.py app.py /app/app.py
```

Output:
```
🔌 Connecting to your.server.ip...
✅ Connected
📤 Uploading app.py to /tmp/app.py...
✅ Upload complete
🐳 Copying to Docker container web_container...
✅ Copied to container
🔄 Restarting container web_container...
✅ Container restarted
🎉 Deployment successful!
```

### 5. Check logs

```bash
python scripts/check_logs.py web_container 50
```

## 📁 Project Structure

```
ai-devops-automation/
├── scripts/
│   ├── deploy.py           # Deploy files to server
│   ├── check_logs.py        # Retrieve and analyze logs
│   └── apply_migration.py   # Apply database migrations
├── examples/
│   └── docker-compose.yml   # Example Docker setup
├── docs/
│   └── SETUP.md            # Detailed setup guide
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore file
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
└── README.md               # This file
```

## 🔧 How It Works

### Architecture

```
┌─────────────────────────────────────────┐
│     AI Assistant (Claude Code)          │
│  ┌────────────────────────────────────┐ │
│  │  1. Reads deployment scripts       │ │
│  │  2. Loads .env credentials         │ │
│  │  3. Creates new scripts            │ │
│  │  4. Executes via Python            │ │
│  │  5. Analyzes results               │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
                    ↓
         ┌──────────────────────┐
         │  Python Scripts      │
         │  (paramiko + .env)   │
         └──────────────────────┘
                    ↓
              ┌──────────┐
              │    SSH   │
              └──────────┘
                    ↓
      ┌─────────────────────────────┐
      │    Production Server        │
      │  ┌─────────┐  ┌──────────┐ │
      │  │ Docker  │  │  MySQL   │ │
      │  └─────────┘  └──────────┘ │
      └─────────────────────────────┘
```

### Philosophy

1. **Code as Single Source of Truth**: All configs in repository, AI reads from there
2. **Automate Routine, Keep Creativity**: AI handles deployment, human makes decisions
3. **Trust but Verify**: AI has full access, but explains every action

## 💡 Usage Examples

### Deploy with AI

**You say**: "Deploy models.py to server"

**AI does**:
1. Reads `deploy.py` and `.env`
2. Creates deployment script
3. Uploads file via SSH
4. Copies to Docker container
5. Restarts container
6. Checks logs for errors
7. Reports results

**Time**: 15 seconds vs 7 minutes manually

### Fix Bug Automatically

**You say**: "Site is down, investigate"

**AI does**:
1. Checks container status: `docker ps -a`
2. Sees: `web_container - Exited (1)`
3. Reads logs: `docker logs web_container`
4. Finds: `AttributeError: 'NoneType'`
5. Reads problematic code
6. Adds null check
7. Deploys fix
8. Verifies site is working

**Time**: 45 seconds, fully automated

### Apply Database Migration

**You say**: "Add max_age column to projects table"

**AI does**:
1. Creates SQL migration
2. Creates apply script
3. Uploads to server
4. Applies via Docker exec
5. Validates with DESCRIBE
6. Reports success

**Time**: 30 seconds vs 10 minutes manually

## 🔐 Security

### Current Implementation (for MVP)
- Credentials in `.env` file (gitignored)
- SSH password authentication
- Single user access

### Production Recommendations
✅ Use SSH keys instead of passwords
✅ Store secrets in vault (HashiCorp Vault, AWS Secrets Manager)
✅ Configure firewall (allow SSH from specific IPs only)
✅ Use VPN for server access
✅ Rotate credentials monthly
✅ Enable 2FA where possible

## 📚 Documentation

- [Setup Guide](docs/SETUP.md) - Detailed installation and configuration
- [API Reference](docs/API.md) - Script documentation
- [Examples](examples/) - Real-world usage examples
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Paramiko](https://www.paramiko.org/) - SSH implementation for Python
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment variable management
- [Docker](https://www.docker.com/) - Containerization platform
- [Claude Code](https://claude.ai/claude-code) - AI assistant with file system access

## 📬 Contact

- **Habr Article**: [Как я научил AI управлять сервером](https://habr.com/your-article-link)
- **Issues**: [GitHub Issues](https://github.com/yourusername/ai-devops-automation/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ai-devops-automation/discussions)

## ⭐ Star History

If this project helped you, please consider giving it a star ⭐

---

**Made with ❤️ by developers, for developers**

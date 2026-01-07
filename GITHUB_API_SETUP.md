# GitHub API 配置指南

本指南将帮助你配置 GitHub Personal Access Token，用于提高 GitHub Search API 的速率限制。

## 为什么需要配置 GitHub Token？

GitHub API **无需认证也可以使用**，但有速率限制：
- **未认证**：60 次/小时
- **认证**：5000 次/小时

对于每周抓取一次的项目，未认证的速率限制通常已经足够。但如果你需要更频繁地抓取，或者想要更稳定的服务，建议配置 Token。

## 配置步骤

### 1. 创建 GitHub Personal Access Token

1. **访问 GitHub Settings**
   - 打开 https://github.com/settings/tokens
   - 或访问 GitHub 主页 → 右上角头像 → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **生成新 Token**
   - 点击 "Generate new token" → "Generate new token (classic)"
   - 或者直接访问：https://github.com/settings/tokens/new

3. **配置 Token**
   - **Note（备注）**：输入 Token 名称，如 "VLA Tracker"
   - **Expiration（过期时间）**：选择过期时间（建议选择较长时间，如 90 天或 1 年）
   - **Select scopes（权限）**：
     - ✅ 勾选 `public_repo`（搜索公开仓库需要此权限）
     - 其他权限不需要勾选

4. **生成 Token**
   - 滚动到页面底部，点击 "Generate token" 按钮
   - **重要**：立即复制生成的 Token，因为关闭页面后无法再次查看完整 Token
   - Token 格式类似：`ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 2. 配置到项目中

编辑 `config.py` 文件，添加你的 GitHub Token：

```python
GITHUB_TOKEN = "你的GitHub_Token"
```

例如：
```python
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 3. 验证配置

运行以下命令测试配置是否正确：

```bash
python -c "
from crawler import github_search
try:
    results = github_search('VLA robot', max_results=5)
    print(f'✓ GitHub API 配置成功，找到 {len(results)} 条结果')
except Exception as e:
    print(f'✗ GitHub API 配置失败: {e}')
"
```

## 使用环境变量（推荐用于生产环境）

如果使用 GitHub Actions 或其他 CI/CD 服务，建议使用环境变量：

1. **在 GitHub Secrets 中配置**（如果使用 GitHub Actions）：
   - 进入仓库设置 → Secrets and variables → Actions
   - 点击 "New repository secret"
   - Name: `GITHUB_TOKEN`
   - Value: 你的 GitHub Token
   - 点击 "Add secret"

2. **在代码中使用环境变量**：
   ```python
   # config.py 已经支持从环境变量读取
   GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
   ```

## 速率限制说明

### 未认证（无 Token）

- **限制**：60 次/小时
- **适用场景**：每周抓取一次，完全够用
- **优点**：无需配置，开箱即用

### 认证（有 Token）

- **限制**：5000 次/小时
- **适用场景**：需要频繁抓取或批量处理
- **优点**：速率限制大幅提升，更稳定

## 常见问题

### Q: Token 过期了怎么办？

**A:** 
1. 访问 https://github.com/settings/tokens
2. 找到过期的 Token，点击 "Regenerate token"
3. 复制新 Token 并更新到 `config.py`

### Q: 如何查看 Token 使用情况？

**A:**
1. 访问 https://github.com/settings/tokens
2. 点击你的 Token 名称
3. 查看 "Last used" 时间

### Q: Token 泄露了怎么办？

**A:**
1. 立即访问 https://github.com/settings/tokens
2. 找到泄露的 Token，点击 "Revoke"（撤销）
3. 创建新的 Token 并更新配置

### Q: 如何保护 Token 安全？

**A:**
1. **不要**将 `config.py` 提交到 Git（已在 `.gitignore` 中）
2. 使用环境变量（推荐用于生产环境）
3. 定期轮换 Token（建议每 90 天更换一次）
4. 不要将 Token 分享给他人

### Q: 不配置 Token 可以吗？

**A:** 可以！GitHub API 无需认证也可以使用，只是速率限制较低（60 次/小时）。对于每周抓取一次的项目，通常已经足够。

## 下一步

配置完成后，运行 `python run_daily.py` 来测试 GitHub 搜索功能是否正常工作。

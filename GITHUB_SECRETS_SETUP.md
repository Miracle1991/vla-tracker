# GitHub Secrets 配置指南

## 已配置的 Secrets ✓

- ✅ `GOOGLE_API_KEY` - Google Custom Search API Key
- ✅ `GOOGLE_CSE_ID` - Google Custom Search Engine ID

## 必须配置的 Secrets（必需）

### 1. `SEARCH_QUERY` - 搜索查询语句

**说明**：用于搜索 VLA 相关内容的查询语句。

**推荐值**：
```
(VLA OR "vision language action") AND (robot OR robotics OR "autonomous driving" OR "self-driving" OR "autonomous vehicle" OR "robotic manipulation" OR "embodied AI" OR "robot control")
```

**如何配置**：
1. 进入 GitHub 仓库
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`
4. Name: `SEARCH_QUERY`
5. Secret: 粘贴上面的查询语句
6. 点击 `Add secret`

---

### 2. `GITHUB_TOKEN` - GitHub Personal Access Token

**说明**：用于访问 GitHub API 和部署到 GitHub Pages。

**如何获取**：
1. 访问 https://github.com/settings/tokens
2. 点击 `Generate new token` → `Generate new token (classic)`
3. 填写 Token 名称（如：`vla-tracker-deploy`）
4. 选择过期时间（建议选择 `No expiration` 或较长时间）
5. 勾选以下权限：
   - ✅ `repo` (完整仓库权限)
   - ✅ `workflow` (工作流权限)
6. 点击 `Generate token`
7. **重要**：立即复制 token（只显示一次）

**如何配置**：
1. 进入 GitHub 仓库
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`
4. Name: `GITHUB_TOKEN`
5. Secret: 粘贴刚才复制的 token
6. 点击 `Add secret`

**注意**：如果使用 GitHub Actions 自动部署，也可以使用系统自动生成的 `GITHUB_TOKEN`（但需要确保有足够权限）。

---

### 3. `HF_TOKEN` - HuggingFace Access Token

**说明**：用于访问 HuggingFace Hub API 搜索模型和数据集。

**如何获取**：
1. 访问 https://huggingface.co/settings/tokens
2. 如果没有账号，先注册一个免费账号
3. 点击 `New token`
4. 填写 Token 名称（如：`vla-tracker`）
5. 选择权限：`Read`（只读权限即可）
6. 点击 `Generate a token`
7. 复制 token

**如何配置**：
1. 进入 GitHub 仓库
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`
4. Name: `HF_TOKEN`
5. Secret: 粘贴刚才复制的 token
6. 点击 `Add secret`

---

## 可选配置的 Secrets（有默认值）

### 4. `MAX_RESULTS_PER_SITE` - 每个站点最多抓取的结果数

**说明**：控制每个站点（GitHub、HuggingFace、arXiv、知乎）最多抓取多少条结果。

**默认值**：`30`

**推荐值**：`30`（如果不需要修改，可以不配置）

**如何配置**（如果需要修改）：
1. 进入 GitHub 仓库
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`
4. Name: `MAX_RESULTS_PER_SITE`
5. Secret: `30`（或你想要的数字）
6. 点击 `Add secret`

---

### 5. `RESEARCH_ORGANIZATIONS` - 研究机构列表

**说明**：用于追踪头部公司和机构的研究进展。多个机构用逗号分隔。

**默认值**（如果未配置，将使用代码中的默认列表）：
```
NVIDIA,Google DeepMind,Meta,Microsoft,OpenAI,MIT,Stanford,UC Berkeley,清华,中科院,新加坡国立大学,Tesla,Boston Dynamics,Physical Intelligence,智元机器人
```

**如何配置**（如果需要自定义）：
1. 进入 GitHub 仓库
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`
4. Name: `RESEARCH_ORGANIZATIONS`
5. Secret: 粘贴机构列表（逗号分隔），例如：
   ```
   NVIDIA,Google DeepMind,Meta,Microsoft,OpenAI,MIT,Stanford,UC Berkeley,清华,中科院,新加坡国立大学,Tesla,Boston Dynamics,Physical Intelligence,智元机器人
   ```
6. 点击 `Add secret`

**注意**：如果不配置，将使用代码中的默认列表。

---

## 配置清单

### 必须配置（3个）

- [ ] `SEARCH_QUERY` - 搜索查询语句
- [ ] `GITHUB_TOKEN` - GitHub Personal Access Token
- [ ] `HF_TOKEN` - HuggingFace Access Token

### 可选配置（2个）

- [ ] `MAX_RESULTS_PER_SITE` - 每个站点最多抓取的结果数（默认：30）
- [ ] `RESEARCH_ORGANIZATIONS` - 研究机构列表（有默认值）

---

## 配置完成后

1. 所有必需的 Secrets 配置完成后，GitHub Actions 工作流就可以正常运行了。
2. 你可以通过以下方式触发工作流：
   - **自动触发**：推送到 `main` 分支
   - **手动触发**：进入 `Actions` 标签页，选择 `Deploy to GitHub Pages` 工作流，点击 `Run workflow`
   - **定时触发**：每周一 UTC 8:00（北京时间 16:00）自动运行

3. 查看工作流执行情况：
   - 进入 `Actions` 标签页
   - 点击最新的工作流运行
   - 查看各个步骤的执行日志

---

## 常见问题

### Q: GITHUB_TOKEN 和系统自动生成的 GITHUB_TOKEN 有什么区别？

A: 
- 系统自动生成的 `GITHUB_TOKEN` 是 GitHub Actions 自动提供的，但权限可能有限。
- 手动配置的 `GITHUB_TOKEN` 是 Personal Access Token，权限更完整，可以访问私有仓库和进行更多操作。
- 对于公开仓库的 GitHub Pages 部署，系统自动生成的 `GITHUB_TOKEN` 通常就足够了。但如果你需要访问 GitHub API 搜索仓库，建议使用手动配置的 Personal Access Token。

### Q: HF_TOKEN 是必需的吗？

A: 是的，因为代码中使用了 HuggingFace Hub API 来搜索模型和数据集。如果没有配置，HuggingFace 搜索功能将无法正常工作。

### Q: 如何验证配置是否正确？

A: 
1. 配置完所有必需的 Secrets 后
2. 手动触发一次工作流（`Actions` → `Deploy to GitHub Pages` → `Run workflow`）
3. 查看工作流日志，确认没有出现 "API key not valid" 或 "Token not found" 等错误

---

## 参考文档

- [GitHub Personal Access Token 创建指南](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [HuggingFace Access Token 创建指南](https://huggingface.co/docs/hub/security-tokens)
- [GitHub Secrets 配置指南](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

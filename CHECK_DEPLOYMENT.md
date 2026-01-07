# 部署问题排查指南

如果网站显示 README 而不是 VLA 追踪内容，请按以下步骤排查：

## 步骤 1：检查 GitHub Actions 是否成功运行

1. 进入仓库：https://github.com/Miracle1991/vla-tracker
2. 点击 **Actions** 标签
3. 查看最新的 "Deploy to GitHub Pages" 运行
4. 检查：
   - ✅ 所有步骤是否都是绿色 ✓
   - ✅ "Deploy to GitHub Pages" 步骤是否成功
   - ❌ 如果有红色 ✗，点击查看错误信息

## 步骤 2：检查 gh-pages 分支是否存在

1. 在仓库页面，点击分支下拉菜单（显示 "main" 的地方）
2. 查看是否有 **gh-pages** 分支
3. 如果有，切换到 `gh-pages` 分支
4. 检查是否有 `index.html` 文件（不是 README.md）

## 步骤 3：检查 GitHub Pages 配置

1. 进入 **Settings** → **Pages**
2. 检查 **Source** 配置：
   - ✅ 应该选择 **Deploy from a branch**
   - ✅ **Branch** 应该选择 **gh-pages**（不是 main）
   - ✅ **Folder** 应该选择 **/ (root)**
3. 如果配置错误，修改后点击 **Save**

## 步骤 4：如果 gh-pages 分支不存在

说明部署步骤失败了。请：

1. 查看 Actions 日志，找出失败原因
2. 常见问题：
   - 权限不足：检查是否添加了 `permissions: contents: write`
   - 生成失败：检查 `generate_static.py` 是否有错误
   - API 错误：检查 Secrets 是否正确配置

## 步骤 5：手动创建 gh-pages 分支（临时方案）

如果 Actions 一直失败，可以手动创建：

```bash
# 在本地运行
python generate_static.py

# 创建 gh-pages 分支并推送
git checkout --orphan gh-pages
git rm -rf .
cp -r docs/* .
git add .
git commit -m "Initial gh-pages commit"
git push origin gh-pages
```

## 步骤 6：验证网站

1. 等待 1-2 分钟让 GitHub Pages 更新
2. 访问：https://miracle1991.github.io/vla-tracker/
3. 应该看到 VLA 追踪内容，而不是 README

## 常见错误

### 错误：显示 README
- **原因**：GitHub Pages 配置为从 `main` 分支读取
- **解决**：改为从 `gh-pages` 分支读取

### 错误：404 Not Found
- **原因**：`gh-pages` 分支不存在或没有 `index.html`
- **解决**：检查 Actions 是否成功运行

### 错误：Actions 失败
- **原因**：代码错误、权限问题、API 错误等
- **解决**：查看 Actions 日志，找出具体错误

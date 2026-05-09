# Git 使用教程

## 1. Git 基础配置

### 初始化配置
```bash
# 设置用户名和邮箱
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 查看配置
git config --list
```

## 2. 常用命令

### 初始化与克隆
```bash
# 初始化仓库
git init

# 克隆远程仓库
git clone https://github.com/username/repo.git
```

### 基础操作
```bash
# 查看状态
git status

# 添加文件到暂存区
git add filename.txt      # 添加单个文件
git add .                 # 添加所有文件

# 提交更改
git commit -m "提交信息"

# 查看提交历史
git log
git log --oneline         # 简洁模式
```

### 分支操作
```bash
# 查看分支
git branch

# 创建新分支
git branch feature-branch

# 切换分支
git checkout feature-branch
git switch feature-branch      # 新版命令

# 创建并切换
git checkout -b feature-branch

# 合并分支
git merge feature-branch

# 删除分支
git branch -d feature-branch
```

## 3. 远程操作

```bash
# 查看远程仓库
git remote -v

# 添加远程仓库
git remote add origin https://github.com/username/repo.git

# 推送代码
git push origin main

# 拉取代码
git pull origin main
```

## 4. 撤销操作

```bash
# 撤销工作区的修改
git checkout -- filename.txt

# 取消暂存（从暂存区移出）
git reset HEAD filename.txt

# 回退到上一个版本
git reset --hard HEAD^

# 回退到指定版本
git reset --hard commit_id
```

## 5. 标签管理

```bash
# 创建标签
git tag v1.0.0

# 推送标签
git push origin v1.0.0

# 查看所有标签
git tag
```

---
*Git 教程整理于 2026-05-09*
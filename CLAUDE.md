# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

本仓库包含两个独立的部分：

### 1. Spring Boot Web 应用（根目录）
- **技术栈**：Java 8, Spring Boot 2.6.13, Maven, Thymeleaf
- **用途**：个人主页和在线简历展示
- **结构**：
  - `src/main/java/com/example/demo/` — Java 源码
    - `DemoApplication.java` — 应用入口
    - `demos/controller/HomeController.java` — 页面路由（`/`, `/cv`）
    - `demos/web/BasicController.java` — REST API（`/hello`, `/user`, `/save_user`）
    - `demos/web/PathVariableController.java` — 路径参数示例
  - `src/main/resources/templates/` — Thymeleaf 模板（`index.html`, `cv.html`）
  - `src/main/resources/static/` — 静态资源
  - `src/main/resources/file/` — 文件资源（`resume.png`）
  - `src/main/resources/application.properties` — 应用配置（端口 8080, Thymeleaf, 静态资源路径）

### 2. Jekyll 考研笔记网站（docs/ 目录）
- **技术栈**：Jekyll + GitHub Pages, `jekyll-theme-minimal` 主题
- **用途**：考研（408 计算机、数学、英语、政治）学习笔记
- **CI/CD**：`.github/workflows/jekyll.yml` — main 分支推送自动部署到 GitHub Pages
- **内容**：`docs/` 下按科目组织（math/, cs/, english/, politics/），含 HTML 静态页面

## 常用命令

```bash
# 启动 Spring Boot 应用
mvn spring-boot:run

# 运行测试
mvn test

# 构建（跳过测试）
mvn package -DskipTests

# 清除构建产物
mvn clean
```

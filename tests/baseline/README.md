# 阶段 1 验收基线

基线记录于 2026-08-02，代表阶段 1 开始时的站点行为和页面结构。

## 当前数据

- HTML 页面：46
- 本地链接与资源引用：783
- 页面内 ID：1400
- 失效本地目标：0
- 失效页内锚点：0
- 失效跨页面锚点：0
- 含 viewport：46
- 含唯一 H1：46
- 含站点导航、页脚和跳转链接：46
- 含目录：41
- 含 MathJax：22
- 使用 `<main>`：0（已记录的现有技术债务，不是阶段 1 新增问题）

`site-baseline.json` 不保存整页哈希，而是保存用户和链接依赖的页面路径、标题、锚点及结构特征。这样可以发现意外回归，同时允许后续有意调整正文和样式。

## 视觉基线

截图保存在 `output/playwright/baseline/`：

- `home-desktop-1440x1000.png`
- `home-mobile-390x844.png`
- `home-dark-desktop-1440x1000.png`
- `knowledge-base-desktop-1440x1000.png`
- `knowledge-base-mobile-390x844.png`
- `probability-desktop-1440x1000.png`
- `probability-mobile-390x844.png`
- `computer-network-desktop-1440x1000.png`
- `computer-network-mobile-390x844.png`

截图只记录当前状态，不表示现有布局已经达到最终设计标准。

## 已记录的现有问题

- 页面尚未使用 `<main>` 语义元素。
- 本地预览首页会请求不存在的 `favicon.ico`，浏览器控制台出现一次 404。
- 移动端长目录会占据较多首屏空间。
- 关闭状态的移动菜单仍出现在浏览器无障碍树中。

这些问题留待后续结构或阅读体验阶段处理，本阶段没有修改页面实现。

## 使用方式

```powershell
python tools/site_audit.py check --root . --baseline tests/baseline/site-baseline.json
python -m unittest discover -s tests -v
```

只有在确认变化属于预期修改后，才能重新执行 `scan` 更新基线。

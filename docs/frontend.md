# 前端开发笔记

## HTML 基础

### 文档结构
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>页面标题</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>
```

### 常用标签
- 标题：`<h1>` - `<h6>`
- 段落：`<p>`
- 链接：`<a href="url">`
- 图片：`<img src="path" alt="描述">`
- 列表：`<ul>`, `<ol>`, `<li>`
- 表格：`<table>`, `<tr>`, `<td>`
- 表单：`<form>`, `<input>`, `<button>`

## CSS 基础

### 选择器
```css
/* 元素选择器 */
p { color: blue; }

/* 类选择器 */
.highlight { background: yellow; }

/* ID选择器 */
#header { height: 60px; }

/* 后代选择器 */
article p { line-height: 1.6; }

/* 伪类 */
a:hover { color: red; }
```

### 盒模型
```css
.box {
    width: 200px;
    padding: 20px;
    border: 1px solid #ccc;
    margin: 10px;
    box-sizing: border-box;
}
```

### Flexbox 布局
```css
.container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
}
```

### Grid 布局
```css
.grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
}
```

## JavaScript 基础

### 变量声明
```javascript
// 变量
let name = 'Tom';

// 常量
const PI = 3.14159;

// 数据类型
let num = 123;           // Number
let str = "Hello";       // String
let isTrue = true;       // Boolean
let arr = [1, 2, 3];     // Array
let obj = { key: 'value' }; // Object
```

### 函数
```javascript
// 函数声明
function greet(name) {
    return `Hello, ${name}!`;
}

// 箭头函数
const add = (a, b) => a + b;

// 回调函数
setTimeout(() => {
    console.log('延迟执行');
}, 1000);
```

### DOM 操作
```javascript
// 获取元素
const element = document.getElementById('myId');
const elements = document.querySelectorAll('.myClass');

// 修改内容
element.textContent = '新文本';
element.innerHTML = '<span>HTML内容</span>';

// 修改样式
element.style.color = 'red';

// 添加事件
element.addEventListener('click', () => {
    alert('点击了！');
});
```

### 数组方法
```javascript
const arr = [1, 2, 3, 4, 5];

// 遍历
arr.forEach(item => console.log(item));

// 映射
const doubled = arr.map(item => item * 2);

// 过滤
const evens = arr.filter(item => item % 2 === 0);

//  reduce
const sum = arr.reduce((acc, item) => acc + item, 0);
```

---
*前端笔记整理于 2026-05-09*
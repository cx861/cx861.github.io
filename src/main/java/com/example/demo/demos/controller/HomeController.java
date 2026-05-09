package com.example.demo.demos.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class HomeController {
    // 首页 - 唯一映射 / 路径
    @GetMapping("/")
    public String index() {
        // 返回 templates 目录下的 index.html
        return "index";
    }

    // 简历页 - 唯一映射 /cv 路径
    @GetMapping("/cv")
    public String cv() {
        // 返回 templates 目录下的 cv.html
        return "cv";
    }
}

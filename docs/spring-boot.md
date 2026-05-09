# Spring Boot 入门指南

## 1. Spring Boot 简介

Spring Boot 是 Spring 框架的扩展，简化了 Spring 应用的创建和部署过程。

**核心优势：**
- 自动配置
- 嵌入式服务器
- starter 依赖简化
- 生产级特性

## 2. 快速开始

### 项目结构
```
src/
├── main/
│   ├── java/
│   │   └── com/example/demo/
│   │       └── DemoApplication.java
│   └── resources/
│       ├── application.properties
│       ├── static/
│       └── templates/
└── test/
```

### 主类
```java
@SpringBootApplication
public class DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}
```

## 3. 常用注解

| 注解 | 作用 |
|------|------|
| @SpringBootApplication | 标识主类 |
| @RestController | RESTful 控制器 |
| @RequestMapping | 请求映射 |
| @GetMapping | GET 请求 |
| @PostMapping | POST 请求 |
| @Autowired | 依赖注入 |
| @Service | 服务层组件 |
| @Repository | 数据访问层组件 |

## 4. 控制器示例

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }

    @PostMapping
    public User createUser(@RequestBody User user) {
        return userService.save(user);
    }
}
```

## 5. 配置文件

### application.properties
```properties
server.port=8080
spring.application.name=demo
```

### application.yml
```yaml
server:
  port: 8080
spring:
  application:
    name: demo
```

## 6. 数据库操作

### JPA 示例
```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    List<User> findByName(String name);
}
```

---
*Spring Boot 笔记整理于 2026-05-09*
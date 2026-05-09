# Java 基础知识

## 1. 基本数据类型

Java 有 8 种基本数据类型：

| 类型 | 大小 | 范围 |
|------|------|------|
| byte | 1字节 | -128 ~ 127 |
| short | 2字节 | -32768 ~ 32767 |
| int | 4字节 | -2^31 ~ 2^31-1 |
| long | 8字节 | -2^63 ~ 2^63-1 |
| float | 4字节 | 单精度浮点 |
| double | 8字节 | 双精度浮点 |
| char | 2字节 | Unicode字符 |
| boolean | 1位 | true/false |

## 2. 面向对象三大特性

### 封装
将数据和操作封装在类中，隐藏内部细节。

```java
public class Person {
    private String name;
    private int age;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }
}
```

### 继承
子类继承父类的属性和方法。

```java
public class Student extends Person {
    private String school;

    public String getSchool() {
        return school;
    }
}
```

### 多态
同一个方法调用产生不同行为。

- 重写（Override）：子类重写父类方法
- 重载（Overload）：同一个类中方法名相同但参数不同

## 3. 集合框架

### List（列表）
- ArrayList：动态数组，查询快增删慢
- LinkedList：链表，增删快查询慢

### Set（集合）
- HashSet：无序不重复
- TreeSet：有序不重复

### Map（映射）
- HashMap：键值对映射
- TreeMap：按键排序

## 4. 异常处理

```java
try {
    // 可能抛出异常的代码
    int result = 10 / 0;
} catch (ArithmeticException e) {
    // 处理异常
    System.out.println("除数不能为0");
} finally {
    // 无论是否异常都会执行
    System.out.println("执行完毕");
}
```

## 5. 多线程

### 创建线程的方式

**方式一：继承 Thread 类**
```java
public class MyThread extends Thread {
    @Override
    public void run() {
        System.out.println("线程执行中...");
    }
}
```

**方式二：实现 Runnable 接口**
```java
public class MyRunnable implements Runnable {
    @Override
    public void run() {
        System.out.println("线程执行中...");
    }
}
```

---
*Java 基础笔记整理于 2026-05-09*
# MySQL Tool

本项目的 SQL 工具支持两种后端：

```text
sqlite -> 本地 demo 数据库
mysql  -> 真实业务 MySQL
```

## 连接方式

MySQL 连接信息从环境变量读取：

```text
MYSQL_HOST
MYSQL_PORT
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE
```

## 只读策略

SQL 执行前会经过：

1. `validate_readonly_sql()`
2. 单语句检查
3. `SELECT` 校验
4. 自动 `LIMIT`

这意味着：

- 不能执行写操作；
- 不能执行多语句；
- 不能绕过只读约束。

## 验证命令

```powershell
cd agent-platform
python scripts\smoke_mysql.py --query "销售额最高的商品是什么？"
python scripts\smoke_mysql.py --show-schema
```

## 部署建议

如果是真实业务库，建议使用只读账号，并限制：

- 只允许 SELECT；
- 只允许指定 schema；
- 只允许业务必要表；
- 只允许有限超时和行数。

## 与 SQLite 的关系

SQLite 仍然保留给本地开发、测试和 demo。MySQL 是生产 / 真实业务后端，不应直接替代本地测试数据源。
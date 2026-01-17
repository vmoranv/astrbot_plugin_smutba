# SmutBase AstrBot 插件

用于查询 [SmutBase](https://smutba.se/) 网站 3D 模型资源的 AstrBot 插件。

## 功能特性

- 🔍 搜索模型资源
- 📦 查看模型详情
- 📃 分页浏览
- 🏷️ 分类筛选
- 🎲 随机获取
- 🖼️ 缩略图显示（支持模糊处理）
- 🧹 自动缓存清理

## 安装

将插件目录放入 AstrBot 的插件目录中，然后重启 AstrBot。

依赖会自动安装，或者手动安装：

```bash
pip install -r requirements.txt
```

## 命令列表

| 命令 | 说明 | 用法 |
|------|------|------|
| `/smutbase` | 获取模型详情 | `/smutbase <模型ID>` |
| `/smutbase_search` | 搜索模型 | `/smutbase_search <关键词>` |
| `/smutbase_page` | 搜索并指定页码 | `/smutbase_page <页码> [关键词]` |
| `/smutbase_latest` | 获取最新模型 | `/smutbase_latest [页码]` |
| `/smutbase_popular` | 获取热门模型 | `/smutbase_popular [页码]` |
| `/smutbase_random` | 获取随机模型 | `/smutbase_random` |
| `/smutbase_category` | 按分类搜索 | `/smutbase_category <分类> [页码]` |
| `/smutbase_url` | 获取模型链接 | `/smutbase_url <模型ID>` |
| `/smutbase_clean` | 清理缓存 | `/smutbase_clean` |

### 可用分类

- `models` - 模型
- `textures` - 纹理
- `sceneries` - 场景
- `hdris` - HDR 环境
- `other` - 其他

## 配置说明

在 AstrBot 的配置面板中可以配置以下选项：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `proxy` | string | "" | 代理服务器地址，格式如 `http://127.0.0.1:7890` |
| `blur_level` | int | 0 | 缩略图模糊程度 (0-100)，0 为不模糊 |
| `max_results` | int | 10 | 每次搜索返回的最大结果数 |
| `timeout` | int | 30 | 网络请求超时时间（秒） |
| `cache_dir` | string | "cache" | 缓存目录名称 |
| `auto_cleanup` | bool | true | 是否自动清理上次的缓存文件 |
| `show_thumbnail` | bool | true | 是否显示模型缩略图 |

## 使用示例

> **注意**: 模型 ID 使用 UUID 格式（如 `b8c7264b-29e7-4091-bb73-3eac2fddb350`），可从搜索结果或网站链接中获取。

### 搜索模型

```
/smutbase_search anime
/smutbase_search genshin
/smutbase_search 2b nier
```

### 查看模型详情

```
/smutbase b8c7264b-29e7-4091-bb73-3eac2fddb350
/smutbase 31e26928-ca0a-4eb7-a671-a0cccf125171
```

### 搜索并指定页码

```
/smutbase_page 2 anime
/smutbase_page 3 genshin
```

### 获取最新模型

```
/smutbase_latest
/smutbase_latest 2
```

### 获取热门模型

```
/smutbase_popular
/smutbase_popular 3
```

### 按分类浏览

```
/smutbase_category models
/smutbase_category textures 2
/smutbase_category sceneries
```

### 获取随机模型

```
/smutbase_random
```

### 获取模型链接

```
/smutbase_url b8c7264b-29e7-4091-bb73-3eac2fddb350
```

### 清理缓存

```
/smutbase_clean
```

## 测试

运行测试：

```bash
# 使用 pytest
python -m pytest tests/test_smutbase.py -v

# 或直接运行
python tests/test_smutbase.py
```

## 项目结构

```
astrbot_plugin_smutba/
├── main.py              # 插件主文件
├── metadata.yaml        # 插件元数据
├── config_schema.json   # 配置模式定义
├── requirements.txt     # 依赖列表
├── README.md           # 说明文档
├── modules/            # 核心模块
│   ├── __init__.py
│   ├── client.py       # API 客户端
│   ├── model.py        # 数据模型
│   ├── consts.py       # 常量定义
│   └── errors.py       # 异常类
├── tests/              # 测试文件
│   ├── __init__.py
│   └── test_smutbase.py
└── data/               # 运行时数据（自动创建）
    └── cache/          # 缓存目录
```

## 注意事项

1. 本插件仅供学习和技术研究使用
2. 请遵守目标网站的服务条款
3. 建议配置代理以确保访问稳定性
4. 缩略图会自动缓存，发送下一条消息时会自动清理

## 许可证

MIT License

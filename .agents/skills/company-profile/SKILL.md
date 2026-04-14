---
name: company-profile
description: >
  获取 A 股上市公司画像：公司基本信息（主营业务、行业、成立/上市日期）、
  营收构成（按产品和地区拆分，含毛利率）、十大股东、最新业绩快报/预告。
  为深度分析提供"这家公司做什么、靠什么赚钱"的基础信息。
  当用户提到公司简介、主营业务、营收结构、股东信息、业绩快报、业绩预告，
  或在做个股综合分析需要了解公司基本面背景时触发。
  触发短语："公司简介"、"做什么的"、"主营业务"、"营收构成"、"收入结构"、
  "海外收入占比"、"十大股东"、"业绩快报"、"业绩预告"、
  "company profile"、"business overview"、"revenue breakdown"。
---

# 公司画像

获取 A 股上市公司的基础画像信息，回答"这家公司做什么、靠什么赚钱、谁在持有、最新业绩如何"。

## 前置条件

```bash
pip install akshare pandas
```

## 使用方式

```bash
# 获取完整公司画像
python .agents/skills/company-profile/scripts/profile.py <股票代码>

# 获取特定模块
python .agents/skills/company-profile/scripts/profile.py <股票代码> --module info
python .agents/skills/company-profile/scripts/profile.py <股票代码> --module revenue
python .agents/skills/company-profile/scripts/profile.py <股票代码> --module holders
python .agents/skills/company-profile/scripts/profile.py <股票代码> --module earnings
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 股票代码 | 6 位纯数字，如 `688267`、`600519` | 必填 |
| `--module` | 查询模块 | `all` |

### 模块说明

| 模块 | 内容 | 数据源 |
|------|------|--------|
| `info` | 公司名称、行业、主营业务描述、成立/上市日期、注册地 | 巨潮 stock_profile_cninfo |
| `revenue` | 按产品和按地区的营收拆分，含营收占比和毛利率 | 东财 stock_zygc_em |
| `holders` | 十大股东名单、持股比例、股东总数 | 东财 stock_main_stock_holder |
| `earnings` | 最新业绩快报（营收/净利/同比增长）和业绩预告 | 东财 stock_yjkb_em / stock_yjyg_em |

### 输出内容

Markdown 格式报告，包含：

1. **公司基本信息**：名称、行业、主营业务描述、公司简介
2. **主营构成**：按产品/行业分类的营收和毛利率；按地区分类的营收（识别海外收入占比）
3. **十大股东**：股东名称、持股比例、股东总数和人均持股
4. **最新业绩**：业绩快报（自动搜索最近已披露的报告期）和业绩预告

## 分析价值

| 信息 | 分析用途 |
|------|---------|
| 主营业务描述 | 理解公司做什么，判断所属赛道 |
| 按产品营收拆分 | 识别核心收入来源和利润贡献，判断第二曲线进展 |
| 按地区营收拆分 | 评估海外收入占比→汇率风险、国际化程度 |
| 产品毛利率差异 | 判断高毛利业务是否在增长，业务结构是否在优化 |
| 十大股东 | 判断股权集中度、是否有机构/社保入驻 |
| 业绩快报 | 获取最新披露的业绩数据（早于年报/季报） |

## 与其他技能的配合

| 场景 | 工作流 |
|------|--------|
| **个股综合分析** | 先 `company-profile` 了解公司做什么 → 再 `financial-data-analysis` 深入财务 → `technical-indicator` 看位置 |
| **估值分析** | `company-profile --module revenue` 看业务结构 → 判断应该对标哪个板块估值 |
| **风险识别** | 海外收入占比高 → 关注汇率；单一产品占比高 → 关注集中度风险 |

## 注意事项

- 股票代码使用纯 6 位数字（不带 sh/sz 前缀）
- `stock_zygc_em` 需要 SH/SZ 前缀，脚本内部自动转换
- 业绩快报会自动从最近的报告期向前搜索，找到第一个有数据的报告期
- 公司简介可能较长，脚本会截取前 500 字

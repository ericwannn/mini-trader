#!/bin/bash
# 发送今日摘要到微信（精简版）
set -e

cd /Users/ericwan/Investment/daily_digest

TODAY=$(date +%Y-%m-%d)
DIGEST_FILE="output/digests/digest_${TODAY}.md"
RAW_FILE="output/raw/raw_${TODAY}.json"

# 如果今天的 digest 不存在，先生成
if [ ! -f "$DIGEST_FILE" ]; then
    uv run minitrader digest
fi

if [ ! -f "$DIGEST_FILE" ]; then
    echo "今日摘要不存在，先运行采集..."
    uv run minitrader all
fi

# 提取议题数量
TOPIC_COUNT=$(grep -c "^## [0-9]" "$DIGEST_FILE" 2>/dev/null || echo 0)
ARTICLE_COUNT=$(grep -c "^### 文章:" "$DIGEST_FILE" 2>/dev/null || echo 0)

# 提取关键词
KEY_ITEMS=$(grep "^### 文章:" "$DIGEST_FILE" | head -3)

# 构建精简消息
echo "==== 每日宏观资产配置摘要 — ${TODAY} ===="
echo ""
echo "今日共整理 ${ARTICLE_COUNT} 篇分析文章，涵盖 ${TOPIC_COUNT} 个核心议题。"
echo ""
echo "--- 议题概览 ---"

# 提取每个议题的标题
grep "^## [0-9]" "$DIGEST_FILE" | while IFS= read -r line; do
    echo "  $line"
    # 提取该议题下的涉及品种
done

echo ""
echo "--- 涉及品种一览 ---"
grep -- "- 涉及品种:" "$DIGEST_FILE" | sed 's/- 涉及品种: //' | tr '、' '\n' | sed 's/^ *//' | sort -u | head -15

echo ""
echo "--- 今日参考文章 ---"
grep "^### 文章:" "$DIGEST_FILE" | head -8

echo ""
echo "---"
echo "完整摘要已保存至: ~/Investment/daily_digest/output/digests/digest_${TODAY}.md"
echo "原始数据: ~/Investment/daily_digest/output/raw/raw_${TODAY}.json"

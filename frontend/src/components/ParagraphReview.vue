<template>
  <div class="paragraph-review">
    <!-- 左侧：原文 -->
    <div class="review-left">
      <div class="paragraph-index">{{ paragraphLabel }}</div>
      <div class="original-text">
        <template v-if="hasTypos">
          <span
            v-for="(part, idx) in renderedOriginal"
            :key="idx"
            :class="part.class"
          >
            <template v-if="part.isTypo">
              <span class="typo-wrong">{{ part.text }}</span>
              <span class="typo-correct">{{ part.correct }}</span>
            </template>
            <template v-else>{{ part.text }}</template>
          </span>
        </template>
        <template v-else>
          <div
            v-for="(para, idx) in originalParagraphs"
            :key="idx"
            class="original-paragraph"
          >{{ para || '（本段无原文）' }}</div>
        </template>
      </div>
    </div>

    <!-- 右侧：批改 -->
    <div class="review-right">
      <div class="comment">{{ review.comment || '暂无批改意见' }}</div>

      <div v-if="review.typos && review.typos.length" class="correction-block">
        <div class="block-title">错别字</div>
        <div class="typo-list">
          <span
            v-for="(t, idx) in review.typos"
            :key="'t' + idx"
            class="typo-item"
          >
            <span class="wrong">{{ t.wrong }}</span>
            <span class="arrow">→</span>
            <span class="correct">{{ t.correct }}</span>
          </span>
        </div>
      </div>

      <div v-if="review.sentence_corrections && review.sentence_corrections.length" class="correction-block">
        <div class="block-title">病句修改</div>
        <div
          v-for="(sc, idx) in review.sentence_corrections"
          :key="'sc' + idx"
          class="sentence-item"
        >
          <div class="sentence-original">原：{{ sc.original }}</div>
          <div class="sentence-corrected">改：{{ sc.corrected }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  review: {
    type: Object,
    required: true,
  },
})

const hasTypos = computed(() => {
  return (props.review.typos || []).length > 0
})

const paragraphLabel = computed(() => {
  const idx = String(props.review.paragraph_index || '')
  if (idx.includes('-')) {
    return `第 ${idx} 段（合并段）`
  }
  return `第 ${idx} 段`
})

// 合并段用 ||| 分隔各段原文，展示时保留段落结构
const originalParagraphs = computed(() => {
  const original = props.review.original || ''
  return original.split('|||').map(p => p.trim()).filter(Boolean)
})

// 将原文按错字拆分，用于行内标注
const renderedOriginal = computed(() => {
  const original = props.review.original || ''
  const typos = props.review.typos || []
  if (!original || typos.length === 0) {
    return [{ text: original, class: '', isTypo: false }]
  }

  const parts = []
  let remaining = original

  typos.forEach((t) => {
    const wrong = t.wrong
    const idx = remaining.indexOf(wrong)
    if (idx >= 0) {
      if (idx > 0) {
        parts.push({ text: remaining.slice(0, idx), class: '', isTypo: false })
      }
      parts.push({
        text: wrong,
        correct: t.correct,
        class: 'typo-wrapper',
        isTypo: true,
      })
      remaining = remaining.slice(idx + wrong.length)
    }
  })

  if (remaining) {
    parts.push({ text: remaining, class: '', isTypo: false })
  }

  return parts
})
</script>

<style scoped>
.paragraph-review {
  display: flex;
  gap: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
  background: #fff;
}

.review-left {
  flex: 1;
  min-width: 0;
  padding: 16px;
  background: #fafafa;
  border-right: 1px solid #ebeef5;
}

.review-right {
  flex: 1;
  min-width: 0;
  padding: 16px;
}

.paragraph-index {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.original-text {
  line-height: 1.8;
  font-size: 15px;
  color: #303133;
  white-space: pre-wrap;
}

.original-paragraph {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #e4e7ed;
}

.original-paragraph:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.comment {
  line-height: 1.8;
  font-size: 14px;
  color: #303133;
  margin-bottom: 12px;
}

.correction-block {
  margin-top: 10px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.block-title {
  font-size: 13px;
  font-weight: bold;
  color: #606266;
  margin-bottom: 8px;
}

.typo-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.typo-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
}

.typo-item .wrong {
  color: #f56c6c;
  text-decoration: line-through;
}

.typo-item .arrow {
  color: #909399;
  font-size: 12px;
}

.typo-item .correct {
  color: #67c23a;
  font-weight: bold;
}

.sentence-item {
  margin-bottom: 8px;
  font-size: 13px;
}

.sentence-original {
  color: #f56c6c;
  margin-bottom: 2px;
}

.sentence-corrected {
  color: #67c23a;
}

/* 行内错字标注：错字加红色圆圈，正确字显示在右上方小圆圈内 */
.typo-wrapper {
  position: relative;
  display: inline-block;
  margin-right: 14px;
}

.typo-wrong {
  display: inline-block;
  color: #f56c6c;
  border: 1.5px solid #f56c6c;
  border-radius: 50%;
  padding: 0 3px;
  line-height: 1.2;
}

.typo-correct {
  position: absolute;
  top: -14px;
  right: -14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  font-size: 11px;
  color: #409eff;
  border: 1.5px solid #409eff;
  border-radius: 50%;
  background: #fff;
}

@media (max-width: 768px) {
  .paragraph-review {
    flex-direction: column;
  }
  .review-left {
    border-right: none;
    border-bottom: 1px solid #ebeef5;
  }
}
</style>

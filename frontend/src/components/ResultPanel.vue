<template>
  <div v-if="essay">
    <el-row :gutter="20">
      <!-- 左侧：图片与识别文本 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12">
        <div class="card">
          <div class="card-title">原始作文</div>
          <el-image
            :src="imageUrl"
            fit="contain"
            style="width: 100%; max-height: 400px; border-radius: 4px"
          />
        </div>

        <div class="card">
          <div class="card-title">识别文本</div>
          <div class="recognized-text">{{ essay.recognized_text || '暂无识别文本' }}</div>
        </div>
      </el-col>

      <!-- 右侧：评分与评语 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12">
        <div class="card">
          <div class="card-title">总分</div>
          <div class="score-header">
            <div class="score-number">{{ essay.total_score }}</div>
            <div class="score-label">满分 100 分</div>
          </div>
        </div>

        <div class="card">
          <div class="card-title">分项得分</div>
          <ScoreRadar :scores="essay.dimension_scores || {}" />
          <el-row :gutter="10" class="dimension-list">
            <el-col :span="6">
              <div class="dimension-item">
                <div class="dimension-value">{{ (essay.dimension_scores || {}).content }}</div>
                <div class="dimension-name">内容</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="dimension-item">
                <div class="dimension-value">{{ (essay.dimension_scores || {}).structure }}</div>
                <div class="dimension-name">结构</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="dimension-item">
                <div class="dimension-value">{{ (essay.dimension_scores || {}).language }}</div>
                <div class="dimension-name">语言</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="dimension-item">
                <div class="dimension-value">{{ (essay.dimension_scores || {}).writing }}</div>
                <div class="dimension-name">书写</div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-col>
    </el-row>

    <div class="card">
      <div class="card-title">总体评语</div>
      <p>{{ (essay.comments || {}).overall }}</p>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :sm="12">
        <div class="card">
          <div class="card-title" style="border-left-color: #67c23a">优点</div>
          <ul class="list">
            <li v-for="(item, index) in (essay.comments || {}).strengths || []" :key="'s' + index">
              {{ item }}
            </li>
          </ul>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12">
        <div class="card">
          <div class="card-title" style="border-left-color: #f56c6c">不足</div>
          <ul class="list">
            <li v-for="(item, index) in (essay.comments || {}).weaknesses || []" :key="'w' + index">
              {{ item }}
            </li>
          </ul>
        </div>
      </el-col>
    </el-row>

    <div class="card">
      <div class="card-title">段落批注</div>
      <el-timeline>
        <el-timeline-item
          v-for="(item, index) in essay.paragraph_comments || []"
          :key="'p' + index"
          :type="index === 0 ? 'primary' : ''"
        >
          <h4>第 {{ item.paragraph_index }} 段</h4>
          <p>{{ item.comment }}</p>
        </el-timeline-item>
      </el-timeline>
    </div>

    <div class="card">
      <div class="card-title">改进建议</div>
      <ol class="list">
        <li v-for="(item, index) in essay.suggestions || []" :key="'sg' + index">
          {{ item }}
        </li>
      </ol>
    </div>

    <div class="card" v-if="(essay.corrected_sentences || []).length > 0">
      <div class="card-title">病句修改</div>
      <el-table :data="essay.corrected_sentences" style="width: 100%">
        <el-table-column prop="original" label="原句" />
        <el-table-column prop="corrected" label="修改后" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ScoreRadar from './ScoreRadar.vue'
import { getEssayImageUrl } from '../api/essay'

const props = defineProps({
  essay: {
    type: Object,
    default: null,
  },
})

const imageUrl = computed(() => {
  if (!props.essay) return ''
  return getEssayImageUrl(props.essay.id)
})
</script>

<style scoped>
.score-header {
  text-align: center;
  padding: 20px 0;
}

.recognized-text {
  line-height: 1.8;
  white-space: pre-wrap;
  color: #606266;
  font-size: 15px;
}

.dimension-list {
  margin-top: 16px;
  text-align: center;
}

.dimension-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.dimension-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.dimension-name {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.list {
  padding-left: 20px;
  line-height: 1.8;
  color: #606266;
}

.list li {
  margin-bottom: 8px;
}
</style>

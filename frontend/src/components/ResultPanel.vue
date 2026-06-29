<template>
  <div v-if="essay">
    <!-- 第一行：审题 + 亮点 + 诊断 -->
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="8">
        <div class="card">
          <div class="card-title" style="border-left-color: #409eff">审题分析</div>
          <div v-if="essay.topic_analysis" class="topic-box">
            <p><strong>关键词：</strong>{{ topicKeywords }}</p>
            <p><strong>核心要求：</strong>{{ essay.topic_analysis.core_requirements }}</p>
            <p><strong>写作重点：</strong>{{ essay.topic_analysis.writing_focus }}</p>
            <p><strong>常见失分点：</strong>{{ essay.topic_analysis.common_pitfalls }}</p>
            <p><strong>评分侧重：</strong>{{ essay.topic_analysis.grading_emphasis }}</p>
          </div>
          <div v-else class="empty-tip">暂无审题分析</div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="8">
        <div class="card">
          <div class="card-title" style="border-left-color: #67c23a">本次亮点</div>
          <ul v-if="highlights.length" class="list highlight-list">
            <li v-for="(item, index) in highlights" :key="'h' + index">{{ item }}</li>
          </ul>
          <div v-else class="empty-tip">暂无亮点</div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="8">
        <div class="card">
          <div class="card-title" style="border-left-color: #e6a23c">深度诊断</div>
          <div v-if="essay.deep_diagnosis" class="diagnosis-box">
            <p><strong>问题表现：</strong>{{ essay.deep_diagnosis.problem }}</p>
            <p><strong>原因分析：</strong>{{ essay.deep_diagnosis.cause }}</p>
            <p><strong>改进方向：</strong>{{ essay.deep_diagnosis.suggestion }}</p>
          </div>
          <div v-else class="empty-tip">暂无深度诊断</div>
        </div>
      </el-col>
    </el-row>

    <!-- 分数区 -->
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="8">
        <div class="card">
          <div class="card-title">深圳中考得分</div>
          <div class="score-header">
            <div class="score-number">{{ essay.shenzhen_score }}</div>
            <div class="score-label">{{ essay.shenzhen_level || '未评定' }} / 满分 45 分</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="8">
        <div class="card">
          <div class="card-title">百分制得分</div>
          <div class="score-header">
            <div class="score-number">{{ essay.total_score }}</div>
            <div class="score-label">满分 100 分</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="8">
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

    <!-- 作文原稿 -->
    <div class="card">
      <div class="card-title">作文原稿</div>
      <p v-if="imageUrls.length > 1" style="color: #909399; font-size: 12px; margin-bottom: 10px">
        共 {{ imageUrls.length }} 张图片，按顺序组成完整作文
      </p>
      <div class="original-images">
        <el-image
          v-for="(url, idx) in imageUrls"
          :key="idx"
          :src="url"
          fit="contain"
          :preview-src-list="imageUrls"
          :initial-index="idx"
          class="original-image"
        />
      </div>
    </div>

    <!-- 识别文本编辑 -->
    <div class="card">
      <div class="card-title" style="display: flex; justify-content: space-between; align-items: center">
        <span>识别文本</span>
        <div>
          <el-button v-if="!isEditing" type="primary" text @click="startEdit">
            <el-icon><Edit /></el-icon> 编辑
          </el-button>
          <el-button v-if="isEditing" type="primary" text :loading="saving" @click="saveText">
            保存
          </el-button>
          <el-button v-if="isEditing" text @click="cancelEdit">取消</el-button>
          <el-button type="warning" :loading="reCorrecting" :disabled="isEditing" @click="handleReCorrect">
            <el-icon><RefreshRight /></el-icon> 重新批改
          </el-button>
        </div>
      </div>
      <div v-if="!isEditing" class="recognized-text">{{ essay.recognized_text || '暂无识别文本' }}</div>
      <el-input
        v-else
        v-model="editedText"
        type="textarea"
        :rows="12"
        resize="vertical"
        placeholder="请在此校对识别文本..."
      />
      <p v-if="essay.shenzhen_score_first !== undefined && essay.shenzhen_score_first !== null" style="color: #909399; font-size: 12px; margin-top: 10px">
        第一评 {{ essay.shenzhen_score_first }} 分，第二评 {{ essay.shenzhen_score_second || '-' }} 分
        <span v-if="essay.shenzhen_score_third !== undefined && essay.shenzhen_score_third !== null">，第三评 {{ essay.shenzhen_score_third }} 分</span>
      </p>
    </div>

    <!-- 精批细改：左右对照 -->
    <div class="card">
      <div class="card-title">精批细改</div>
      <ParagraphReview
        v-for="(item, index) in paragraphReviews"
        :key="'pr' + index"
        :review="item"
      />
      <div v-if="!paragraphReviews.length" class="empty-tip">暂无段落精批</div>
    </div>

    <!-- 写作提升 -->
    <div v-if="hasWritingImprovement" class="card">
      <div class="card-title">写作提升</div>
      <p class="section-subtitle">学习名家写法，明确提升方向</p>
      <div v-if="essay.writing_improvement.example_author" class="writing-author">
        {{ essay.writing_improvement.example_author }}
      </div>
      <p v-if="essay.writing_improvement.example_analysis" class="writing-text">
        {{ essay.writing_improvement.example_analysis }}
      </p>
      <p v-if="essay.writing_improvement.summary" class="writing-text">
        {{ essay.writing_improvement.summary }}
      </p>
    </div>

    <!-- 兜底：总体评语 + 旧版建议 -->
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

    <div v-if="(essay.suggestions || []).length" class="card">
      <div class="card-title">改进建议</div>
      <ol class="list">
        <li v-for="(item, index) in essay.suggestions" :key="'sg' + index">
          <template v-if="typeof item === 'string'">{{ item }}</template>
          <template v-else>
            <div class="suggestion-problem">问题：{{ item.problem }}</div>
            <div class="suggestion-advice">建议：{{ item.advice }}</div>
            <div v-if="item.original" class="suggestion-compare">
              <div class="suggestion-label">原文：</div>
              <div class="suggestion-text original">{{ item.original }}</div>
            </div>
            <div v-if="item.suggested" class="suggestion-compare">
              <div class="suggestion-label">改文：</div>
              <div class="suggestion-text suggested">{{ item.suggested }}</div>
            </div>
          </template>
        </li>
      </ol>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import ScoreRadar from './ScoreRadar.vue'
import ParagraphReview from './ParagraphReview.vue'
import { getEssayImageUrl, updateRecognizedText, reCorrectEssay } from '../api/essay'

const props = defineProps({
  essay: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['refresh'])

const isEditing = ref(false)
const editedText = ref('')
const saving = ref(false)
const reCorrecting = ref(false)

watch(
  () => props.essay?.recognized_text,
  (val) => {
    if (!isEditing.value) {
      editedText.value = val || ''
    }
  },
  { immediate: true }
)

function startEdit() {
  editedText.value = props.essay?.recognized_text || ''
  isEditing.value = true
}

function cancelEdit() {
  isEditing.value = false
  editedText.value = props.essay?.recognized_text || ''
}

async function saveText() {
  saving.value = true
  try {
    await updateRecognizedText(props.essay.id, editedText.value)
    ElMessage.success('识别文本已保存')
    isEditing.value = false
    emit('refresh')
  } catch (error) {
    console.error(error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleReCorrect() {
  reCorrecting.value = true
  try {
    await reCorrectEssay(props.essay.id)
    ElMessage.info('已开始重新批改，请稍候...')
    emit('refresh')
  } catch (error) {
    console.error(error)
    ElMessage.error(error.response?.data?.detail || '重新批改失败')
  } finally {
    reCorrecting.value = false
  }
}

const imageUrls = computed(() => {
  if (!props.essay) return []
  const count = (props.essay.image_paths || []).length || 1
  return Array.from({ length: count }, (_, idx) => getEssayImageUrl(props.essay.id, idx))
})

const topicKeywords = computed(() => {
  const keywords = (props.essay.topic_analysis || {}).topic_keywords || []
  return keywords.join('、') || '无'
})

const highlights = computed(() => {
  return props.essay.highlights || []
})

const hasWritingImprovement = computed(() => {
  const wi = props.essay.writing_improvement || {}
  return wi.example_author || wi.example_analysis || wi.summary
})

const paragraphReviews = computed(() => {
  let reviews = props.essay.paragraph_reviews || []
  // 兼容旧数据：如果只有 paragraph_comments，也展示出来
  if (!reviews.length && (props.essay.paragraph_comments || []).length) {
    reviews = (props.essay.paragraph_comments || []).map((item) => ({
      paragraph_index: item.paragraph_index,
      original: '',
      comment: item.comment,
      typos: [],
      sentence_corrections: [],
    }))
  }
  return reviews
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

.highlight-list li {
  color: #67c23a;
}

.empty-tip {
  color: #909399;
  font-size: 14px;
  text-align: center;
  padding: 20px 0;
}

.topic-box p,
.diagnosis-box p {
  margin-bottom: 8px;
  line-height: 1.6;
  font-size: 13px;
  color: #303133;
}

.section-subtitle {
  color: #909399;
  font-size: 13px;
  margin-top: -8px;
  margin-bottom: 12px;
}

.writing-author {
  font-weight: bold;
  margin-bottom: 8px;
  color: #303133;
}

.writing-text {
  line-height: 1.8;
  color: #606266;
  margin-bottom: 10px;
}

.suggestion-problem {
  font-weight: bold;
  color: #303133;
  margin-bottom: 6px;
}

.suggestion-advice {
  color: #606266;
  margin-bottom: 10px;
  line-height: 1.6;
}

.suggestion-compare {
  margin-top: 8px;
  padding: 10px;
  border-radius: 4px;
  background: #f5f7fa;
}

.suggestion-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.suggestion-text {
  line-height: 1.7;
  color: #303133;
}

.suggestion-text.original {
  color: #f56c6c;
}

.suggestion-text.suggested {
  color: #67c23a;
}

.original-images {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.original-image {
  width: 100%;
  max-height: 600px;
  border-radius: 4px;
  border: 1px solid #ebeef5;
  background: #fafafa;
}

:deep(.original-image img) {
  max-height: 600px;
  object-fit: contain;
}
</style>

<template>
  <div class="container">
    <div class="page-title">
      <h1>批改结果</h1>
      <p>查看 AI 对作文的识别结果与详细批改</p>
    </div>

    <div v-if="loading" class="card" style="text-align: center; padding: 60px">
      <el-icon class="is-loading" style="font-size: 40px; color: #409eff"><Loading /></el-icon>
      <p style="margin-top: 16px; color: #909399">正在识别与批改，请稍候...</p>
    </div>

    <template v-else-if="essay">
      <div class="card">
        <div class="card-title">作文信息</div>
        <el-descriptions :column="3" border>
          <el-descriptions-item label="学生">{{ essay.student_name || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="标题">{{ essay.title || '未命名' }}</el-descriptions-item>
          <el-descriptions-item label="年级">{{ essay.grade }}</el-descriptions-item>
          <el-descriptions-item label="日期">{{ essay.submitted_date || '未设置' }}</el-descriptions-item>
          <el-descriptions-item label="OCR 引擎">{{ essay.ocr_engine }}</el-descriptions-item>
          <el-descriptions-item label="文体">{{ genreText(essay.genre) }}</el-descriptions-item>
        </el-descriptions>
        <div style="margin-top: 16px">
          <el-button type="primary" @click="downloadPdf">
            <el-icon><Download /></el-icon>
            导出 PDF 报告
          </el-button>
        </div>
      </div>

      <ResultPanel :essay="essay" />
    </template>

    <div v-else class="card" style="text-align: center">
      <p>未找到作文记录</p>
      <el-button type="primary" @click="$router.push('/')">返回上传</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import ResultPanel from '../components/ResultPanel.vue'
import { getEssay, getEssayPdfUrl } from '../api/essay'

const route = useRoute()
const essay = ref(null)
const loading = ref(true)

const genreMap = {
  narrative: '记叙文',
  argumentation: '议论文',
  description: '说明文',
  prose: '散文',
}

function genreText(genre) {
  return genreMap[genre] || genre
}

function downloadPdf() {
  if (!essay.value) return
  window.open(getEssayPdfUrl(essay.value.id), '_blank')
}

async function fetchEssay() {
  try {
    const res = await getEssay(route.params.id)
    essay.value = res.data
  } catch (error) {
    console.error(error)
    ElMessage.error('获取批改结果失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchEssay)
</script>

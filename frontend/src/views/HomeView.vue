<template>
  <div class="container">
    <div class="page-title">
      <h1>AI 作文批改</h1>
      <p>选择学生并上传作文图片，Kimi 智能识别并给出专业批改意见</p>
    </div>

    <UploadCard
      :loading="loading"
      :students="students"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import UploadCard from '../components/UploadCard.vue'
import { uploadEssay, correctEssay, getEssayStatus, listStudents } from '../api/essay'

const router = useRouter()
const loading = ref(false)
const students = ref([])

async function loadStudents() {
  try {
    const res = await listStudents({ limit: 1000 })
    students.value = res.data.items
  } catch (error) {
    console.error(error)
  }
}

async function pollStatus(essayId, taskId) {
  const maxAttempts = 60
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await getEssayStatus(essayId)
      const status = res.data.status

      if (status === 'done') {
        return res.data.result
      } else if (status === 'failed') {
        throw new Error(res.data.error_message || '批改失败')
      }
    } catch (error) {
      throw error
    }
    await new Promise((resolve) => setTimeout(resolve, 2000))
  }
  throw new Error('批改超时，请稍后到历史记录中查看')
}

async function handleSubmit(form) {
  if (!form.student_id) {
    ElMessage.warning('请先选择学生')
    return
  }

  loading.value = true
  try {
    const formData = new FormData()
    formData.append('file', form.file)
    if (form.title) formData.append('title', form.title)
    formData.append('grade', form.grade)
    formData.append('student_id', form.student_id)
    formData.append('ocr_engine', form.ocr_engine)
    formData.append('genre', form.genre)

    // 上传图片
    const uploadRes = await uploadEssay(formData)
    const essayId = uploadRes.data.id

    // 触发异步批改
    const correctRes = await correctEssay(essayId)
    const taskId = correctRes.data.task_id

    ElMessage.info('已开始批改，请稍候...')

    // 轮询状态
    await pollStatus(essayId, taskId)

    ElMessage.success('批改完成')
    router.push(`/result/${essayId}`)
  } catch (error) {
    console.error(error)
    const msg = error.response?.data?.detail || error.message || '批改失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

onMounted(loadStudents)
</script>

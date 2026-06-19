<template>
  <div class="container">
    <div class="page-title">
      <h1>批改历史</h1>
      <p>查看过往批改记录</p>
    </div>

    <div class="card">
      <div class="card-title">查询条件</div>
      <el-form :inline="true" :model="queryForm">
        <el-form-item label="学生姓名">
          <el-input v-model="queryForm.student_name" placeholder="请输入学生姓名" clearable />
        </el-form-item>
        <el-form-item label="作文标题">
          <el-input v-model="queryForm.title" placeholder="请输入标题" clearable />
        </el-form-item>
        <el-form-item label="日期">
          <el-input v-model="queryForm.date" placeholder="格式：YYYYMMDD" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="全部" clearable>
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="done" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card">
      <el-table :data="essays" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="student_name" label="学生" width="100" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="grade" label="年级" width="90" />
        <el-table-column prop="submitted_date" label="日期" width="110" />
        <el-table-column prop="total_score" label="总分" width="90">
          <template #default="scope">
            <el-tag v-if="scope.row.total_score !== null" type="success">
              {{ scope.row.total_score }}
            </el-tag>
            <el-tag v-else type="info">未批改</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="statusType(scope.row.status)">
              {{ statusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="170">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button type="primary" size="small" @click="viewDetail(scope.row.id)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listEssays } from '../api/essay'

const router = useRouter()
const essays = ref([])
const loading = ref(false)

const queryForm = reactive({
  student_name: '',
  title: '',
  date: '',
  status: '',
})

function statusType(status) {
  const map = {
    pending: 'info',
    processing: 'warning',
    done: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

function statusText(status) {
  const map = {
    pending: '待处理',
    processing: '处理中',
    done: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

function viewDetail(id) {
  router.push(`/result/${id}`)
}

function handleSearch() {
  fetchList()
}

function resetQuery() {
  queryForm.student_name = ''
  queryForm.title = ''
  queryForm.date = ''
  queryForm.status = ''
  fetchList()
}

async function fetchList() {
  loading.value = true
  try {
    const params = {}
    if (queryForm.student_name) params.student_name = queryForm.student_name
    if (queryForm.title) params.title = queryForm.title
    if (queryForm.date) params.date = queryForm.date
    if (queryForm.status) params.status = queryForm.status

    const res = await listEssays(params)
    essays.value = res.data.items
  } catch (error) {
    console.error(error)
    ElMessage.error('获取历史记录失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)
</script>

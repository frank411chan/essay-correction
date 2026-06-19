<template>
  <div class="container">
    <div class="page-title">
      <h1>学生管理</h1>
      <p>管理学生信息，批改作文时选择对应学生</p>
    </div>

    <div class="card">
      <div class="card-title">查询条件</div>
      <el-form :inline="true" :model="queryForm">
        <el-form-item label="姓名">
          <el-input v-model="queryForm.name" placeholder="请输入姓名" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
          <el-button type="success" @click="openDialog()">新增学生</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card">
      <el-table :data="students" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="grade" label="年级" />
        <el-table-column prop="class_name" label="班级" />
        <el-table-column prop="student_no" label="学号" />
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="primary" size="small" @click="openDialog(scope.row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑学生' : '新增学生'"
      width="500px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="年级">
          <el-select v-model="form.grade" placeholder="请选择年级" style="width: 100%">
            <el-option label="小学" value="小学" />
            <el-option label="初中" value="初中" />
            <el-option label="高中" value="高中" />
            <el-option label="大学/成人" value="大学/成人" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-input v-model="form.class_name" placeholder="请输入班级" />
        </el-form-item>
        <el-form-item label="学号">
          <el-input v-model="form.student_no" placeholder="请输入学号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listStudents, createStudent, updateStudent, deleteStudent } from '../api/essay'

const students = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)

const queryForm = reactive({
  name: '',
})

const form = reactive({
  name: '',
  grade: '初中',
  class_name: '',
  student_no: '',
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

function openDialog(student = null) {
  if (student) {
    isEdit.value = true
    currentId.value = student.id
    form.name = student.name
    form.grade = student.grade || '初中'
    form.class_name = student.class_name || ''
    form.student_no = student.student_no || ''
  } else {
    isEdit.value = false
    currentId.value = null
    form.name = ''
    form.grade = '初中'
    form.class_name = ''
    form.student_no = ''
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入姓名')
    return
  }

  try {
    if (isEdit.value) {
      await updateStudent(currentId.value, { ...form })
      ElMessage.success('修改成功')
    } else {
      await createStudent({ ...form })
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch (error) {
    console.error(error)
    ElMessage.error('操作失败')
  }
}

async function handleDelete(id) {
  try {
    await ElMessageBox.confirm('确定要删除该学生吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteStudent(id)
    ElMessage.success('删除成功')
    fetchList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error('删除失败')
    }
  }
}

function handleSearch() {
  fetchList()
}

function resetQuery() {
  queryForm.name = ''
  fetchList()
}

async function fetchList() {
  loading.value = true
  try {
    const params = {}
    if (queryForm.name) params.name = queryForm.name
    const res = await listStudents(params)
    students.value = res.data.items
  } catch (error) {
    console.error(error)
    ElMessage.error('获取学生列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)
</script>

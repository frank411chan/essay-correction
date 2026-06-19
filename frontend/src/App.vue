<template>
  <el-container>
    <el-header class="app-header">
      <div class="header-content">
        <div class="logo">
          <el-icon><EditPen /></el-icon>
          <span>作文批改系统</span>
        </div>
        <el-menu
          :default-active="activeIndex"
          class="nav-menu"
          mode="horizontal"
          router
          background-color="#409eff"
          text-color="#fff"
          active-text-color="#fff"
        >
          <el-menu-item index="/">上传批改</el-menu-item>
          <el-menu-item index="/batch">批量批改</el-menu-item>
          <el-menu-item index="/history">历史记录</el-menu-item>
          <el-menu-item index="/students">学生管理</el-menu-item>
        </el-menu>
      </div>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
    <el-footer class="app-footer">
      <p>基于 Kimi 多模态大模型 · 本地部署</p>
    </el-footer>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeIndex = computed(() => route.path)
</script>

<style scoped>
.app-header {
  background-color: #409eff;
  padding: 0;
  height: 60px;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.logo {
  display: flex;
  align-items: center;
  color: #fff;
  font-size: 20px;
  font-weight: bold;
}

.logo .el-icon {
  margin-right: 8px;
  font-size: 24px;
}

.nav-menu {
  border-bottom: none;
}

.app-footer {
  text-align: center;
  color: #909399;
  padding: 20px;
}
</style>

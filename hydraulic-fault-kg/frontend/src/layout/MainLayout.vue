<template>
  <el-container style="height: 100vh">
    <el-aside width="230px" style="background: #304156; overflow-y: auto">
      <div style="padding: 16px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1); cursor: pointer" @click="$router.push('/dashboard')">
        <span style="color: #fff; font-size: 15px; font-weight: bold">液压故障KG系统</span>
      </div>

      <el-menu :default-active="route.path" router background-color="#304156" text-color="#bfcbd9" active-text-color="#409EFF" style="border-right: none">

        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon><span>系统首页</span>
        </el-menu-item>

        <el-sub-menu index="build">
          <template #title><el-icon><Setting /></el-icon><span>知识图谱构建</span></template>
          <el-menu-item index="/sources"><el-icon><Document /></el-icon><span>来源资料管理</span></el-menu-item>
          <el-menu-item index="/extraction"><el-icon><Search /></el-icon><span>事件抽取与证据锚定</span></el-menu-item>
          <el-menu-item index="/build-process"><el-icon><Operation /></el-icon><span>构建过程</span></el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/kg">
          <el-icon><Share /></el-icon><span>知识图谱展示</span>
        </el-menu-item>

        <el-menu-item index="/qa" style="background: rgba(245,108,108,0.08)">
          <el-icon><ChatDotRound /></el-icon><span>大模型图谱问答</span>
          <el-tag size="small" type="danger" style="margin-left: 6px">必须</el-tag>
        </el-menu-item>

        <el-menu-item index="/recommend">
          <el-icon><MagicStick /></el-icon><span>维修方案推荐</span>
        </el-menu-item>

        <el-menu-item index="/sample-analysis">
          <el-icon><DataAnalysis /></el-icon><span>结果分析</span>
          <el-tag size="small" type="warning" style="margin-left: 6px">新增</el-tag>
        </el-menu-item>

        <el-menu-item index="/import" style="background: rgba(144,147,153,0.06)">
          <el-icon><Upload /></el-icon><span>资料导入分析</span>
          <el-tag size="small" type="info" style="margin-left: 6px">可选</el-tag>
        </el-menu-item>

        <el-sub-menu index="admin">
          <template #title><el-icon><Monitor /></el-icon><span>系统管理</span></template>
          <el-menu-item index="/admin"><el-icon><DataBoard /></el-icon><span>后台管理</span></el-menu-item>
          <el-menu-item index="/metrics"><el-icon><DataAnalysis /></el-icon><span>构建质量评价</span></el-menu-item>
          <el-menu-item index="/advantages"><el-icon><TrophyBase /></el-icon><span>系统方法优势</span></el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/report">
          <el-icon><Notebook /></el-icon><span>汇报展示</span>
        </el-menu-item>

      </el-menu>

      <div style="position: absolute; bottom: 0; width: 230px; padding: 12px; text-align: center; border-top: 1px solid rgba(255,255,255,0.1)">
        <span style="color: #909399; font-size: 11px">机理约束 · 证据可追溯 · 双时态</span>
      </div>
    </el-aside>

    <el-container>
      <el-header style="background: #fff; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e4e7ed; padding: 0 20px; height: 50px">
        <span style="font-size: 16px; font-weight: 600">{{ route.meta.title }}</span>
        <div>
          <el-tag type="success" size="small" style="margin-right: 12px">后端: 127.0.0.1:8000</el-tag>
          <el-button size="small" @click="$router.push('/login')">退出</el-button>
        </div>
      </el-header>
      <el-main style="background: #f0f2f5; padding: 20px">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

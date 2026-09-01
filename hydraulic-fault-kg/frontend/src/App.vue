<template>
  <router-view v-if="route.path === '/login'" />
  <MainLayout v-else />
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import MainLayout from '@/layout/MainLayout.vue'

const route = useRoute()
</script>

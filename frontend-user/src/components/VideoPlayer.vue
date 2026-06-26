<template>
  <div class="video-player">
    <video :src="videoUrl" controls :poster="thumbnail" style="width: 100%; max-width: 800px" />
  </div>
</template>

<script setup>
defineProps({ videoUrl: String, thumbnail: String })
</script>

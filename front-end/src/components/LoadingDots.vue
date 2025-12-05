<template>
  <div class="loading-dots">
    <div class="dot"></div>
    <div class="dot"></div>
    <div class="dot"></div>
    <div class="dot"></div>
  </div>
</template>

<style scoped>
.loading-dots {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 200px; /* Default height for containers */
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  background-color: #a855f7; /* Purple accent color */
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style>



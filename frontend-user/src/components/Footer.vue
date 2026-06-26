<template>
  <footer class="site-footer">
    <div class="footer-glow"></div>
    <div class="footer-inner">
      <div class="footer-brand">
        <div class="brand-logo">
          <svg viewBox="0 0 32 32" width="28" height="28" fill="none">
            <rect width="32" height="32" rx="8" fill="url(#fLogo)"/>
            <defs><linearGradient id="fLogo" x1="0" y1="0" x2="32" y2="32"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient></defs>
            <path d="M12 10l10 6-10 6V10z" fill="#fff"/>
          </svg>
          <span>短视频复刻</span>
        </div>
        <p class="brand-desc">AI 驱动的爆款短视频一键复刻平台</p>
        <div class="brand-social">
          <a href="#" class="social-icon" title="微信">微</a>
          <a href="#" class="social-icon" title="微博">博</a>
          <a href="#" class="social-icon" title="抖音">抖</a>
        </div>
      </div>
      <div class="footer-links">
        <div class="link-group">
          <h4>产品</h4>
          <a href="/video/create">视频解析</a>
          <a href="/video/create">视频创作</a>
          <a href="/watermark">去水印</a>
          <a href="/membership">会员服务</a>
        </div>
        <div class="link-group">
          <h4>支持</h4>
          <a href="#">使用教程</a>
          <a href="#">常见问题</a>
          <a href="#">联系我们</a>
          <a href="#">意见反馈</a>
        </div>
        <div class="link-group">
          <h4>法律</h4>
          <a href="#">用户协议</a>
          <a href="#">隐私政策</a>
          <a href="#">版权声明</a>
        </div>
      </div>
    </div>
    <div class="footer-bottom">
      <p>&copy; {{ new Date().getFullYear() }} 爆款短视频复刻SaaS平台. All rights reserved.</p>
    </div>
  </footer>
</template>

<script setup>
</script>

<style scoped>
.site-footer {
  background: linear-gradient(180deg, #0f172a 0%, #071526 100%);
  color: rgba(255, 255, 255, 0.6);
  margin-top: auto;
  position: relative;
  overflow: hidden;
}
.footer-glow {
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.3), transparent);
}
.footer-inner {
  max-width: 1280px; margin: 0 auto;
  padding: 56px 24px 40px;
  display: flex; gap: 64px;
}
.footer-brand { flex-shrink: 0; }
.brand-logo {
  display: flex; align-items: center; gap: 10px;
  font-size: 1.25rem; font-weight: 700; color: #fff;
  margin-bottom: 12px;
}
.brand-desc { font-size: 0.85rem; line-height: 1.7; max-width: 240px; margin-bottom: 20px; }
.brand-social { display: flex; gap: 10px; }
.social-icon {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
  transition: all 0.2s;
}
.social-icon:hover { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.footer-links { display: flex; gap: 56px; flex: 1; justify-content: flex-end; }
.link-group h4 {
  color: #fff; font-size: 0.9rem; margin-bottom: 16px;
  font-weight: 600; letter-spacing: 0.5px;
}
.link-group a {
  display: block; font-size: 0.85rem; padding: 5px 0;
  color: rgba(255, 255, 255, 0.5); transition: all 0.2s;
}
.link-group a:hover { color: #fff; transform: translateX(4px); }
.footer-bottom {
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  text-align: center; padding: 20px 24px;
  font-size: 0.8rem; color: rgba(255, 255, 255, 0.35);
}
@media (max-width: 768px) {
  .footer-inner { flex-direction: column; gap: 32px; padding: 40px 16px 24px; }
  .footer-links { gap: 32px; justify-content: flex-start; flex-wrap: wrap; }
  .link-group { flex: 1; min-width: 100px; }
  .brand-desc { max-width: 100%; }
}
</style>
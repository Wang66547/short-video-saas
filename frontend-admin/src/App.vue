<template>
  <router-view />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --admin-primary: #60a5fa;
  --admin-primary-light: #93c5fd;
  --admin-accent: #3b82f6;
  --admin-bg: #0f172a;
  --admin-white: #1e293b;
  --admin-text: #e2e8f0;
  --admin-text-secondary: #94a3b8;
  --admin-text-light: #64748b;
  --admin-border: #334155;
  --admin-border-light: #1e293b;
  --admin-success: #10b981;
  --admin-warning: #f59e0b;
  --admin-danger: #ef4444;
  --admin-purple: #a78bfa;
  --admin-radius: 12px;
  --admin-radius-lg: 16px;
  --admin-shadow: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
  --admin-shadow-md: 0 4px 6px -1px rgba(0,0,0,0.4), 0 2px 4px -2px rgba(0,0,0,0.3);
  --admin-shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.5), 0 4px 6px -4px rgba(0,0,0,0.4);
  --admin-sidebar-bg: #020617;
  --admin-sidebar-active: #3b82f6;
}

html { font-size: 14px; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--admin-bg);
  color: var(--admin-text);
  -webkit-font-smoothing: antialiased;
}

a { text-decoration: none; color: inherit; }
#app { min-height: 100vh; background: var(--admin-bg); }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
::-webkit-scrollbar-track { background: #0f172a; }

.el-card {
  background: var(--admin-white) !important;
  border: 1px solid var(--admin-border) !important;
  border-radius: var(--admin-radius-lg) !important;
  box-shadow: var(--admin-shadow) !important;
  color: var(--admin-text) !important;
}
.el-card__body {
  color: var(--admin-text) !important;
}
.el-table {
  border-radius: var(--admin-radius) !important;
  overflow: hidden;
  background: var(--admin-white) !important;
}
.el-table th.el-table__cell {
  background: var(--admin-bg) !important;
  color: var(--admin-text-secondary) !important;
  border-color: var(--admin-border) !important;
}
.el-table tr {
  background: var(--admin-white) !important;
}
.el-table td.el-table__cell {
  border-color: var(--admin-border) !important;
  color: var(--admin-text) !important;
}
.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background: var(--admin-bg) !important;
}
.el-input__wrapper {
  border-radius: var(--admin-radius) !important;
  background: var(--admin-bg) !important;
  border-color: var(--admin-border) !important;
  box-shadow: none !important;
}
.el-input__inner {
  color: var(--admin-text) !important;
}
.el-input__wrapper.is-focus {
  border-color: var(--admin-accent) !important;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15) !important;
}
.el-button--primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  border: none !important;
  box-shadow: 0 2px 8px rgba(59,130,246,0.25) !important;
}
.el-dialog {
  background: var(--admin-white) !important;
  border: 1px solid var(--admin-border) !important;
}
.el-dialog__title {
  color: var(--admin-text) !important;
}
.el-message-box {
  background: var(--admin-white) !important;
  border-color: var(--admin-border) !important;
}
.el-message-box__title {
  color: var(--admin-text) !important;
}
.el-message-box__message {
  color: var(--admin-text-secondary) !important;
}
.el-pagination {
  color: var(--admin-text-secondary) !important;
}
.el-pagination button {
  background: var(--admin-white) !important;
  color: var(--admin-text-secondary) !important;
}
.el-pagination .el-pager li {
  background: var(--admin-white) !important;
  color: var(--admin-text-secondary) !important;
}
.el-pagination .el-pager li.is-active {
  background: var(--admin-accent) !important;
  color: #fff !important;
}
.el-select-dropdown {
  background: var(--admin-white) !important;
  border-color: var(--admin-border) !important;
}
.el-select-dropdown__item {
  color: var(--admin-text) !important;
}
.el-select-dropdown__item:hover {
  background: var(--admin-bg) !important;
}
.el-select-dropdown__item.selected {
  color: var(--admin-accent) !important;
  font-weight: 600 !important;
}
.el-form-item__label {
  color: var(--admin-text) !important;
}
.el-upload-dragger {
  background: var(--admin-bg) !important;
  border-color: var(--admin-border) !important;
}
.el-upload-dragger:hover {
  border-color: var(--admin-accent) !important;
}
.el-textarea__inner {
  background: var(--admin-bg) !important;
  border-color: var(--admin-border) !important;
  color: var(--admin-text) !important;
}
.el-textarea__inner:focus {
  border-color: var(--admin-accent) !important;
}

.text-success { color: var(--admin-success); }
.text-warning { color: var(--admin-warning); }
.text-danger { color: var(--admin-danger); }
.text-muted { color: var(--admin-text-light); }
.gradient-text {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>

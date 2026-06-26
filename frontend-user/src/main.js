import { createApp } from "vue"
import { createPinia } from "pinia"
import ElementPlus from "element-plus"
import "element-plus/dist/index.css"
import zhCn from "element-plus/es/locale/lang/zh-cn"
import * as ElementPlusIconsVue from "@element-plus/icons-vue"
import App from "./App.vue"
import router from "./router"
import "@/styles/main.scss"

const app = createApp(App)

// 注册所有图标
for (const [k, c] of Object.entries(ElementPlusIconsVue)) {
  app.component(k, c)
}

app.use(createPinia())
  .use(router)
  .use(ElementPlus, { locale: zhCn })
  .mount("#app")
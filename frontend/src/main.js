import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { createI18n } from 'vue-i18n';

import App from './App.vue'
import router from './router'

import zh from './locales/zh.js';
import en from './locales/en.js';

const i18n = createI18n({
  legacy: false, // Use Composition API
  locale: 'zh', // Set default locale to Chinese
  fallbackLocale: 'en', // Fallback to English
  messages: {
    zh,
    en,
  },
});

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, {
  locale: zhCn, // Element Plus components will use Chinese
})
app.use(i18n) // Use vue-i18n

app.mount('#app')

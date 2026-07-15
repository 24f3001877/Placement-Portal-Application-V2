// RecruitRadar — main.js

const { createApp } = Vue

const App = {
  name: 'App',
  components: { NavBar, AlertMsg },
  template: `
    <div>
      <nav-bar></nav-bar>
      <main>
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
      <footer class="text-center text-muted py-4 mt-5 border-top small">
        &copy; {{ year }} RecruitRadar — Placement Portal
      </footer>
    </div>
  `,
  computed: {
    year() { return new Date().getFullYear() }
  }
}

const app = createApp(App)
app.use(router)

app.component('NavBar', NavBar)
app.component('AlertMsg', AlertMsg)

// Make rrStore and helpers available in ALL component templates 
// Without this, templates can't access plain global JS variables.
app.config.globalProperties.rrStore = rrStore
app.config.globalProperties.rrShowAlert = rrShowAlert
app.config.globalProperties.rrIsLoggedIn = rrIsLoggedIn
app.config.globalProperties.rrRole = rrRole
app.config.globalProperties.rrApi = rrApi
app.config.globalProperties.rrGetError = rrGetError

app.mount('#app')
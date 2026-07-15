// RecruitRadar — components/NavBar.js
// Role-aware top navbar. Shows different links based on rrStore.user.role.

const NavBar = {
  name: 'NavBar',
  template: `
    <nav class="navbar navbar-expand-lg rr-navbar mb-0">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">
          <i class="bi bi-radar me-1"></i>RecruitRadar
        </router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#rrNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="rrNav">
          <ul class="navbar-nav ms-auto align-items-lg-center gap-1">

            <!-- Public -->
            <template v-if="!isLoggedIn">
              <li class="nav-item"><router-link class="nav-link" to="/">Home</router-link></li>
              <li class="nav-item"><router-link class="nav-link" to="/login">Login / Register</router-link></li>
            </template>

            <!-- Admin links -->
            <template v-if="role === 'admin'">
              <li class="nav-item"><router-link class="nav-link" to="/admin/dashboard">Dashboard</router-link></li>
              <li class="nav-item"><router-link class="nav-link" to="/admin/companies">Companies</router-link></li>
              <li class="nav-item"><router-link class="nav-link" to="/admin/students">Students</router-link></li>
              <li class="nav-item"><router-link class="nav-link" to="/admin/drives">Drives</router-link></li>
              <li class="nav-item"><router-link class="nav-link" to="/admin/applications">Applications</router-link></li>
            </template>

            <!-- Company links -->
            <template v-if="role === 'company'">
              <li class="nav-item"><router-link class="nav-link" to="/company/dashboard">Dashboard</router-link></li>
              <li class="nav-item"><router-link class="nav-link" to="/company/drives">My Drives</router-link></li>
            </template>

            <!-- Student links -->
            <template v-if="role === 'student'">
              <li class="nav-item"><router-link class="nav-link" to="/student/dashboard">Dashboard</router-link></li>
              <li class="nav-item"><router-link class="nav-link" to="/student/profile">My Profile</router-link></li>
              <li class="nav-item"><router-link class="nav-link" to="/student/history">Applications</router-link></li>
              <li class="nav-item"><router-link class="nav-link" to="/student/ats-check">ATS Checker</router-link></li>
            </template>

            <!-- User info + logout -->
            <template v-if="isLoggedIn">
              <li class="nav-item">
                <span class="nav-link text-warning">
                  <i class="bi bi-person-circle me-1"></i>{{ displayName }}
                  <span class="badge bg-secondary ms-1" style="font-size:0.7rem;">{{ role }}</span>
                </span>
              </li>
              <li class="nav-item">
                <button class="btn btn-sm btn-outline-light ms-1" @click="logout">
                  <i class="bi bi-box-arrow-right me-1"></i>Logout
                </button>
              </li>
            </template>

          </ul>
        </div>
      </div>
    </nav>
  `,
  computed: {
    isLoggedIn() { return rrIsLoggedIn() },
    role() { return rrRole() },
    displayName() {
      if (!rrStore.user) return ''
      return rrStore.user.full_name || rrStore.user.company_name || rrStore.user.email
    }
  },
  methods: {
    async logout() {
      try { await rrApi.post('/api/auth/logout') } catch (e) { /* ignore */ }
      rrClearAuth()
      this.$router.push('/login')
      rrShowAlert('Logged out successfully.', 'info')
    }
  }
}

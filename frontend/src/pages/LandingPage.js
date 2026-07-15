// RecruitRadar — pages/LandingPage.js
// Public landing page — shows portal stats without requiring login.


const LandingPage = {
  name: 'LandingPage',
  template: `
    <div>
      <!-- Hero -->
      <div style="background:linear-gradient(135deg,#0f172a 60%,#1d4ed8);color:#fff;padding:72px 0 56px;">
        <div class="container text-center">
          <h1 class="display-4 fw-bold mb-2">
            <i class="bi bi-radar text-warning me-2"></i>RecruitRadar
          </h1>
          <p class="lead mb-4" style="color:#94a3b8;">
            Your institute's smart placement portal — connecting students with opportunities.
          </p>
          <router-link to="/login" class="btn btn-warning btn-lg fw-semibold px-5">
            Get Started <i class="bi bi-arrow-right ms-2"></i>
          </router-link>
        </div>
      </div>

      <!-- Stats -->
      <div class="container py-5">
        <h5 class="text-center text-muted mb-4 fw-semibold text-uppercase" style="letter-spacing:1px;">
          Portal at a Glance
        </h5>
        <div class="row g-4 justify-content-center">
          <div class="col-6 col-md-3" v-for="stat in stats" :key="stat.label">
            <div class="card rr-card rr-stat-card text-center p-3">
              <div class="fs-1 fw-bold" style="color:var(--rr-primary);">{{ stat.value }}</div>
              <div class="text-muted small">{{ stat.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- How it works -->
      <div class="bg-white py-5">
        <div class="container">
          <h5 class="text-center fw-semibold mb-5 text-uppercase text-muted" style="letter-spacing:1px;">How It Works</h5>
          <div class="row g-4 text-center">
            <div class="col-md-4" v-for="step in steps" :key="step.title">
              <div class="p-4">
                <div class="mb-3">
                  <i :class="step.icon" style="font-size:2.5rem;color:var(--rr-primary);"></i>
                </div>
                <h6 class="fw-bold">{{ step.title }}</h6>
                <p class="text-muted small">{{ step.desc }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      stats: [
        { label: 'Students Registered', value: '—' },
        { label: 'Companies Onboard', value: '—' },
        { label: 'Active Drives', value: '—' },
        { label: 'Placements Done', value: '—' },
      ],
      steps: [
        { icon: 'bi bi-building-add', title: 'Companies Register', desc: 'Companies sign up and await admin approval to post placement drives.' },
        { icon: 'bi bi-person-badge', title: 'Students Apply', desc: 'Students browse approved drives and apply based on their eligibility.' },
        { icon: 'bi bi-trophy', title: 'Get Placed', desc: 'Companies shortlist, interview, and select candidates through the portal.' },
      ]
    }
  },
  async mounted() {
    // Fetch public stats — no auth needed (admin dashboard cached endpoint)
    // We use a lightweight public stats endpoint
    try {
      const res = await axios.get('/api/public/stats')
      const d = res.data
      this.stats = [
        { label: 'Students Registered', value: d.total_students },
        { label: 'Companies Onboard',   value: d.total_companies },
        { label: 'Active Drives',       value: d.total_drives },
        { label: 'Placements Done',     value: d.total_placed },
      ]
    } catch (e) { /* stats unavailable, keep dashes */ }
  }
}

// RecruitRadar — pages/LoginPage.js

// Tab 1: Login (all roles), Tab 2: Student Register, Tab 3: Company Register.

const LoginPage = {
  name: 'LoginPage',
  template: `
    <div class="container py-5" style="max-width:520px;">
      <div class="text-center mb-4">
        <h2 class="fw-bold" style="color:var(--rr-secondary);">
          <i class="bi bi-radar text-warning me-2"></i>RecruitRadar
        </h2>
        <p class="text-muted">Placement Portal — Login or Register</p>
      </div>

      <alert-msg></alert-msg>

      <!-- Tabs -->
      <ul class="nav nav-tabs mb-4" role="tablist">
        <li class="nav-item">
          <button class="nav-link" :class="{active: tab==='login'}" @click="tab='login'">
            <i class="bi bi-box-arrow-in-right me-1"></i>Login
          </button>
        </li>
        <li class="nav-item">
          <button class="nav-link" :class="{active: tab==='student'}" @click="tab='student'">
            <i class="bi bi-mortarboard me-1"></i>Student Register
          </button>
        </li>
        <li class="nav-item">
          <button class="nav-link" :class="{active: tab==='company'}" @click="tab='company'">
            <i class="bi bi-building me-1"></i>Company Register
          </button>
        </li>
      </ul>

      <!-- LOGIN FORM -->
      <div v-if="tab==='login'" class="card rr-card p-4">
        <h5 class="mb-3 fw-semibold">Welcome back</h5>
        <div class="mb-3">
          <label class="form-label">Email</label>
          <input type="email" class="form-control" v-model="login.email" placeholder="you@example.com" required />
        </div>
        <div class="mb-3">
          <label class="form-label">Password</label>
          <input type="password" class="form-control" v-model="login.password" placeholder="••••••••" required />
        </div>
        <button class="btn btn-primary w-100 fw-semibold" @click="doLogin" :disabled="rrStore.loading">
          <span v-if="rrStore.loading" class="spinner-border spinner-border-sm me-2"></span>
          Login
        </button>
        <p class="text-muted small mt-3 mb-0 text-center">
          Admin? Use admin credentials. No registration needed.
        </p>
      </div>

      <!-- STUDENT REGISTER -->
      <div v-if="tab==='student'" class="card rr-card p-4">
        <h5 class="mb-3 fw-semibold">Student Registration</h5>
        <div class="row g-3">
          <div class="col-12">
            <label class="form-label">Full Name <span class="text-danger">*</span></label>
            <input class="form-control" v-model="sreg.full_name" placeholder="John Doe" required />
          </div>
          <div class="col-12">
            <label class="form-label">Email <span class="text-danger">*</span></label>
            <input type="email" class="form-control" v-model="sreg.email" placeholder="student@college.edu" required />
          </div>
          <div class="col-6">
            <label class="form-label">Password <span class="text-danger">*</span></label>
            <input type="password" class="form-control" v-model="sreg.password" placeholder="Min 8 chars" required />
          </div>
          <div class="col-6">
            <label class="form-label">Branch <span class="text-danger">*</span></label>
            <select class="form-select" v-model="sreg.branch" required>
              <option value="">Select branch</option>
              <option>CSE</option><option>ECE</option><option>EEE</option>
              <option>ME</option><option>CE</option><option>IT</option><option>Other</option>
            </select>
          </div>
          <div class="col-6">
            <label class="form-label">Year <span class="text-danger">*</span></label>
            <select class="form-select" v-model.number="sreg.year" required>
              <option value="">Year</option>
              <option :value="1">1st</option><option :value="2">2nd</option>
              <option :value="3">3rd</option><option :value="4">4th</option>
            </select>
          </div>
          <div class="col-6">
            <label class="form-label">CGPA <span class="text-danger">*</span></label>
            <input type="number" step="0.01" min="0" max="10" class="form-control"
              v-model.number="sreg.cgpa" placeholder="e.g. 8.5" required />
          </div>
          <div class="col-6">
            <label class="form-label">Phone</label>
            <input class="form-control" v-model="sreg.phone" placeholder="Optional" />
          </div>
          <div class="col-6">
            <label class="form-label">Skills</label>
            <input class="form-control" v-model="sreg.skills" placeholder="Python, React, ..." />
          </div>
          <div class="col-12">
            <button class="btn btn-primary w-100 fw-semibold" @click="doStudentRegister" :disabled="rrStore.loading">
              <span v-if="rrStore.loading" class="spinner-border spinner-border-sm me-2"></span>
              Register as Student
            </button>
          </div>
        </div>
      </div>

      <!-- COMPANY REGISTER -->
      <div v-if="tab==='company'" class="card rr-card p-4">
        <h5 class="mb-3 fw-semibold">Company Registration</h5>
        <div class="row g-3">
          <div class="col-12">
            <label class="form-label">Company Name <span class="text-danger">*</span></label>
            <input class="form-control" v-model="creg.company_name" placeholder="Infosys" required />
          </div>
          <div class="col-12">
            <label class="form-label">Email <span class="text-danger">*</span></label>
            <input type="email" class="form-control" v-model="creg.email" placeholder="hr@acmecorp.com" required />
          </div>
          <div class="col-6">
            <label class="form-label">Password <span class="text-danger">*</span></label>
            <input type="password" class="form-control" v-model="creg.password" placeholder="Min 8 chars" required />
          </div>
          <div class="col-6">
            <label class="form-label">Industry</label>
            <input class="form-control" v-model="creg.industry" placeholder="IT, Finance, ..." />
          </div>
          <div class="col-6">
            <label class="form-label">Location</label>
            <input class="form-control" v-model="creg.location" placeholder="Bangalore" />
          </div>
          <div class="col-6">
            <label class="form-label">Website</label>
            <input class="form-control" v-model="creg.website" placeholder="https://..." />
          </div>
          <div class="col-12">
            <label class="form-label">HR Contact</label>
            <input class="form-control" v-model="creg.hr_contact" placeholder="HR name or phone" />
          </div>
          <div class="col-12">
            <label class="form-label">Company Description</label>
            <textarea class="form-control" v-model="creg.description" rows="2" placeholder="Brief about your company"></textarea>
          </div>
          <div class="col-12">
            <div class="alert alert-info py-2 small">
              <i class="bi bi-info-circle me-1"></i>
              After registration, your company must be approved by admin before you can log in and post drives.
            </div>
            <button class="btn btn-primary w-100 fw-semibold" @click="doCompanyRegister" :disabled="rrStore.loading">
              <span v-if="rrStore.loading" class="spinner-border spinner-border-sm me-2"></span>
              Register Company
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      tab: 'login',
      login: { email: '', password: '' },
      sreg: { full_name:'', email:'', password:'', branch:'', year:'', cgpa:'', phone:'', skills:'' },
      creg: { company_name:'', email:'', password:'', industry:'', location:'', website:'', hr_contact:'', description:'' },
    }
  },
  methods: {
    async doLogin() {
      if (!this.login.email || !this.login.password) {
        return rrShowAlert('Email and password are required.', 'warning')
      }
      rrStore.loading = true
      try {
        const res = await rrApi.post('/api/auth/login', this.login)
        const d = res.data
        rrSetAuth(d.rr_token, {
          user_id: d.user_id, email: d.email, role: d.role,
          full_name: d.full_name, company_name: d.company_name
        })
        rrShowAlert(`Welcome back${d.full_name ? ', ' + d.full_name : ''}!`, 'success')
        // Role-based redirect
        if (d.role === 'admin')   this.$router.push('/admin/dashboard')
        else if (d.role === 'company') this.$router.push('/company/dashboard')
        else                           this.$router.push('/student/dashboard')
      } catch (e) {
        rrShowAlert(rrGetError(e), 'danger')
      } finally { rrStore.loading = false }
    },

    async doStudentRegister() {
      const f = this.sreg
      if (!f.full_name || !f.email || !f.password || !f.branch || !f.year || !f.cgpa) {
        return rrShowAlert('Please fill all required fields.', 'warning')
      }
      rrStore.loading = true
      try {
        await rrApi.post('/api/auth/register', { ...f, role: 'student' })
        rrShowAlert('Registration successful! You can now log in.', 'success')
        this.tab = 'login'
        this.login.email = f.email
      } catch (e) {
        rrShowAlert(rrGetError(e), 'danger')
      } finally { rrStore.loading = false }
    },

    async doCompanyRegister() {
      const f = this.creg
      if (!f.company_name || !f.email || !f.password) {
        return rrShowAlert('Company name, email, and password are required.', 'warning')
      }
      rrStore.loading = true
      try {
        await rrApi.post('/api/auth/register', { ...f, role: 'company' })
        rrShowAlert('Company registered! Awaiting admin approval. You will be able to login once approved.', 'success')
        this.tab = 'login'
      } catch (e) {
        rrShowAlert(rrGetError(e), 'danger')
      } finally { rrStore.loading = false }
    }
  }
}

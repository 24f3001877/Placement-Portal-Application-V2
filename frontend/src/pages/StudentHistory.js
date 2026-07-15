// RecruitRadar — pages/StudentHistory.js

const StudentHistory = {
  name: 'StudentHistory',
  template: `
    <div class="container py-4">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h4 class="fw-bold mb-0"><i class="bi bi-clock-history me-2 text-primary"></i>My Applications</h4>
        <button class="btn btn-outline-primary btn-sm" @click="exportCSV">
          <i class="bi bi-download me-1"></i>Export CSV
        </button>
      </div>
      <alert-msg></alert-msg>

      <!-- Export job status -->
      <div v-if="exportJobId && !exportFile" class="alert alert-info d-flex align-items-center gap-2">
        <div class="spinner-border spinner-border-sm"></div>
        Processing export (Job #{{ exportJobId }})... You'll receive an email when ready.
        <button class="btn btn-sm btn-outline-info ms-auto" @click="checkExport">Check Status</button>
      </div>

      <!-- Export ready -->
      <div v-if="exportFile" class="alert alert-success d-flex align-items-center gap-2">
        Export ready!
        <button class="btn btn-sm btn-success ms-auto" @click="downloadCSV">Download CSV</button>
      </div>

      <!-- Tab: Applications / Interviews / Placements -->
      <ul class="nav nav-tabs mb-3">
        <li class="nav-item"><button class="nav-link" :class="{active:tab==='apps'}" @click="tab='apps'">Applications</button></li>
        <li class="nav-item"><button class="nav-link" :class="{active:tab==='interviews'}" @click="tab='interviews';fetchInterviews()">Interviews</button></li>
        <li class="nav-item"><button class="nav-link" :class="{active:tab==='placed'}" @click="tab='placed';fetchPlacements()">Placements</button></li>
      </ul>

      <!-- Applications tab -->
      <div v-if="tab==='apps'">
        <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>
        <div v-else-if="apps.length===0" class="text-center text-muted py-5">
          <i class="bi bi-inbox d-block mb-2" style="font-size:2rem;"></i>No applications yet.
          <div class="mt-2"><router-link to="/student/dashboard" class="btn btn-primary btn-sm">Browse Drives</router-link></div>
        </div>
        <div v-else>
          <div v-for="a in apps" :key="a.id" class="card rr-card mb-3 p-3">
            <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
              <div>
                <h6 class="fw-bold mb-1">{{ a.job_title }}</h6>
                <div class="text-muted small"><i class="bi bi-building me-1"></i>{{ a.company_name }}</div>
                <div class="text-muted small">Applied: {{ fmtDate(a.applied_at) }}</div>
                <div v-if="a.interview_date" class="text-muted small">
                  <i class="bi bi-calendar-event me-1 text-warning"></i>Interview: {{ fmtDate(a.interview_date) }}
                </div>
                <div v-if="a.feedback" class="text-muted small mt-1">
                  <i class="bi bi-chat-quote me-1"></i>{{ a.feedback }}
                </div>
              </div>
              <span :class="'badge rr-badge-'+a.status" style="font-size:0.9rem;">{{ a.status }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Interviews tab -->
      <div v-if="tab==='interviews'">
        <div v-if="interviews.length===0" class="text-center text-muted py-5">No interviews scheduled.</div>
        <div v-else>
          <div v-for="a in interviews" :key="a.id" class="card rr-card mb-3 p-3 border-start border-warning border-3">
            <h6 class="fw-bold mb-1">{{ a.job_title }}</h6>
            <div class="text-muted small"><i class="bi bi-building me-1"></i>{{ a.company_name }}</div>
            <div class="text-warning fw-semibold mt-2">
              <i class="bi bi-calendar-event me-1"></i>{{ fmtDateTime(a.interview_date) }}
            </div>
            <span :class="'badge rr-badge-'+a.status+' mt-2'">{{ a.status }}</span>
          </div>
        </div>
      </div>

      <!-- Placements tab -->
      <div v-if="tab==='placed'">
        <div v-if="placements.length===0" class="text-center text-muted py-5">No confirmed placements yet.</div>
        <div v-else>
          <div v-for="p in placements" :key="p.id" class="card rr-card mb-3 p-3 border-start border-success border-3">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <h6 class="fw-bold mb-1 text-success"><i class="bi bi-trophy me-1"></i>{{ p.position }}</h6>
                <div class="text-muted small"><i class="bi bi-building me-1"></i>{{ p.company_name }}</div>
                <div class="text-muted small" v-if="p.salary">Package: {{ p.salary }}</div>
                <div class="text-muted small" v-if="p.joining_date">Joining: {{ p.joining_date }}</div>
                <div class="text-muted small">Placed on: {{ fmtDate(p.placed_at) }}</div>
              </div>
              <button v-if="p.offer_letter_path" class="btn btn-sm btn-outline-success" @click="downloadOfferLetter(p.id)">
                <i class="bi bi-file-earmark-pdf me-1"></i>Offer Letter
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return { apps:[], interviews:[], placements:[], loading:true, tab:'apps', exportJobId:null, exportFile:null }
  },
  async mounted() { await this.fetchApps() },
  methods: {
    async fetchApps() {
      this.loading = true
      try {
        const res = await rrApi.get('/api/student/applications')
        this.apps = res.data
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
      finally { this.loading = false }
    },
    async fetchInterviews() {
      try {
        const res = await rrApi.get('/api/student/interviews')
        this.interviews = res.data
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    },
    async fetchPlacements() {
      try {
        const res = await rrApi.get('/api/student/placements')
        this.placements = res.data
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    },
    async exportCSV() {
      this.exportFile = null
      try {
        const res = await rrApi.post('/api/student/export')
        this.exportJobId = res.data.export_job_id
        rrShowAlert(res.data.message,'info')
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    },
    async checkExport() {
      if (!this.exportJobId) return
      try {
        const res = await rrApi.get(`/api/student/export/${this.exportJobId}/status`)
        if (res.data.status === 'done') {
          this.exportFile = res.data.file_path
          rrShowAlert('Export ready — click Download.','success')
        } else if (res.data.status === 'failed') {
          rrShowAlert('Export failed. Please try again.','danger')
          this.exportJobId = null
        } else {
          rrShowAlert('Still processing...','info')
        }
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    },
    async downloadCSV() {
      try {
        const res = await rrApi.get(`/api/student/export/${this.exportFile}/download`, { responseType: 'blob' })
        const url = window.URL.createObjectURL(new Blob([res.data]))
        const a = document.createElement('a')
        a.href = url
        a.download = this.exportFile
        a.click()
      } catch(e) { rrShowAlert('Could not download file.', 'danger') }
    },
    async downloadOfferLetter(placementId) {
      try {
        const res = await rrApi.get(`/api/student/offer-letter/${placementId}`, { responseType: 'blob' })
        const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
        window.open(url, '_blank')
      } catch(e) { rrShowAlert('Could not open offer letter.', 'danger') }
    },
    fmtDate(d) { return d ? new Date(d).toLocaleDateString() : '—' },
    fmtDateTime(d) { return d ? new Date(d).toLocaleString() : '—' }
  }
}
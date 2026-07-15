// RecruitRadar — pages/CompanyApplications.js
// Company views applications for a specific drive, updates status, schedules interviews.
const CompanyApplications = {
  name: 'CompanyApplications',
  template: `
    <div class="container py-4">
      <div class="d-flex align-items-center gap-3 mb-4">
        <button class="btn btn-outline-secondary btn-sm" @click="$router.back()">
          <i class="bi bi-arrow-left"></i>
        </button>
        <h4 class="fw-bold mb-0"><i class="bi bi-people me-2 text-primary"></i>Applicants for Drive #{{ driveId }}</h4>
      </div>
      <alert-msg></alert-msg>

      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>

      <div v-else>
        <div v-if="apps.length===0" class="text-center text-muted py-5">
          <i class="bi bi-inbox d-block mb-2" style="font-size:2rem;"></i>No applications yet.
        </div>

        <div v-for="a in apps" :key="a.id" class="card rr-card mb-3 p-3">
          <div class="row align-items-center g-3">
            <div class="col-md-4">
              <h6 class="fw-bold mb-1">{{ a.student_name }}</h6>
              <div class="text-muted small">{{ a.student_email }}</div>
              <div class="text-muted small">
                {{ a.student_branch }} &bull; CGPA: <strong>{{ a.student_cgpa }}</strong>
              </div>
              <div class="mt-1">
                <span :class="'badge rr-badge-'+a.status">{{ a.status }}</span>
              </div>
              <button v-if="a.status==='interview'" class="btn btn-outline-warning btn-sm mt-2"
                @click="sendReminder(a.id)" :disabled="reminding===a.id">
                <span v-if="reminding===a.id" class="spinner-border spinner-border-sm me-1"></span>
                <i v-else class="bi bi-bell me-1"></i>Send Interview Reminder
              </button>
            </div>
            <div class="col-md-5">
              <label class="form-label small fw-semibold">Update Status</label>
              <select class="form-select form-select-sm mb-2" v-model="a._newStatus">
                <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
              </select>
              <div v-if="a._newStatus==='interview'">
                <label class="form-label small">Interview Date & Time</label>
                <input type="datetime-local" class="form-control form-control-sm mb-2" v-model="a._interviewDate" />
              </div>
              <label class="form-label small fw-semibold">Feedback</label>
              <input class="form-control form-control-sm" v-model="a._feedback" placeholder="Optional feedback..." />
            </div>
            <div class="col-md-3">
              <button class="btn btn-primary btn-sm w-100 mb-2" @click="updateApp(a)">
                Save Update
              </button>
              <button v-if="a.status==='placed'" class="btn btn-outline-success btn-sm w-100"
                @click="genOffer(a.id)">
                <i class="bi bi-file-earmark-pdf me-1"></i>Generate Offer Letter
              </button>
              <div v-if="a.interview_date" class="text-muted small mt-2">
                <i class="bi bi-calendar-event me-1"></i>Interview: {{ fmtDate(a.interview_date) }}
              </div>
              <div v-if="a.feedback" class="text-muted small mt-1">
                <i class="bi bi-chat-quote me-1"></i>{{ a.feedback }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      apps: [], loading: true, reminding: null,
      statuses: ['applied','shortlisted','interview','placed','rejected']
    }
  },
  computed: {
    driveId() { return this.$route.params.id }
  },
  mounted() { this.fetchApps() },
  methods: {
    async fetchApps() {
      this.loading = true
      try {
        const res = await rrApi.get(`/api/company/drives/${this.driveId}/applications`)
        this.apps = res.data.map(a => ({ ...a, _newStatus: a.status, _interviewDate:'', _feedback: a.feedback||'' }))
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
      finally { this.loading = false }
    },
    async updateApp(a) {
      const payload = {}
      if (a._newStatus) payload.status = a._newStatus
      if (a._feedback !== undefined) payload.feedback = a._feedback
      if (a._newStatus === 'interview' && a._interviewDate) payload.interview_date = a._interviewDate
      try {
        await rrApi.put(`/api/company/applications/${a.id}`, payload)
        rrShowAlert('Application updated.','success')
        this.fetchApps()
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    },
    async genOffer(appId) {
      try {
        const res = await rrApi.post(`/api/company/applications/${appId}/offer-letter`)
        rrShowAlert(`Offer letter generated: ${res.data.file}`,'success')
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    },
    async sendReminder(appId) {
      this.reminding = appId
      try {
        const res = await rrApi.post(`/api/company/applications/${appId}/send-interview-reminder`)
        rrShowAlert(res.data.message, 'info')
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
      finally { this.reminding = null }
    },
    fmtDate(d) { return d ? new Date(d).toLocaleString() : '—' }
  }
}
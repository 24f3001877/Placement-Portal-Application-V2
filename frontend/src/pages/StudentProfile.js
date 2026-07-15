// RecruitRadar — pages/StudentProfile.js

const StudentProfile = {
  name: 'StudentProfile',
  template: `
    <div class="container py-4" style="max-width:680px;">
      <h4 class="fw-bold mb-4"><i class="bi bi-person-circle me-2 text-primary"></i>My Profile</h4>
      <alert-msg></alert-msg>

      <div v-if="loading" class="text-center py-5"><div class="spinner-border text-primary"></div></div>

      <div v-else class="card rr-card p-4">
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">Full Name</label>
            <input class="form-control" v-model="form.full_name" />
          </div>
          <div class="col-md-6">
            <label class="form-label">Phone</label>
            <input class="form-control" v-model="form.phone" placeholder="Optional" />
          </div>
          <div class="col-md-4">
            <label class="form-label">Branch</label>
            <select class="form-select" v-model="form.branch">
              <option>CSE</option><option>ECE</option><option>EEE</option>
              <option>ME</option><option>CE</option><option>IT</option><option>Other</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">Year</label>
            <select class="form-select" v-model.number="form.year">
              <option :value="1">1st</option><option :value="2">2nd</option>
              <option :value="3">3rd</option><option :value="4">4th</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">CGPA</label>
            <input type="number" step="0.01" min="0" max="10" class="form-control" v-model.number="form.cgpa" />
          </div>
          <div class="col-12">
            <label class="form-label">Skills <span class="text-muted small">(comma separated)</span></label>
            <input class="form-control" v-model="form.skills" placeholder="Python, Java, SQL, ..." />
          </div>
          <div class="col-12">
            <label class="form-label">Experience</label>
            <textarea class="form-control" v-model="form.experience" rows="2"
              placeholder="Internships, projects, etc."></textarea>
          </div>
          <div class="col-12">
            <label class="form-label">Resume <span class="text-muted small">(PDF only, max 5MB)</span></label>
            <input type="file" class="form-control" ref="resumeInput" accept=".pdf" />
            <div v-if="form.resume_path" class="text-muted small mt-1">
              <i class="bi bi-file-earmark-pdf text-danger me-1"></i>Current: {{ form.resume_path }}
            </div>
          </div>
          <div class="col-12">
            <button class="btn btn-primary fw-semibold" @click="save" :disabled="saving">
              <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
              Save Profile
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      loading: true, saving: false,
      form: { full_name:'', phone:'', branch:'', year:'', cgpa:'', skills:'', experience:'', resume_path:'' }
    }
  },
  async mounted() {
    try {
      const res = await rrApi.get('/api/student/profile')
      Object.assign(this.form, res.data)
    } catch(e) { rrShowAlert(rrGetError(e),'danger') }
    finally { this.loading = false }
  },
  methods: {
    async save() {
      this.saving = true
      try {
        const fileInput = this.$refs.resumeInput
        if (fileInput && fileInput.files.length > 0) {
          // Has resume file — use FormData for multipart upload
          const fd = new FormData()
          Object.entries(this.form).forEach(([k,v]) => { if (v) fd.append(k, v) })
          fd.append('resume', fileInput.files[0])
          await rrApi.put('/api/student/profile', fd, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })
        } else {
          await rrApi.put('/api/student/profile', this.form)
        }
        rrShowAlert('Profile updated successfully!','success')
        // Refresh
        const res = await rrApi.get('/api/student/profile')
        Object.assign(this.form, res.data)
      } catch(e) { rrShowAlert(rrGetError(e),'danger') }
      finally { this.saving = false }
    }
  }
}

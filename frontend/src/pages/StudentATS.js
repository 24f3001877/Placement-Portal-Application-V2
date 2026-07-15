// RecruitRadar — pages/StudentATS.js
// ATS Resume Checker page for students.
//
// How it works (explainable in viva):
//   1. Student selects a placement drive from the dropdown.
//   2. Frontend calls POST /api/student/ats-check with { drive_id }.
//   3. Backend reads the student's uploaded resume PDF using pdfplumber.
//   4. Backend extracts raw text and checks each required skill (keyword match).
//   5. Returns match score, matched skills (green), missing skills (red), feedback.
//
// Why keyword matching: transparent, no black box, every result is explainable.

const StudentATS = {
  name: 'StudentATS',
  template: `
    <div class="container py-4" style="max-width:700px;">
      <h4 class="fw-bold mb-1">
        <i class="bi bi-file-earmark-check me-2 text-primary"></i>ATS Resume Checker
      </h4>
      <p class="text-muted mb-4">
        Check how well your resume matches a placement drive's skill requirements
        before applying.
      </p>
      <alert-msg></alert-msg>

      <!-- No resume warning -->
      <div v-if="!hasResume" class="alert alert-warning">
        <i class="bi bi-exclamation-triangle me-2"></i>
        You haven't uploaded a resume yet.
        <router-link to="/student/profile" class="fw-semibold">Upload from My Profile</router-link>
        first.
      </div>

      <!-- Checker form -->
      <div class="card rr-card p-4 mb-4" v-if="hasResume">
        <h6 class="fw-semibold mb-3">Select a Drive to Check Against</h6>

        <div v-if="loadingDrives" class="text-center py-3">
          <div class="spinner-border spinner-border-sm text-primary"></div>
          <span class="ms-2 text-muted">Loading approved drives...</span>
        </div>

        <div v-else>
          <div class="mb-3">
            <label class="form-label">Placement Drive</label>
            <select class="form-select" v-model="selectedDriveId">
              <option value="">— Select a drive —</option>
              <option v-for="d in drives" :key="d.id" :value="d.id">
                {{ d.job_title }} @ {{ d.company_name }}
              </option>
            </select>
          </div>

          <!-- Show selected drive's required skills preview -->
          <div v-if="selectedDrive" class="mb-3 p-3 bg-light rounded">
            <div class="small text-muted mb-1 fw-semibold">Required Skills:</div>
            <div v-if="selectedDrive.skills_required">
              <span
                v-for="skill in selectedDrive.skills_required.split(',')"
                :key="skill"
                class="badge bg-secondary me-1 mb-1"
              >{{ skill.trim() }}</span>
            </div>
            <div v-else class="text-muted small">No specific skills listed for this drive.</div>
          </div>

          <button
            class="btn btn-primary fw-semibold"
            @click="runCheck"
            :disabled="!selectedDriveId || checking"
          >
            <span v-if="checking" class="spinner-border spinner-border-sm me-2"></span>
            <i v-else class="bi bi-search me-2"></i>
            Analyse My Resume
          </button>
        </div>
      </div>

      <!-- Results card -->
      <div v-if="result" class="card rr-card p-4">
        <h6 class="fw-bold mb-1">
          Results for: <span class="text-primary">{{ result.drive_title }}</span>
        </h6>
        <div class="text-muted small mb-3">{{ result.company_name }}</div>

        <!-- Score meter -->
        <div class="mb-3">
          <div class="d-flex justify-content-between mb-1">
            <span class="fw-semibold">Match Score</span>
            <span class="fw-bold" :style="{ color: scoreColor }">{{ result.match_score }}%</span>
          </div>
          <div class="progress" style="height:14px; border-radius:8px;">
            <div
              class="progress-bar"
              :style="{ width: result.match_score + '%', backgroundColor: scoreColor }"
              style="border-radius:8px; transition: width 0.6s ease;"
            ></div>
          </div>
        </div>

        <!-- Feedback message -->
        <div class="alert mb-3 py-2" :class="feedbackClass">
          <i class="bi bi-info-circle me-2"></i>{{ result.feedback }}
        </div>

        <div class="row g-3">
          <!-- Matched skills -->
          <div class="col-md-6">
            <div class="fw-semibold mb-2 text-success">
              <i class="bi bi-check-circle me-1"></i>
              Matched ({{ result.matched_skills.length }})
            </div>
            <div v-if="result.matched_skills.length === 0" class="text-muted small">None matched.</div>
            <span
              v-for="skill in result.matched_skills"
              :key="skill"
              class="badge me-1 mb-1"
              style="background-color:#16a34a; color:#fff;"
            >{{ skill }}</span>
          </div>

          <!-- Missing skills -->
          <div class="col-md-6">
            <div class="fw-semibold mb-2 text-danger">
              <i class="bi bi-x-circle me-1"></i>
              Missing ({{ result.missing_skills.length }})
            </div>
            <div v-if="result.missing_skills.length === 0" class="text-muted small">
              No missing skills — great resume!
            </div>
            <span
              v-for="skill in result.missing_skills"
              :key="skill"
              class="badge me-1 mb-1"
              style="background-color:#dc2626; color:#fff;"
            >{{ skill }}</span>
          </div>
        </div>

        <!-- Tip -->
        <div v-if="result.missing_skills.length > 0" class="mt-3 text-muted small">
          <i class="bi bi-lightbulb me-1 text-warning"></i>
          <strong>Tip:</strong> Add the missing skills to your resume and re-upload from
          <router-link to="/student/profile">My Profile</router-link> to improve your score.
        </div>
      </div>
    </div>
  `,

  data() {
    return {
      drives: [],
      selectedDriveId: '',
      result: null,
      hasResume: false,
      loadingDrives: true,
      checking: false,
    }
  },

  computed: {
    /** @returns {Object|null} The full drive object for the selected drive_id */
    selectedDrive() {
      if (!this.selectedDriveId) return null
      return this.drives.find(d => d.id === this.selectedDriveId) || null
    },

    /** @returns {string} Hex colour based on match score */
    scoreColor() {
      const s = this.result ? this.result.match_score : 0
      if (s >= 75) return '#16a34a'   // green
      if (s >= 50) return '#f59e0b'   // amber
      return '#dc2626'                // red
    },

    /** @returns {string} Bootstrap alert class based on score */
    feedbackClass() {
      const s = this.result ? this.result.match_score : 0
      if (s >= 75) return 'alert-success'
      if (s >= 50) return 'alert-warning'
      return 'alert-danger'
    },
  },

  async mounted() {
    await this.loadProfile()
    await this.loadDrives()
  },

  methods: {
    /** Check if the student has a resume uploaded — if not, show warning. */
    async loadProfile() {
      try {
        const res = await rrApi.get('/api/student/profile')
        this.hasResume = !!res.data.resume_path
      } catch (e) {
        this.hasResume = false
      }
    },

    /** Load all approved drives for the dropdown. */
    async loadDrives() {
      this.loadingDrives = true
      try {
        const res = await rrApi.get('/api/student/drives')
        this.drives = res.data
      } catch (e) {
        rrShowAlert(rrGetError(e), 'danger')
      } finally {
        this.loadingDrives = false
      }
    },

    /**
     * Send the ATS check request.
     * Backend extracts resume text and compares against drive's skills_required.
     */
    async runCheck() {
      if (!this.selectedDriveId) return
      this.checking = true
      this.result = null

      try {
        const res = await rrApi.post('/api/student/ats-check', {
          drive_id: this.selectedDriveId,
        })
        this.result = res.data
      } catch (e) {
        rrShowAlert(rrGetError(e), 'danger')
      } finally {
        this.checking = false
      }
    },
  },
}

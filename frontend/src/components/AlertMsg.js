// RecruitRadar — components/AlertMsg.js
const AlertMsg = {
  name: 'AlertMsg',
  template: `
    <transition name="page">
      <div v-if="rrStore.alertMsg"
        :class="['alert','alert-'+rrStore.alertType,'alert-dismissible','mb-3']"
        role="alert" style="border-radius:8px;">
        <i :class="iconClass" class="me-2"></i>
        {{ rrStore.alertMsg }}
        <button type="button" class="btn-close" @click="rrStore.alertMsg=null"></button>
      </div>
    </transition>
  `,
  computed: {
    iconClass() {
      const m = { success:'bi bi-check-circle-fill', danger:'bi bi-exclamation-triangle-fill',
                  warning:'bi bi-exclamation-circle-fill', info:'bi bi-info-circle-fill' }
      return m[rrStore.alertType] || 'bi bi-info-circle-fill'
    }
  }
}


---

# 📄 FILE 6: `docs/operations_runbook.md`

**Path:** `padi-nairobi-01/docs/operations_runbook.md`

```markdown
# PADI EXECUTOR v5.3 — NAIROBI-01 NODE OPERATIONS RUNBOOK

**Version:** 5.3  
**Node:** Nairobi-01  
**Location:** Tassia III, NSSF Nyayo Embakasi, Embakasi, Nairobi, 00515, Kenya  
**Timezone:** Africa/Nairobi (EAT)  
**Effective Date:** 2026-03-26  

---

## 1. QUICK START

### 1.1 Initial Setup

```bash
cd padi-nairobi-01
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install prometheus-client
cp .env.template .env
nano .env
python test_deployment.py

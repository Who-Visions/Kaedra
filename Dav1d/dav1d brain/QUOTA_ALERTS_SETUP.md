# GCP Quota Alert Setup - COMPLETE ✅

## Alert Policy Created

**Policy Name:** Dav1d - High Quota Usage (>80%)  
**Project:** gen-lang-client-0285887798  
**Notification Email:** whoentertains@gmail.com  
**Status:** ACTIVE

## What This Alert Does

Monitors **all GCP quotas** in your project and sends an email notification to `whoentertains@gmail.com` when:
- Any quota usage exceeds **80%** of its allocated limit
- This includes:
  - Compute Engine (CPUs, Networks, Firewall Rules, etc.)
  - Cloud Run (Services, Revisions)
  - Cloud Build (Concurrent Builds)
  - Vertex AI (Reasoning Engine entities)
  - IAM (Service Accounts)
  - All other enabled services

## How to Access

1. **View the alert policy:**
   - Go to: https://console.cloud.google.com/monitoring/alerting/policies?project=gen-lang-client-0285887798
   - Look for "Dav1d - High Quota Usage (>80%)"

2. **View all quotas:**
   - Go to: https://console.cloud.google.com/iam-admin/quotas?project=gen-lang-client-0285887798

## How It Works

The alert uses **MQL (Monitoring Query Language)** to:
1. Fetch quota allocation usage from `serviceruntime.googleapis.com/quota/allocation/usage`
2. Fetch quota limits from `serviceruntime.googleapis.com/quota/limit`
3. Calculate the ratio (usage / limit)
4. Alert when ratio > 0.8 (80%)
5. Check every 1 minute
6. Group by service, quota metric, and location

## Next Steps

✅ **Alert is now active!** You'll receive email notifications when any quota reaches 80% usage.

To test or modify:
- Run `python setup_quota_alerts.py` again to verify
- Modify the threshold in the script (currently 0.8 = 80%)
- Check the GCP Console to see the alert in action

## Files Created

- `setup_quota_alerts.py` - Setup script
- `requirements.txt` - Updated with `google-cloud-monitoring`
- This README

---
**AI with Dav3 × Who Visions LLC**  
Deployed: 2025-11-27 17:16 EST

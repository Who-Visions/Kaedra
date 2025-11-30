import os
import time
from google.cloud import monitoring_v3
from google.protobuf import duration_pb2

# Configuration
PROJECT_ID = "gen-lang-client-0285887798"
EMAIL = "whoentertains@gmail.com"

def setup_alerts():
    print(f"Initializing Alert Setup for Project: {PROJECT_ID}")
    
    try:
        client = monitoring_v3.AlertPolicyServiceClient()
        channel_client = monitoring_v3.NotificationChannelServiceClient()
        project_name = f"projects/{PROJECT_ID}"
    except Exception as e:
        print(f"Error initializing clients: {e}")
        return

    # 1. Setup Notification Channel
    channel_name = None
    print("Checking notification channels...")
    try:
        results = channel_client.list_notification_channels(name=project_name)
        for channel in results:
            if channel.type_ == "email" and channel.labels.get("email_address") == EMAIL:
                channel_name = channel.name
                print(f"Found existing notification channel: {channel_name}")
                break
        
        if not channel_name:
            print(f"Creating new notification channel for {EMAIL}...")
            channel = monitoring_v3.NotificationChannel(
                type_="email",
                display_name="Dav1d Admin",
                labels={"email_address": EMAIL}
            )
            created_channel = channel_client.create_notification_channel(
                name=project_name, notification_channel=channel
            )
            channel_name = created_channel.name
            print(f"Created channel: {channel_name}")
    except Exception as e:
        print(f"Error setting up notification channel: {e}")
        return

    # 2. Create Alert Policy for Allocation Quotas (>80%)
    print("Configuring Allocation Quota Alert Policy...")
    
    # MQL for Allocation Quotas
    # Calculates usage / limit ratio
    mql_allocation = """
    fetch consumer_quota
    | { metric 'serviceruntime.googleapis.com/quota/allocation/usage'
        | align next_older(1m)
      ; metric 'serviceruntime.googleapis.com/quota/limit'
        | align next_older(1m) }
    | join
    | div
    | group_by [resource.service, metric.quota_metric, resource.location],
        max(val())
    | condition val() > 0.8
    """

    alert_policy = monitoring_v3.AlertPolicy(
        display_name="Dav1d - High Quota Usage (>80%)",
        combiner=monitoring_v3.AlertPolicy.ConditionCombinerType.OR,
        conditions=[
            monitoring_v3.AlertPolicy.Condition(
                display_name="Quota Usage Ratio > 80%",
                condition_monitoring_query_language=monitoring_v3.AlertPolicy.Condition.MonitoringQueryLanguageCondition(
                    query=mql_allocation,
                    duration=duration_pb2.Duration(seconds=60)
                )
            )
        ],
        notification_channels=[channel_name],
        documentation=monitoring_v3.AlertPolicy.Documentation(
            content="## Quota Warning\n\nYour quota usage is exceeding 80% of the limit for one or more services.\n\nPlease check the [Quota Page](https://console.cloud.google.com/iam-admin/quotas) to request an increase.",
            mime_type="text/markdown"
        )
    )

    # Check for duplicates
    try:
        existing_policies = client.list_alert_policies(name=project_name)
        for policy in existing_policies:
            if policy.display_name == alert_policy.display_name:
                print("Alert policy 'Dav1d - High Quota Usage (>80%)' already exists.")
                return
    except Exception as e:
        print(f"Error listing policies: {e}")

    # Create Policy
    try:
        created_policy = client.create_alert_policy(
            name=project_name, alert_policy=alert_policy
        )
        print(f"Successfully created alert policy: {created_policy.name}")
        print(f"View policy at: https://console.cloud.google.com/monitoring/alerting/policies/{created_policy.name.split('/')[-1]}?project={PROJECT_ID}")
    except Exception as e:
        print(f"Error creating policy: {e}")

if __name__ == "__main__":
    setup_alerts()

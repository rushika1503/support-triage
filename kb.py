"""A tiny fictional knowledge base for the demo. Every article here is made up."""

ARTICLES = [
    {
        "id": "AZ-1",
        "team": "Azure",
        "title": "Database queries time out under load",
        "body": "Check the connection pool size and slow query log first. "
                "Scale the database tier or add an index on the filtered column, then retest under load.",
    },
    {
        "id": "AZ-2",
        "team": "Azure",
        "title": "Virtual machine unreachable after a network change",
        "body": "Verify the network security group rules and the route table. "
                "Confirm the public IP is still attached, then test from a different network.",
    },
    {
        "id": "M365-1",
        "team": "Microsoft 365",
        "title": "Teams meetings drop audio after several minutes",
        "body": "Collect the client logs and check for network jitter. "
                "Update the client, disable hardware acceleration, and test with a wired connection.",
    },
    {
        "id": "M365-2",
        "team": "Microsoft 365",
        "title": "Mailbox sync is delayed in Outlook",
        "body": "Rebuild the Outlook profile and check mailbox size limits. "
                "Confirm the service health dashboard shows no mail flow incident.",
    },
    {
        "id": "ID-1",
        "team": "Identity",
        "title": "Directory sync with on-premises has not completed",
        "body": "Run a delta sync and read the sync service error code. "
                "Check for duplicate attributes and confirm the sync account password has not expired.",
    },
    {
        "id": "ID-2",
        "team": "Identity",
        "title": "Conditional access blocks sign-in for some users",
        "body": "Open the sign-in logs and find which policy applied. "
                "Check device compliance and location conditions, then add a test exclusion group.",
    },
    {
        "id": "EP-1",
        "team": "Endpoint",
        "title": "Device compliance policy fails to apply",
        "body": "Force a device sync and check the policy assignment scope. "
                "Look for conflicting policies and confirm the device checked in recently.",
    },
    {
        "id": "EP-2",
        "team": "Endpoint",
        "title": "Application deployment stuck as pending",
        "body": "Confirm the app is assigned to the right group and the installer detection rule is correct. "
                "Retry the install and review the agent log.",
    },
    {
        "id": "PP-1",
        "team": "Power Platform",
        "title": "Scheduled refresh fails after a gateway update",
        "body": "Restart the gateway service and update the data source credentials. "
                "Confirm the gateway version is supported and the dataset is mapped to it.",
    },
    {
        "id": "PP-2",
        "team": "Power Platform",
        "title": "Flow run fails with a connection authorization error",
        "body": "Re-authenticate the connection and check the connection owner. "
                "Confirm the account still has permission to the target service.",
    },
    {
        "id": "D365-1",
        "team": "Dynamics 365",
        "title": "Work orders are not syncing to the mobile app",
        "body": "Check the offline profile filters and the user's security role. "
                "Clear the app cache and force a full sync.",
    },
    {
        "id": "D365-2",
        "team": "Dynamics 365",
        "title": "Plugin times out when saving records",
        "body": "Review the plugin trace log for long-running steps. "
                "Move heavy work to an asynchronous step and retest.",
    },
]
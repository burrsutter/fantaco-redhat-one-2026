As Cluster Admin

----
oc patch OdhDashboardConfig odh-dashboard-config -n redhat-ods-applications --type=merge -p '{"spec":{"dashboardConfig":{"genAiStudio":true}}}'
----

----
oc get OdhDashboardConfig odh-dashboard-config -n redhat-ods-applications -o jsonpath='{.spec.dashboardConfig}' | jq
----

----
{
  "disableTracking": false,
  "genAiStudio": true
}
----

----
oc rollout restart deployment/rhods-dashboard -n redhat-ods-applications
----

----
deployment.apps/rhods-dashboard restarted
----


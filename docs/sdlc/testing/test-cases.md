# Tests

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start summary -->
131 tests · Passed 130 · Failed 0 · Skipped 0 · Not run 1

Acceptance criteria covered: 10/146 · passing: 10/146
<!-- sdlc:auto:end summary -->

<!-- sdlc:auto:start tests -->
## Sprint 1

### US-001: Load the supplied dataset files in one admin ingest run

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| AC-001 | test_ac001_a_patient_row_gets_its_uuid_from_the_server | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[coverage_periods] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[encounter_truth] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[events] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[ingest_file_results] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[ingest_runs] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[intake_answers] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[notes] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[patients] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_every_primary_key_is_a_server_generated_uuid[personas] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[coverage_periods] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[encounter_truth] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[events] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[ingest_file_results] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[ingest_runs] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[intake_answers] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[notes] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[patients] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_migration_creates_every_table[personas] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_each_patient_scoped_table_has_a_patient_foreign_key[coverage_periods] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_each_patient_scoped_table_has_a_patient_foreign_key[encounter_truth] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_each_patient_scoped_table_has_a_patient_foreign_key[events] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_each_patient_scoped_table_has_a_patient_foreign_key[intake_answers] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_each_patient_scoped_table_has_a_patient_foreign_key[notes] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_patient_and_event_time_are_indexed_together[coverage_periods-columns0] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_patient_and_event_time_are_indexed_together[encounter_truth-columns1] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_patient_and_event_time_are_indexed_together[events-columns2] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_patient_and_event_time_are_indexed_together[intake_answers-columns3] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-002 | test_ac002_patient_and_event_time_are_indexed_together[notes-columns4] | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-003 | test_ac003_ingest_file_results_stores_the_per_file_outcome | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-003 | test_ac003_ingest_runs_stores_the_run_summary_columns | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-004 | test_ac004_dataset_patient_id_is_distinct_from_the_internal_uuid | Unit | Passed | `backend/tests/unit/test_event_store_migration.py` |
| AC-001 | test_ac001_a_gzipped_file_is_decompressed_in_a_stream_not_read_whole | Unit | Passed | `backend/tests/unit/test_ingest_fhir.py` |
| AC-001 | test_ac001_every_gzipped_fhir_resource_type_present_is_streamed_and_loaded | Unit | Passed | `backend/tests/unit/test_ingest_fhir.py` |
| AC-002 | test_ac002_a_malformed_file_fails_and_leaves_no_partial_rows | Unit | Passed | `backend/tests/unit/test_ingest_fhir.py` |
| AC-002 | test_ac002_a_resource_missing_a_required_field_is_rejected_and_named | Unit | Passed | `backend/tests/unit/test_ingest_fhir.py` |
| AC-003 | test_ac003_a_second_run_replaces_the_fhir_load_rather_than_duplicating | Unit | Passed | `backend/tests/unit/test_ingest_fhir.py` |
| AC-001 | test_ac001_every_file_streams_from_the_configured_location | Unit | Passed | `backend/tests/unit/test_ingest_job.py` |
| AC-002 | test_ac002_a_malformed_row_is_rejected_and_counted_not_inserted | Unit | Passed | `backend/tests/unit/test_ingest_job.py` |
| AC-002 | test_ac002_a_missing_required_column_names_the_file_and_column_and_loads_nothing | Unit | Passed | `backend/tests/unit/test_ingest_job.py` |
| AC-003 | test_ac003_a_second_run_replaces_the_prior_load_rather_than_duplicating | Unit | Passed | `backend/tests/unit/test_ingest_job.py` |
| AC-004 | test_ac004_progress_is_written_as_the_job_proceeds | Unit | Passed | `backend/tests/unit/test_ingest_job.py` |
| AC-144, AC-145 | Admin connections and settings > [AC-144/AC-145] a configured deployment shows Connected for both and the dataset version | Unit | Passed | `frontend/src/screens/Admin.test.tsx` |
| AC-145 | Admin connections and settings > [AC-145] an unconfigured deployment shows Not configured and never a credential value | Unit | Passed | `frontend/src/screens/Admin.test.tsx` |
| AC-001, AC-002, AC-003 | Admin ingest report > [AC-001/AC-002/AC-003] a successful run renders passed files with their counts | Unit | Passed | `frontend/src/screens/Admin.test.tsx` |
| AC-003 | Admin ingest report > [AC-003] a failed file's row shows its named reason | Unit | Passed | `frontend/src/screens/Admin.test.tsx` |
| AC-001 | test_ac001_every_required_file_type_is_loaded_with_per_file_row_counts | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| AC-002 | test_ac002_the_report_carries_version_seed_patient_count_and_a_pass_line_per_file | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| AC-003 | test_ac003_a_file_missing_a_required_column_fails_and_is_named_with_that_column | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| AC-004, NFR-021 | test_ac004_nfr021_re_running_replaces_the_prior_load_without_duplicates | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| NFR-005 | test_nfr005_the_loaded_cohort_is_served_from_the_database_not_the_raw_files | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| NFR-006 | test_nfr006_ingest_runs_as_a_background_job_with_progress | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| NFR-023 | test_nfr023_the_supplied_formats_are_read_as_they_are | Integration | Passed | `backend/tests/integration/test_ingest_run_acceptance.py` |
| AC-001 | test_ac001_a_start_without_a_dataset_version_is_422 | Integration | Passed | `backend/tests/integration/test_ingest_run_access.py` |
| AC-001 | test_ac001_starting_a_run_requires_a_bearer_token | Integration | Passed | `backend/tests/integration/test_ingest_run_access.py` |
| AC-002 | test_ac002_an_unknown_run_id_is_404 | Integration | Passed | `backend/tests/integration/test_ingest_run_access.py` |
| AC-002 | test_ac002_the_report_requires_a_bearer_token | Integration | Passed | `backend/tests/integration/test_ingest_run_access.py` |
| AC-001 | test_ac001_a_second_start_while_a_run_is_in_progress_is_409 | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-001 | test_ac001_start_returns_202_with_the_run_summary | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-002 | test_ac002_an_unknown_run_id_is_404 | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-002 | test_ac002_the_report_carries_the_run_summary_and_a_line_per_file | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-003 | test_ac003_a_failed_files_error_names_the_file_and_the_column | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-004 | test_ac004_both_routes_need_the_shared_bearer[Bearer wrong-token] | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-004 | test_ac004_both_routes_need_the_shared_bearer[None] | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |
| AC-004 | test_ac004_both_routes_need_the_shared_bearer[not-a-bearer] | Integration | Passed | `backend/tests/unit/test_ingest_run_routes.py` |

### US-037: Show the synthetic-data banner on every screen

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| AC-119 | test_ac119_the_notice_says_synthetic_and_not_for_clinical_use | Unit | Passed | `backend/tests/unit/test_synthetic_notice_exports.py` |
| AC-119 | test_ac119_with_notice_adds_it_to_a_payload_without_dropping_its_data | Unit | Passed | `backend/tests/unit/test_synthetic_notice_exports.py` |
| AC-120 | test_ac120_every_page_of_an_export_carries_the_notice | Unit | Passed | `backend/tests/unit/test_synthetic_notice_exports.py` |
| AC-121 | test_ac121_a_page_with_no_body_text_still_carries_the_notice | Unit | Passed | `backend/tests/unit/test_synthetic_notice_exports.py` |
| AC-119 | SyntheticDataNotice > [AC-119] an unregistered route still shows the notice after its redirect | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119 | SyntheticDataNotice > [AC-119] states the data is 100% synthetic and not for clinical use | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /admin | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /case-summary | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /insufficient-history | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /my-health | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /start | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /timeline | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, AC-121 | SyntheticDataNotice > [AC-119][AC-121] the notice renders on /worklist | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-121 | SyntheticDataNotice > [AC-121] the route table is not empty, so the guardrail below cannot pass vacuously | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| — | SyntheticDataNotice > [AC-SIMPLIFY] /start is still drawn without the app menu | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| — | SyntheticDataNotice > [AC-SIMPLIFY] a shell route is still drawn inside the app menu | Unit | Passed | `frontend/src/components/SyntheticDataNotice.test.tsx` |
| AC-119, NFR-017 | test_ac119_nfr017_every_data_route_carries_the_synthetic_notice[GET-/api/demo/personas-None] | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_every_data_route_carries_the_synthetic_notice[GET-/api/evaluation/runs/latest-None] | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_every_data_route_carries_the_synthetic_notice[GET-/api/patients/me/timeline-None] | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_every_data_route_carries_the_synthetic_notice[GET-/api/patients/me/updates-None] | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_every_data_route_carries_the_synthetic_notice[GET-/api/patients/me/visit-prep-None] | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_every_data_route_carries_the_synthetic_notice[GET-/api/worklist-None] | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_the_demo_replay_carries_the_notice | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-119, NFR-017 | test_ac119_nfr017_the_evaluation_report_carries_the_notice | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-120, NFR-017 | test_ac120_nfr017_the_referral_packet_has_the_notice_on_every_page | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-120, NFR-017 | test_ac120_nfr017_the_visit_prep_sheet_has_the_notice_on_every_page | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |
| AC-121, NFR-017 | test_ac121_nfr017_every_data_route_is_covered_at_one_hundred_percent | Integration | Passed | `backend/tests/integration/test_synthetic_notice.py` |

### US-044: Deploy and configure the application as a managed web app

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| AC-144 | test_ac144_health_reports_ok_and_the_services_it_depends_on | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-144 | test_ac144_settings_reports_the_latest_passed_runs_dataset_version | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-145, NFR-011 | test_ac145_nfr011_settings_never_contains_a_credential_value | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-145, NFR-011 | test_ac145_nfr011_settings_reports_connected_for_configured_credentials | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-146 | test_ac146_health_succeeds_unauthenticated | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-146, NFR-010 | test_ac146_nfr010_a_wrong_bearer_is_refused | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-146, NFR-010 | test_ac146_nfr010_an_unauthenticated_request_is_refused | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| NFR-010 | test_nfr010_every_patient_and_clinician_route_refuses_an_anonymous_request | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| NFR-010 | test_nfr010_the_api_offers_no_public_sign_up_or_self_service_entry_point | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| NFR-011 | test_nfr011_no_credential_value_appears_in_any_api_response_or_the_openapi_document | Integration | Passed | `backend/tests/integration/test_deployment_access_and_settings.py` |
| AC-144 | test_ac144_health_reports_ok_and_the_services_it_depends_on | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-144 | test_ac144_health_stays_reachable_without_any_header | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-144 | test_ac144_settings_reports_the_latest_passed_runs_dataset_version | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-145 | test_ac145_no_credential_value_appears_anywhere_in_the_body | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-145 | test_ac145_settings_report_connected_when_both_are_configured | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-145 | test_ac145_settings_report_not_configured_when_the_database_url_is_absent | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-145 | test_ac145_settings_report_not_configured_when_the_llm_key_is_absent | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_a_missing_or_wrong_bearer_is_401[Bearer ] | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_a_missing_or_wrong_bearer_is_401[Bearer wrong-token] | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_a_missing_or_wrong_bearer_is_401[None] | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_a_missing_or_wrong_bearer_is_401[] | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_a_missing_or_wrong_bearer_is_401[not-a-bearer] | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_every_route_except_health_refuses_an_unauthenticated_request | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_the_correct_bearer_passes | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |
| AC-146 | test_ac146_the_dependency_refuses_without_a_configured_secret | Integration | Passed | `backend/tests/unit/test_admin_settings.py` |

## Project setup

| Criteria | Test | Level | Result | File |
|---|---|---|---|---|
| — | test_is_idempotent_and_never_rehashes_an_existing_users_password | Unit | Passed | `backend/tests/unit/test_bootstrap.py` |
| — | test_seeds_nothing_when_no_platform_variables_are_set | Unit | Passed | `backend/tests/unit/test_bootstrap.py` |
| — | test_seeds_the_admin_and_smoke_test_users_from_exactly_those_names | Unit | Passed | `backend/tests/unit/test_bootstrap.py` |
| — | test_disk_creates_parent_directories | Unit | Passed | `backend/tests/unit/test_storage.py` |
| — | test_disk_delete_is_quiet_when_nothing_was_there | Unit | Passed | `backend/tests/unit/test_storage.py` |
| — | test_disk_delete_removes_the_file | Unit | Passed | `backend/tests/unit/test_storage.py` |
| — | test_disk_refuses_a_key_that_escapes_media_root | Unit | Passed | `backend/tests/unit/test_storage.py` |
| — | test_disk_round_trip | Unit | Passed | `backend/tests/unit/test_storage.py` |
| — | test_disk_url_is_a_local_media_path | Unit | Passed | `backend/tests/unit/test_storage.py` |
| — | test_s3_backend_used_when_bucket_configured | Unit | Passed | `backend/tests/unit/test_storage.py` |
| — | App > renders a screen inside the app shell and shows its menu | Unit | Passed | `frontend/src/App.test.tsx` |
| — | test_health_reports_ok | Integration | Passed | `backend/tests/integration/test_health.py` |
| — | test_the_openapi_document_builds | Integration | Passed | `backend/tests/integration/test_health.py` |
| — | the app loads | E2E | Not run yet | `frontend/e2e/example.spec.ts` |
<!-- sdlc:auto:end tests -->

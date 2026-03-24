# Inventory Area Naming Collision

## Overview

When the `CreateInventoryAreaJob` runs for a warehouse location, it generates an IA name using the formula:

```
warehouse_name_clean + ' ' + location_code_clean [+ franchisee_id if franchisee]
```

See `catalog/app/services/warehouse_location_helper_service.rb` (`SQL_GENERATE_IA_RECORD`, lines ~258–261, 286).

Because the warehouse ID is **not** included in the name, two distinct warehouses with the same name and location code will produce identical IA names and collide.

## Error signature

```
Error generating Inventory Area(s): (WL:<id>) IA Generation: The name '<WarehouseName> <LocationCode>' is already in use.
```

## Diagnosis

This is a **data collision**, not a system outage or code bug. The `SQL_VERIFY_UNIQUE_IA_NAME` query (lines ~359–369) intentionally rejects the duplicate — the system is working correctly.

**Likely cause: two distinct warehouse locations under different retailers share the same cleaned name and location code.**

### Investigation queries (Blazer / Rails console)

```sql
-- Check if the failing WL already has an IA
SELECT id, inventory_area_id, location_code, name
FROM warehouse_locations
WHERE id = <wl_id>;

-- Find which WL owns the conflicting IA name
SELECT ia.id, ia.name, wl.id AS wl_id, wl.location_code, wl.name AS wl_name
FROM inventory_areas ia
JOIN warehouse_locations wl ON wl.inventory_area_id = ia.id
WHERE ia.name = '<ConflictingName>';
```

If the two WLs belong to different warehouses (different `warehouse_id` values), this is the known duplicate-name scenario.

## Resolution

### Immediate (manual)

1. If the failing WL already has an IA (from a prior partial run): update the `LaunchOnboardingWarehouseLocation` record with the correct `inventory_area_id` and mark the waterfall as complete.
2. If not: manually create an IA with a unique name (e.g., append the warehouse ID: `WarehouseName_WarehouseId LocationCode`) via catalog admin, then link it to the failing WL and update the `LaunchOnboardingWarehouseLocation` record.
3. Contact the expansions team (#ask-expansions) to coordinate — post with the WL ID, conflicting IA name, and both warehouse IDs.

### Systemic (longer-term, not immediate)

The `SQL_GENERATE_IA_RECORD` name formula should be extended to include the warehouse ID as a disambiguator for non-franchisee cases, similar to how `franchisee_id` is already appended for franchisees. See `warehouse_location_helper_service.rb:~258–301`.

## What NOT to do

- **Do not generate a PR that adds alerting or Slack notifications for this error** — that masks the symptom without fixing the root cause and reduces visibility into the underlying naming collision problem.
- Do not retry the `CreateInventoryAreaJob` without first resolving the name conflict — it will fail again.

## Code path

```
Partners LaunchOnboardingWarehouseLocations::PropagateAttributesDownstreamJob (line ~265)
  └─ CreateInventoryAreaJob (partners/app/jobs/launch_onboarding_warehouse_locations/create_inventory_area_job.rb:12)
       └─ Catalog::InventoryAreas::CreateService.perform (via RPC)
            └─ inventory_areas_service_handler.rb:43–57
                 └─ WarehouseLocationHelperService.process_ia_generate
                      └─ SQL_VERIFY_UNIQUE_IA_NAME → rejects duplicate → returns error
```

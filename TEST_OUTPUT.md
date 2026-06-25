# Test Run Output

Test suite for Tradexa. Tests live in [`inventory/tests.py`](inventory/tests.py)
and [`orders/tests.py`](orders/tests.py) and cover the core recommendation
logic plus the hardened edge cases (dimensional fit, atomic order references,
duplicate-product merging, weight/volume limits, and the REST API).

CI also runs these on every push — see
[`.github/workflows/tests.yml`](.github/workflows/tests.yml) and the
**Actions** tab on GitHub.

## How to run locally

```bash
python manage.py test --verbosity 2
```

Tests use Django's test runner, which creates and destroys a throwaway
`test_tradexa` database automatically (no effect on your real data).

## Result — 26 passed

```
Creating test database for alias 'default' ('test_tradexa')...
Found 26 test(s).
System check identified no issues (0 silenced).

test_volume_property (inventory.tests.BoxModelTests.test_volume_property) ... ok
test_box_list_only_active (inventory.tests.InventoryApiTests.test_box_list_only_active) ... ok
test_product_detail (inventory.tests.InventoryApiTests.test_product_detail) ... ok
test_product_list (inventory.tests.InventoryApiTests.test_product_list) ... ok
test_sku_is_unique (inventory.tests.ProductModelTests.test_sku_is_unique) ... ok
test_volume_property (inventory.tests.ProductModelTests.test_volume_property) ... ok
test_cheapest_fitting_box_is_chosen (orders.tests.BoxSelectorTests.test_cheapest_fitting_box_is_chosen) ... ok
test_dimensional_fit_rejects_short_box (orders.tests.BoxSelectorTests.test_dimensional_fit_rejects_short_box) ... ok
test_empty_order_returns_prompt (orders.tests.BoxSelectorTests.test_empty_order_returns_prompt) ... ok
test_no_box_when_item_too_large (orders.tests.BoxSelectorTests.test_no_box_when_item_too_large) ... ok
test_rotation_allowed_in_fit (orders.tests.BoxSelectorTests.test_rotation_allowed_in_fit) ... ok
test_weight_limit_excludes_box (orders.tests.BoxSelectorTests.test_weight_limit_excludes_box) ... ok
test_create_order_returns_reference_and_recommendation (orders.tests.OrderApiTests.test_create_order_returns_reference_and_recommendation) ... ok
test_order_detail (orders.tests.OrderApiTests.test_order_detail) ... ok
test_preview_returns_dimensional_fits_flags (orders.tests.OrderApiTests.test_preview_returns_dimensional_fits_flags) ... ok
test_recommend_endpoint_persists_recommendation (orders.tests.OrderApiTests.test_recommend_endpoint_persists_recommendation) ... ok
test_recommend_unknown_order_returns_404 (orders.tests.OrderApiTests.test_recommend_unknown_order_returns_404) ... ok
test_duplicate_products_are_merged (orders.tests.OrderCreateSerializerTests.test_duplicate_products_are_merged) ... ok
test_empty_items_rejected (orders.tests.OrderCreateSerializerTests.test_empty_items_rejected) ... ok
test_recommendation_created_with_order (orders.tests.OrderCreateSerializerTests.test_recommendation_created_with_order) ... ok
test_unknown_product_rejected (orders.tests.OrderCreateSerializerTests.test_unknown_product_rejected) ... ok
test_explicit_reference_is_preserved (orders.tests.OrderModelTests.test_explicit_reference_is_preserved) ... ok
test_reference_generated_from_pk (orders.tests.OrderModelTests.test_reference_generated_from_pk) ... ok
test_references_are_unique_and_sequential (orders.tests.OrderModelTests.test_references_are_unique_and_sequential) ... ok
test_empty_order_totals (orders.tests.PackingCalculatorTests.test_empty_order_totals) ... ok
test_totals_and_efficiency_factor (orders.tests.PackingCalculatorTests.test_totals_and_efficiency_factor) ... ok

----------------------------------------------------------------------
Ran 26 tests in 1.289s

OK
Destroying test database for alias 'default' ('test_tradexa')...
```

## What the tests cover

| Area | Tests |
| ---- | ----- |
| **Packing calculator** | volume + weight totals, 80% efficiency factor, empty order |
| **Box selector — dimensional fit** | rejects a box too short for a 44 cm item, allows rotation, cheapest qualifying box wins |
| **Box selector — limits** | weight limit excludes an over-heavy order, oversized item → no box, empty order prompt |
| **Order references (race-safe)** | generated from DB pk, unique + sequential, explicit reference preserved |
| **Order creation** | duplicate `product_id`s merged into one line, recommendation created with order, empty/unknown items rejected |
| **REST API** | product list/detail, active-only box list, preview `fits` flags, order create/detail, recommend endpoint, 404 on unknown order |

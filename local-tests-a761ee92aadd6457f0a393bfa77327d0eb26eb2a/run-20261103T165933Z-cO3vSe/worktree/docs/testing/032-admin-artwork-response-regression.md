## Admin artwork response regression

A reported HTTP failure (`test_image_choice_and_type_permissions`, `KeyError: image_url`)
identified a missing key in shared admin map responses. The pack-artwork HTTP regression now
asserts the returned URL, consistency with GET map metadata, a successful artwork response,
and the existing no-store, pixel and permission checks. It does not remove or bypass assertions.

```sh
python -m pytest -ra python/tests/test_admin_image_url_contract.py
python -m pytest -v python/tests/test_pack_images_web.py::test_image_choice_and_type_permissions
python -m pytest -ra python/tests --ignore=python/tests/browser
```

`test_admin_image_url_contract.py` is dependency-light source-contract coverage: it evaluates
the production payload URL expression, checks shared payload use in the import route, and
checks that the original-image route retains authorization and no-store headers. It is not an
HTTP test. `Patch/IMAGE_URL_FIX_VALIDATION.md` records the checks actually run for this hotfix;
previous double-reveal validation results must not be counted as reruns of this correction.
The Starlette/httpx deprecation warning is separate; this patch changes no dependency pins.



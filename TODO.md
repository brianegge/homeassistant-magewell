# TODO: Get Listed in HACS Default

## Verify CI Workflows

- [x] Hassfest Validate — passing
- [x] Tests — passing (40 tests, 92% coverage)
- [ ] HACS Validate — 7/8 checks pass; **brands** check will pass after brand assets PR is merged

## Set GitHub Repo Metadata

- [x] Add description: "Home Assistant custom integration for Magewell Pro Convert NDI encoders"
- [x] Add topics: `home-assistant`, `hacs`, `magewell`, `ndi`, `custom-component`
- [x] Issues are enabled

## Submit Brand Assets

- [ ] Create `icon.png` (256x256) and `icon@2x.png` (512x512) with the Magewell logo
- [ ] Fork [home-assistant/brands](https://github.com/home-assistant/brands)
- [ ] Add icons to `custom_integrations/magewell/`
- [ ] Open a PR — must be merged before HACS submission

## Submit to HACS Default

- [ ] Fork [hacs/default](https://github.com/hacs/default)
- [ ] Add `https://github.com/brianegge/homeassistant-magewell` to the `integration` file (alphabetically)
- [ ] Open a PR with links to:
  - Passing HACS validation run
  - Passing hassfest validation run
  - [v1.1.0 release](https://github.com/brianegge/homeassistant-magewell/releases/tag/v1.1.0)
- [ ] Do **not** comment on the PR during review — reviews take weeks to months

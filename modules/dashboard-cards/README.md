# Dashboard cards

Two small front-end modules for Home Assistant dashboards. Copy them to `/config/www/` and add each as a dashboard
resource of type *JavaScript module* (Settings → Dashboards → ⋮ → Resources), e.g. `/local/ingress-frame-card.js`.
Neither needs a restart; reload the page (Ctrl+F5) after adding them.

## `ingress-frame-card.js`: a hass_ingress panel inside a dashboard

[hass_ingress](https://github.com/lovelylain/hass_ingress) proxies a web app through Home Assistant's own login, but
the stock iframe card can't show it: inside the frame it lands on a nested Home Assistant page that can't sign in
(always in the Android/iOS apps). This card asks Home Assistant for the ingress session over its WebSocket and frames
the panel directly, so the app shows inside the dashboard with no extra tab and no second login.

```yaml
type: custom:ingress-frame-card
panel: my_terminal        # the hass_ingress panel slug
grid_options: { columns: full, rows: 15 }
```

The panel can be hidden from the sidebar (`show_in_sidebar: false`) and admin-only (`require_admin: true`). Keep in
mind that whoever can sign in to Home Assistant then reaches the app; turn on multi-factor authentication for sensitive
ones (a terminal, for example).

## `input-text-hints.js`: your own hint in empty text fields

Shows your text instead of "(empty value)" in an empty `input_text` row:

```yaml
type: entities
entities:
  - entity: input_text.mail_to
    placeholder: Write the recipient
```

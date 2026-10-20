// Placeholder hints for input_text rows in entities cards: shows your own text (e.g. "Write the subject") in an empty
// field instead of Home Assistant's "(empty value)". Add `placeholder:` to the row:
//   - entity: input_text.mail_subject
//     placeholder: Write the subject
// Lovelace resource (module): /local/input-text-hints.js
customElements.whenDefined("hui-input-text-entity-row").then(() => {
  const Row = customElements.get("hui-input-text-entity-row");
  const updated = Row.prototype.updated;
  Row.prototype.updated = function (changed) {
    updated?.call(this, changed);
    const hint = this._config?.placeholder;
    const input = hint && this.shadowRoot?.querySelector("ha-input");
    if (input) input.placeholder = hint;  // after HA's own render, so it wins
  };
});

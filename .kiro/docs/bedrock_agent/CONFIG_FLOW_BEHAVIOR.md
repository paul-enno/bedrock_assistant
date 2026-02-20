# Config Flow Behavior - When Are Changes Saved?

## Overview

This document clarifies when configuration changes are saved in the Bedrock Agent options flow.

## Save Behavior

### ✅ Changes Are Saved Immediately

When you click **Submit** in any configuration section (AI, Memory, or Tools), your changes are:

1. **Saved immediately** to the config entry
2. **Applied to the integration** right away
3. **Persisted** to disk

After saving, you are returned to the main menu where you can:
- Configure other sections
- Review your changes
- Close the dialog

### 🔄 Navigation Flow

```
Main Menu
  ↓ (select section)
Configuration Form
  ↓ (click Submit)
✅ CHANGES SAVED ← Happens here!
  ↓
Main Menu (return here)
  ↓ (close dialog or configure another section)
```

### 📝 What This Means

**For Users:**
- You don't need to worry about losing changes
- Each section saves independently
- You can configure sections in any order
- Closing the dialog doesn't lose your work (already saved)
- Changes take effect immediately

**Technical Details:**
- Uses `hass.config_entries.async_update_entry()` to save
- Options are merged with existing options
- Integration is notified of changes via `async_reload()`
- No "Apply" or "Save All" button needed

## Button Labels

### Current Implementation

Home Assistant uses standard button labels:
- **Submit** - The default button text (saves and returns to menu)
- **Cancel** - Discards changes and returns to menu

### Why "Submit" Instead of "Save"?

Home Assistant's design system uses "Submit" as the standard button label for forms. This is consistent across all integrations and provides a familiar experience for users.

The key is that the **description text** makes it clear that changes are saved:

> "Configure the AI model and system prompt. Changes are saved when you submit and you'll return to the main menu."

## Comparison with Other Patterns

### ❌ What We Don't Do

**Pattern 1: Save on Close**
```
Configure → Close → Save
```
Problem: Users might lose changes if they close accidentally

**Pattern 2: Explicit Save Button**
```
Configure → Click "Save" → Close
```
Problem: Extra step, users might forget to save

**Pattern 3: Apply Button**
```
Configure → Click "Apply" → Continue → Close
```
Problem: Confusing, when does it actually save?

### ✅ What We Do

**Pattern: Save on Submit**
```
Configure → Submit (saves) → Return to Menu
```
Benefits:
- Clear and immediate
- No risk of losing changes
- Consistent with Home Assistant patterns
- Users can configure multiple sections

## User Experience

### Scenario 1: Configure One Section

1. Open Options → See Menu
2. Click "AI Configuration"
3. Change model to Claude 3.5 Sonnet
4. Click Submit
5. ✅ **Changes saved!**
6. Return to Menu
7. Close dialog

Result: Model is changed and active

### Scenario 2: Configure Multiple Sections

1. Open Options → See Menu
2. Click "AI Configuration"
3. Change model
4. Click Submit → ✅ **AI changes saved!**
5. Back at Menu
6. Click "Memory Configuration"
7. Enable memory
8. Click Submit → ✅ **Memory changes saved!**
9. Back at Menu
10. Click "Tools Configuration"
11. Disable HA Control
12. Click Submit → ✅ **Tools changes saved!**
13. Back at Menu
14. Close dialog

Result: All three sections are configured and active

### Scenario 3: Change Mind

1. Open Options → See Menu
2. Click "AI Configuration"
3. Change model
4. Click Cancel (or back button)
5. ❌ **Changes NOT saved**
6. Back at Menu

Result: Original model still active

## Technical Implementation

### Save Method

```python
async def _update_options(self) -> ConfigFlowResult:
    """Update config entry options and return to menu."""
    # Merge current options with new options
    new_options = {**self.config_entry.options, **self._options}
    
    # Update the config entry (SAVES HERE!)
    self.hass.config_entries.async_update_entry(
        self.config_entry, options=new_options
    )
    
    # Clear the temporary options
    self._options = {}
    
    # Return to menu so user can configure other sections
    return await self.async_step_init()
```

### When Called

Each configuration step calls `_update_options()` when user submits:

```python
async def async_step_ai_config(self, user_input: dict[str, Any] | None = None):
    if user_input is not None:
        # User clicked Submit
        self._options.update(user_input)
        return await self._update_options()  # ← Saves and returns to menu
    
    # Show form
    return self.async_show_form(...)
```

## Summary

**When are changes saved?**
→ Immediately when you click Submit in any configuration section

**What happens after saving?**
→ You return to the main menu to configure other sections or exit

**Can I lose my changes?**
→ No, changes are saved immediately when you submit

**Do I need to click a "Save All" button?**
→ No, each section saves independently

**What if I click Cancel?**
→ Changes are NOT saved and you return to the menu

This design provides a clear, safe, and intuitive configuration experience!

# Button Label Fix - Submit Instead of Next

## Issue

The config flow forms were showing "Next" button instead of "Submit" button, which was confusing because:
- "Next" implies moving to another step without saving
- "Submit" clearly indicates that changes will be saved
- Home Assistant standard is to use "Submit" for forms that save data

## Root Cause

The `last_step` parameter in `async_show_form()` controls the button label:
- `last_step=False` → Shows "Next" button
- `last_step=True` or `None` (default) → Shows "Submit" button

We had incorrectly set `last_step=False` thinking it would help with navigation, but this caused the wrong button label to appear.

## Solution

Removed the `last_step=False` parameter from all three configuration forms:
- `async_step_ai_config()`
- `async_step_memory_config()`
- `async_step_tools_config()`

By not setting `last_step`, it defaults to `None`, which shows the "Submit" button.

## Changes Made

### Before
```python
return self.async_show_form(
    step_id="ai_config",
    data_schema=ai_schema,
    description_placeholders={...},
    last_step=False,  # ❌ Shows "Next" button
)
```

### After
```python
return self.async_show_form(
    step_id="ai_config",
    data_schema=ai_schema,
    description_placeholders={...},
    # ✅ Defaults to None, shows "Submit" button
)
```

## Button Behavior

### Submit Button
- **Label**: "Submit"
- **Action**: Saves changes and returns to menu
- **User expectation**: Clear that changes are being saved
- **Home Assistant standard**: ✅ Yes

### Cancel Button
- **Label**: "Cancel"
- **Action**: Discards changes and returns to menu
- **User expectation**: Clear that changes are discarded
- **Home Assistant standard**: ✅ Yes

## User Experience

### Before (Confusing)
```
Form with "Next" button
↓ (click Next)
❓ Are changes saved? Unclear!
```

### After (Clear)
```
Form with "Submit" button
↓ (click Submit)
✅ Changes saved! Clear!
↓
Return to menu
```

## Description Text

Each form also includes clear description text:

**AI Configuration:**
> "Configure the AI model and system prompt. Changes are saved when you submit and you'll return to the main menu."

**Memory Configuration:**
> "Configure memory settings. Changes are saved when you submit and you'll return to the main menu."

**Tools Configuration:**
> "Configure which tools the agent can use. Changes are saved when you submit and you'll return to the main menu."

## Technical Details

### Home Assistant Standards

From Home Assistant's `data_entry_flow.py`:

```python
def async_show_form(
    self,
    *,
    step_id: str | None = None,
    data_schema: vol.Schema | None = None,
    errors: dict[str, str] | None = None,
    description_placeholders: Mapping[str, str] | None = None,
    last_step: bool | None = None,  # Display next or submit button in frontend
    preview: str | None = None,
) -> _FlowResultT:
```

The `last_step` parameter comment clearly states: "Display next or submit button in frontend"

### Button Label Logic

- `last_step=False` → "Next" (for multi-step flows where you move to next step)
- `last_step=True` → "Submit" (for final step that saves)
- `last_step=None` (default) → "Submit" (standard behavior)

### Our Use Case

We have a menu-based flow where each form:
1. Saves changes when submitted
2. Returns to menu (not to another form step)
3. Is not part of a linear multi-step flow

Therefore, we should use "Submit" button (default behavior).

## Testing

All tests pass with the new button labels:
- ✅ 44/44 tests passing (100%)
- ✅ MyPy type checking passes
- ✅ All config flow tests pass
- ✅ Navigation works correctly

## Comparison with Other Integrations

Most Home Assistant integrations use "Submit" for forms that save data:

**Linear Multi-Step Flow (uses "Next"):**
```
Step 1 → Next → Step 2 → Next → Step 3 → Submit
```

**Menu-Based Flow (uses "Submit"):**
```
Menu → Form → Submit → Menu
```

Our integration uses the menu-based pattern, so "Submit" is correct.

## Summary

**What changed:**
- Removed `last_step=False` from all three config forms
- Button now shows "Submit" instead of "Next"

**Why it matters:**
- Clear user expectation that changes are saved
- Follows Home Assistant standards
- Reduces confusion about when changes take effect

**Result:**
- ✅ Clear button labels
- ✅ Follows Home Assistant patterns
- ✅ All tests pass
- ✅ Better user experience

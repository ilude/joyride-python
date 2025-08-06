# VS CODE PROMPT FILE USAGE FOR LIFECYCLE REFACTORING

This document explains how to use the VS Code prompt file feature for lifecycle refactoring.

## Convention Over Configuration

The lifecycle refactoring uses a **single generic prompt file** that automatically detects which step to implement based on your command.

## Usage

In VS Code chat, use natural language commands like:

```
/lifecycle-refactor-step complete lifecycle refactoring step 1
```

```
/lifecycle-refactor-step complete lifecycle refactoring step 4
```

```
/lifecycle-refactor-step complete lifecycle refactoring step 9
```

The prompt file will automatically:
1. **Parse your command** to extract the step number
2. **Reference the procedure file** (.chat_planning/LIFECYCLE_REFACTORING_PROCEDURE.md)
3. **Implement the specified step** completely
4. **Run tests** and ensure they pass
5. **Ask for continuation** to the next step

## Command Variations

These commands all work:
- "complete lifecycle refactoring step 1"
- "implement step 3"
- "do step 5"
- "execute lifecycle refactoring step 7"

## VS Code Setup

1. **Enable prompt files** in VS Code settings:
   ```json
   "chat.promptFiles": true
   ```

2. **The prompt file is located at**:
   ```
   .github/prompts/lifecycle-refactor-step.prompt.md
   ```

3. **Access via**:
   - Type `/lifecycle-refactor-step` in VS Code chat
   - Or use Command Palette: "Chat: Run Prompt" → select "lifecycle-refactor-step"

## Benefits of This Approach

- **Convention over Configuration**: No template variables to replace
- **Natural Language Commands**: Use intuitive phrases to specify steps
- **Single Source of Truth**: All implementation details stay in LIFECYCLE_REFACTORING_PROCEDURE.md
- **No File Management**: One prompt file handles all 9 steps
- **Easy Maintenance**: Update procedure document once, prompt benefits
- **VS Code Integration**: Native prompt file support with GPT-4
- **Consistent Behavior**: Every step follows the same implementation pattern

## File Structure

```
.github/prompts/
└── lifecycle-refactor-step.prompt.md    # Single prompt for all steps

.chat_planning/
├── LIFECYCLE_REFACTORING_PROCEDURE.md   # Master implementation guide
└── PROMPT_TEMPLATE_USAGE.md            # This usage guide (updated)
```

## Workflow Example

1. **Start Step 1**:
   ```
   /lifecycle-refactor-step complete lifecycle refactoring step 1
   ```

2. **Copilot implements Step 1**:
   - Creates types.py and interfaces.py
   - Creates comprehensive tests
   - Runs `make test` until it passes
   - Reports "Step 1 completed successfully"

3. **Continue to Step 2**:
   ```
   /lifecycle-refactor-step complete lifecycle refactoring step 2
   ```

4. **Repeat until complete** (Steps 1-9)

## Technical Details

- **Model**: Uses GPT-4 as specified in prompt file metadata
- **Mode**: Edit mode for direct file modifications
- **Tools**: Terminal and file tools enabled
- **Auto-detection**: Parses step number from natural language commands
- **Error Handling**: Continues debugging until tests pass
- **Progress Tracking**: Clear completion confirmations and next step prompts

This approach eliminates configuration overhead while providing a smooth, intuitive workflow for the entire lifecycle refactoring process.

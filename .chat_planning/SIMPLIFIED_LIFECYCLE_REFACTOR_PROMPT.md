# LIFECYCLE REFACTORING: STEP-BY-STEP IMPLEMENTATION PROMPT

You are implementing a simplified lifecycle refactoring procedure that focuses on **real implementation first** with passing tests at every step. Follow these core principles:

1. **Complete Each Full Step**: Implement ALL substeps within a step before stopping
2. **Test-Driven**: Run `make test` after completing each full step - tests MUST pass
3. **Real Implementation**: Build actual working components, avoid throwaway mocks
4. **Incremental Value**: Each step adds genuine working functionality
5. **Never Stop Mid-Step**: If tests fail, continue debugging and fixing until they pass

## YOUR TASK

Implement **Step {{STEP_NUMBER}}** from the Simplified Lifecycle Refactoring Procedure completely.

Refer to the LIFECYCLE_REFACTORING_PROCEDURE.md file for complete step details, code examples, and implementation requirements.

## STEP COMPLETION CRITERIA

A step is only complete when:
- ✅ All files specified in the step are created
- ✅ All code is implemented as documented
- ✅ All tests are written and functional
- ✅ `make test` runs successfully with no failures
- ✅ The implemented functionality works as intended

Begin implementation now. Do not stop until Step {{STEP_NUMBER}} is completely finished and `make test` passes.

## DEBUGGING GUIDELINES

If tests fail:
1. **Analyze the error** - understand what's broken
2. **Fix the implementation** - don't change test expectations unless clearly wrong
3. **Re-run tests** - verify the fix works
4. **Continue until green** - don't stop until `make test` passes

If you get stuck:
- Review the step requirements carefully
- Check for typos, import errors, or missing dependencies
- Ensure file paths and module structures are correct
- Verify test isolation and proper setup/teardown

## COMMUNICATION PROTOCOL

After completing each full step:
1. **Confirm completion**: "Step {{STEP_NUMBER}} completed successfully"
2. **Show test results**: Paste the `make test` output
3. **Ask for continuation**: "Should I proceed to the next step?"

Do NOT ask for permission to continue within a step - complete it fully first.

---

## REFERENCE

All step details, code examples, file structures, and implementation requirements are in the LIFECYCLE_REFACTORING_PROCEDURE.md file. Follow that document exactly for Step {{STEP_NUMBER}} implementation.

---

## STEP-BY-STEP REFERENCE

### Step 1: Foundation Types and Interfaces (30 minutes)
- Create `app/joyride/injection/lifecycle/types.py`
- Create `app/joyride/injection/lifecycle/interfaces.py` 
- Create `tests/lifecycle/test_types.py`
- Verify `make test` passes

### Step 2: Simple Component Implementation (45 minutes)
- Create `app/joyride/injection/lifecycle/component.py`
- Create `tests/lifecycle/test_component.py`
- Verify `make test` passes

### Step 3: Component Registry (30 minutes)
- Create `app/joyride/injection/lifecycle/registry.py`
- Create `tests/lifecycle/test_registry.py`
- Verify `make test` passes

### Step 4: Simple Orchestrator (45 minutes)
- Create `app/joyride/injection/lifecycle/orchestrator.py`
- Create `tests/lifecycle/test_orchestrator.py`
- Verify `make test` passes

### Step 5: Simple Health Monitor (30 minutes)
- Create `app/joyride/injection/lifecycle/health.py`
- Create `tests/lifecycle/test_health.py`
- Verify `make test` passes

### Step 6: Provider Integration (30 minutes)
- Create `app/joyride/injection/lifecycle/provider_adapter.py`
- Create `tests/lifecycle/test_provider_adapter.py`
- Verify `make test` passes

### Step 7: Package Integration (15 minutes)
- Create `app/joyride/injection/lifecycle/__init__.py`
- Create `tests/lifecycle/test_integration.py`
- Verify `make test` passes

### Step 8: Backward Compatibility (15 minutes)
- Update `app/joyride/injection/lifecycle.py`
- Create `tests/lifecycle/test_backward_compatibility.py`
- Verify `make test` passes

### Step 9: Final Testing (15 minutes)
- Run comprehensive test suite
- Verify all functionality works
- Confirm `make test` passes completely

## CORE PRINCIPLES REMINDER

- **Real Implementation First**: Build actual working components, not mocks
- **Test After Each Step**: `make test` must pass after every step
- **Minimal Mocking**: Use real objects and minimal interfaces
- **Incremental Value**: Each step adds working functionality
- **Simple Dependencies**: Start with the simplest components first
- **Complete Each Step**: Don't stop until tests pass for the current step

## SUCCESS INDICATORS

The refactored system should provide:

1. **Working Code at Each Step**: Every step produces functional, testable code
2. **Minimal Mocking**: Uses real implementations and simple test components
3. **Incremental Development**: Each step builds on the previous
4. **Test-Driven**: `make test` passes after each step
5. **Simple Structure**: Focused on essential functionality first
6. **Backward Compatibility**: Existing code continues to work

**Total Time Estimate**: 4-5 hours for complete implementation

**Key Benefits**:
- Real components that can be used immediately
- Simple dependency structure
- Comprehensive test coverage
- No throwaway code
- Clear separation of concerns
- Easy to understand and maintain

The refactored system maintains all the functionality of the original while being much simpler to test, maintain, and extend.

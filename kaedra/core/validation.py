"""
Validation Hooks for Thread-Based Engineering
Implements the "stop hook" pattern for L-threads.
"""
from dataclasses import dataclass
from typing import Any, Callable, List, Optional
import subprocess
import logging

log = logging.getLogger("kaedra.validation")


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    message: str = ""
    should_continue: bool = True
    score: float = 0.0
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ValidationHook:
    """
    Base validation hook - the "stop hook" pattern.

    When an L-thread tries to stop, the validation hook runs
    deterministic code to decide:
    1. Is the work complete? (passed=True → stop)
    2. Should we continue? (should_continue=True → loop again)
    3. Should we abort? (should_continue=False → stop with failure)
    """

    def validate(self, result: Any) -> ValidationResult:
        """Override this method to implement custom validation."""
        return ValidationResult(passed=True, message="No validation defined")


class CommandValidationHook(ValidationHook):
    """
    Validate by running a shell command.
    Perfect for: tests, linters, build checks.
    """

    def __init__(
        self,
        command: str,
        cwd: Optional[str] = None,
        success_codes: Optional[List[int]] = None,
        timeout_s: float = 60.0,
    ):
        self.command = command
        self.cwd = cwd
        self.success_codes = success_codes or [0]
        self.timeout_s = timeout_s

    def validate(self, result: Any) -> ValidationResult:
        try:
            proc = subprocess.run(
                self.command,
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
            )

            passed = proc.returncode in self.success_codes
            return ValidationResult(
                passed=passed,
                message=f"Exit code: {proc.returncode}",
                should_continue=not passed,  # Continue if failed
                metadata={
                    "stdout": proc.stdout[:1000] if proc.stdout else "",
                    "stderr": proc.stderr[:1000] if proc.stderr else "",
                    "returncode": proc.returncode,
                },
            )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                passed=False,
                message=f"Command timed out after {self.timeout_s}s",
                should_continue=False,  # Don't retry timeouts
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Command error: {e}",
                should_continue=True,  # Retry on errors
            )


class PylintValidationHook(ValidationHook):
    """
    Validate code quality using Pylint score.
    """

    def __init__(
        self,
        target_score: float = 9.0,
        module: str = ".",
        cwd: Optional[str] = None,
    ):
        self.target_score = target_score
        self.module = module
        self.cwd = cwd

    def validate(self, result: Any) -> ValidationResult:
        try:
            proc = subprocess.run(
                f"py -3.12 -m pylint {self.module} --score=y",
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=120.0,
            )

            # Parse score from output
            score = 0.0
            for line in proc.stdout.split("\n"):
                if "rated at" in line:
                    try:
                        # "Your code has been rated at 7.68/10"
                        score_str = line.split("rated at")[1].split("/")[0].strip()
                        score = float(score_str)
                        break
                    except (IndexError, ValueError):
                        pass

            passed = score >= self.target_score
            return ValidationResult(
                passed=passed,
                message=f"Pylint score: {score:.2f}/10 (target: {self.target_score})",
                should_continue=not passed and score > 0,
                score=score,
                metadata={"target_score": self.target_score},
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Pylint error: {e}",
                should_continue=True,
            )


class TestValidationHook(ValidationHook):
    """
    Validate by running pytest.
    """

    def __init__(
        self,
        test_path: str = "tests/",
        cwd: Optional[str] = None,
        required_pass_rate: float = 1.0,
    ):
        self.test_path = test_path
        self.cwd = cwd
        self.required_pass_rate = required_pass_rate

    def validate(self, result: Any) -> ValidationResult:
        try:
            proc = subprocess.run(
                f"py -3.12 -m pytest {self.test_path} -v --tb=short",
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=300.0,
            )

            # Parse test results
            passed_count = 0
            failed_count = 0
            for line in proc.stdout.split("\n"):
                if " passed" in line:
                    try:
                        passed_count = int(line.split(" passed")[0].split()[-1])
                    except ValueError:
                        pass
                if " failed" in line:
                    try:
                        failed_count = int(line.split(" failed")[0].split()[-1])
                    except ValueError:
                        pass

            total = passed_count + failed_count
            pass_rate = passed_count / total if total > 0 else 0.0
            passed = pass_rate >= self.required_pass_rate

            return ValidationResult(
                passed=passed,
                message=f"Tests: {passed_count}/{total} passed ({pass_rate:.1%})",
                should_continue=not passed,
                score=pass_rate,
                metadata={
                    "passed_count": passed_count,
                    "failed_count": failed_count,
                    "total": total,
                },
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Test error: {e}",
                should_continue=True,
            )


class CompositeValidationHook(ValidationHook):
    """
    Combine multiple validators - all must pass.
    """

    def __init__(self, validators: List[ValidationHook], require_all: bool = True):
        self.validators = validators
        self.require_all = require_all

    def validate(self, result: Any) -> ValidationResult:
        results = []
        all_passed = True
        any_passed = False
        messages = []

        for v in self.validators:
            r = v.validate(result)
            results.append(r)
            if r.passed:
                any_passed = True
            else:
                all_passed = False
            messages.append(r.message)

        passed = all_passed if self.require_all else any_passed
        should_continue = any(r.should_continue for r in results)

        return ValidationResult(
            passed=passed,
            message=" | ".join(messages),
            should_continue=should_continue and not passed,
            metadata={"sub_results": [r.message for r in results]},
        )


class CallableValidationHook(ValidationHook):
    """
    Wrap a simple callable as a validation hook.
    """

    def __init__(self, fn: Callable[[Any], bool], message: str = "Custom validation"):
        self.fn = fn
        self.message = message

    def validate(self, result: Any) -> ValidationResult:
        try:
            passed = self.fn(result)
            return ValidationResult(
                passed=passed,
                message=self.message,
                should_continue=not passed,
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"{self.message}: {e}",
                should_continue=True,
            )


# Convenience functions
def validate_command(command: str, **kwargs) -> ValidationHook:
    """Create a command-based validator."""
    return CommandValidationHook(command, **kwargs)


def validate_pylint(target_score: float = 9.0, **kwargs) -> ValidationHook:
    """Create a Pylint score validator."""
    return PylintValidationHook(target_score, **kwargs)


def validate_tests(test_path: str = "tests/", **kwargs) -> ValidationHook:
    """Create a pytest validator."""
    return TestValidationHook(test_path, **kwargs)


def validate_all(*validators: ValidationHook) -> ValidationHook:
    """Combine validators - all must pass."""
    return CompositeValidationHook(list(validators), require_all=True)


def validate_any(*validators: ValidationHook) -> ValidationHook:
    """Combine validators - any must pass."""
    return CompositeValidationHook(list(validators), require_all=False)

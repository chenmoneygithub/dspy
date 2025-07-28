"""DSPy Variable system for optimizable and translatable strings.

Variables are used to wrap strings that should be:
1. Visible to DSPy optimizers for optimization purposes
2. Subject to i18n translations based on locale settings

Similar to PyTorch's Parameter system, each Variable has a unique identifier
and can be looked up from the module level.
"""

import inspect
import uuid
import weakref
from typing import Any, Optional


class VariableRegistry:
    """Global registry for tracking all Variable instances."""
    
    def __init__(self):
        self._variables = weakref.WeakValueDictionary()
        self._variables_by_semantic_name = {}
    
    def register(self, variable: "Variable") -> None:
        """Register a variable in the global registry."""
        self._variables[variable.id] = variable
        if variable.semantic_name:
            if variable.semantic_name in self._variables_by_semantic_name:
                # Allow multiple variables with same semantic name, store as list
                existing = self._variables_by_semantic_name[variable.semantic_name]
                if not isinstance(existing, list):
                    self._variables_by_semantic_name[variable.semantic_name] = [existing, variable]
                else:
                    existing.append(variable)
            else:
                self._variables_by_semantic_name[variable.semantic_name] = variable
    
    def get_variable(self, identifier: str) -> Optional["Variable"]:
        """Get a variable by ID or semantic name."""
        # Try by ID first
        if identifier in self._variables:
            return self._variables[identifier]
        
        # Try by semantic name
        if identifier in self._variables_by_semantic_name:
            result = self._variables_by_semantic_name[identifier]
            if isinstance(result, list):
                return result[0]  # Return first if multiple
            return result
        
        return None
    
    def list_variables(self) -> dict[str, "Variable"]:
        """Get all registered variables."""
        return dict(self._variables)
    
    def list_variables_by_semantic_name(self) -> dict[str, "Variable"]:
        """Get variables grouped by semantic name."""
        result = {}
        for name, var in self._variables_by_semantic_name.items():
            if isinstance(var, list):
                result[name] = var[0]  # Take first if multiple
            else:
                result[name] = var
        return result
    
    def clear(self) -> None:
        """Clear all registered variables (mainly for testing)."""
        self._variables.clear()
        self._variables_by_semantic_name.clear()


# Global registry instance
_registry = VariableRegistry()

# Global counter for auto-generated variable names
_variable_counter = 0


def _generate_auto_name() -> str:
    """Generate an automatic semantic name using stack inspection."""
    global _variable_counter
    _variable_counter += 1
    
    # Look through the call stack to find a meaningful context
    frame = None
    try:
        # Skip current frame (0) and caller frame (1), look for actual usage context
        for i in range(2, 10):  # Search up to 10 frames up
            try:
                frame = inspect.currentframe()
                for _ in range(i):
                    frame = frame.f_back
                if frame is None:
                    break
                    
                # Get class and method information
                class_name = "Unknown"
                method_name = "unknown"
                
                # Try to get the class name from self
                local_vars = frame.f_locals
                if 'self' in local_vars:
                    class_name = local_vars['self'].__class__.__name__
                
                # Get the function/method name
                code = frame.f_code
                method_name = code.co_name
                
                # Skip internal Python methods and __init__ if possible
                if method_name not in ('__new__', '__init__', '<module>') or i >= 5:
                    # Create a meaningful name
                    return f"{class_name}.{method_name}.var_{_variable_counter}"
                    
            except (AttributeError, ValueError):
                continue
                
    except Exception:
        pass
    finally:
        if frame:
            del frame
    
    # Fallback to simple counter-based name
    return f"auto_variable_{_variable_counter}"


class Variable:
    """A Variable represents an optimizable and translatable string.
    
    Variables are used to wrap strings that need to be:
    1. Visible to DSPy optimizers for optimization
    2. Subject to i18n translations based on locale
    
    Examples:
        # Basic usage
        question_desc = Variable("input.question.desc", "The question to answer")
        
        # With description for optimizers
        reasoning_prefix = Variable(
            "cot.reasoning.prefix", 
            "Reasoning: Let's think step by step in order to",
            description="Prefix for chain-of-thought reasoning"
        )
        
        # Anonymous variable (auto-generated ID)
        error_msg = Variable(default_value="An error occurred")
    """
    
    def __init__(
        self, 
        semantic_name: Optional[str] = None,
        default_value: str = "",
        description: Optional[str] = None,
        trainable: bool = True,
        **metadata: Any
    ):
        """Initialize a Variable.
        
        Args:
            semantic_name: Human-readable identifier (e.g., "input.question.desc").
                          If None, an auto-generated ID will be used.
            default_value: The default string value
            description: Description of what this variable represents (for optimizers)
            trainable: Whether this variable should be included in optimization
            **metadata: Additional metadata for optimizers or other systems
        """
        self.id = str(uuid.uuid4())
        self.semantic_name = semantic_name if semantic_name is not None else _generate_auto_name()
        self.default_value = default_value
        self.description = description
        self.trainable = trainable
        self.metadata = metadata
        
        # Locale-specific overrides
        self._locale_values = {}
        
        # Register in global registry
        _registry.register(self)
    
    def __str__(self) -> str:
        """Return the resolved string value for current locale."""
        return self.resolve()
    
    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        name = self.semantic_name or f"id={self.id[:8]}..."
        return f"Variable({name!r}, {self.default_value!r})"
    
    def resolve(self, locale: Optional[str] = None) -> str:
        """Resolve the variable value for the given locale.
        
        Args:
            locale: The locale to resolve for. If None, uses current dspy.settings locale.
            
        Returns:
            The resolved string value
        """
        if locale is None:
            # Import here to avoid circular imports
            try:
                from dspy.dsp.utils.settings import settings
                locale = getattr(settings, 'locale', None)
            except (ImportError, AttributeError):
                locale = None
        
        # Check for locale-specific override first
        if locale and locale in self._locale_values:
            return self._locale_values[locale]
        
        # Try gettext translation if locale is specified
        if locale:
            try:
                from dspy.i18n import translate
                translated = translate(self.default_value, locale)
                if translated != self.default_value:
                    return translated
            except (ImportError, Exception):
                # Fall back to default if translation fails
                pass
        
        # Fall back to default value
        return self.default_value
    
    def set_locale_value(self, locale: str, value: str) -> None:
        """Set a locale-specific value for this variable.
        
        Args:
            locale: The locale code (e.g., "zh-cn", "es", "fr")
            value: The translated value
        """
        self._locale_values[locale] = value
    
    def get_locale_value(self, locale: str) -> Optional[str]:
        """Get the locale-specific value if set.
        
        Args:
            locale: The locale code
            
        Returns:
            The locale-specific value or None if not set
        """
        return self._locale_values.get(locale)
    
    def list_locales(self) -> list[str]:
        """List all locales that have values set."""
        return list(self._locale_values.keys())
    
    def copy(self) -> "Variable":
        """Create a copy of this variable with a new ID."""
        new_var = Variable(
            semantic_name=self.semantic_name,
            default_value=self.default_value,
            description=self.description,
            **self.metadata
        )
        new_var._locale_values = self._locale_values.copy()
        return new_var
    
    def to_dict(self) -> dict:
        """Export variable to dictionary (for serialization)."""
        return {
            "id": self.id,
            "semantic_name": self.semantic_name,
            "default_value": self.default_value,
            "description": self.description,
            "trainable": self.trainable,
            "metadata": self.metadata,
            "locale_values": self._locale_values.copy()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Variable":
        """Create Variable from dictionary (for deserialization)."""
        var = cls(
            semantic_name=data.get("semantic_name"),
            default_value=data.get("default_value", ""),
            description=data.get("description"),
            trainable=data.get("trainable", True),
            **data.get("metadata", {})
        )
        var.id = data.get("id", var.id)  # Preserve ID if available
        var._locale_values = data.get("locale_values", {}).copy()
        return var


# Convenience functions for the registry
def get_variable(identifier: str) -> Optional[Variable]:
    """Get a variable by ID or semantic name."""
    return _registry.get_variable(identifier)


def list_variables() -> dict[str, Variable]:
    """Get all registered variables."""
    return _registry.list_variables()


def list_variables_by_semantic_name() -> dict[str, Variable]:
    """Get variables grouped by semantic name."""
    return _registry.list_variables_by_semantic_name()


def clear_variables() -> None:
    """Clear all registered variables (mainly for testing)."""
    _registry.clear()
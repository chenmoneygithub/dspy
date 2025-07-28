#!/usr/bin/env python3
"""Basic test for the dspy.Variable system."""

import sys
import os

# Add the dspy directory to the path so we can import it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

import dspy
from dspy import Variable, InputField, OutputField
from dspy.signatures import Signature


def test_basic_variable():
    """Test basic Variable functionality."""
    print("Testing basic Variable functionality...")
    
    # Create a simple variable
    greeting_var = Variable("greeting", "Hello, world!", description="A greeting message")
    
    print(f"Variable value: {greeting_var}")
    print(f"Variable repr: {repr(greeting_var)}")
    print(f"Default value: {greeting_var.default_value}")
    print(f"Semantic name: {greeting_var.semantic_name}")
    print(f"Description: {greeting_var.description}")
    
    assert str(greeting_var) == "Hello, world!"
    print("✓ Basic Variable test passed")


def test_variable_in_fields():
    """Test Variable in InputField and OutputField."""
    print("\nTesting Variable in Fields...")
    
    question_desc = Variable("input.question.desc", "The question to answer")
    answer_desc = Variable("output.answer.desc", "The answer to the question")
    
    # Create a signature using Variables
    class QASignature(Signature):
        """Answer questions based on the given context."""
        question: str = InputField(desc=question_desc)
        answer: str = OutputField(desc=answer_desc)
    
    print(f"Question field desc: {QASignature.input_fields['question'].json_schema_extra['desc']}")
    print(f"Answer field desc: {QASignature.output_fields['answer'].json_schema_extra['desc']}")
    
    # Check that the resolved values are correct
    assert QASignature.input_fields['question'].json_schema_extra['desc'] == "The question to answer"
    assert QASignature.output_fields['answer'].json_schema_extra['desc'] == "The answer to the question"
    print("✓ Variable in Fields test passed")


def test_variable_registry():
    """Test the Variable registry system."""
    print("\nTesting Variable registry...")
    
    test_var = Variable("test.registry", "test value")
    
    # Test getting by semantic name
    retrieved = dspy.get_variable("test.registry")
    assert retrieved is test_var
    
    # Test listing variables
    all_vars = dspy.list_variables()
    assert test_var.id in all_vars
    
    vars_by_name = dspy.list_variables_by_semantic_name()
    assert "test.registry" in vars_by_name
    
    print("✓ Variable registry test passed")


def test_locale_support():
    """Test locale configuration."""
    print("\nTesting locale support...")
    
    # Test setting locale in configure
    try:
        dspy.configure(locale="zh-cn")
        print("✓ Locale configuration test passed")
    except Exception as e:
        print(f"✗ Locale configuration failed: {e}")
        raise


def test_variable_with_locale():
    """Test Variable with locale-specific values."""
    print("\nTesting Variable with locale values...")
    
    hello_var = Variable("greeting.hello", "Hello", description="Greeting")
    hello_var.set_locale_value("zh-cn", "你好")
    hello_var.set_locale_value("es", "Hola")
    
    # Test default value (first clear any locale setting)
    dspy.configure(locale=None)
    resolved_default = hello_var.resolve()
    print(f"Resolved default value: {resolved_default!r}")
    assert resolved_default == "Hello", f"Expected 'Hello', got {resolved_default!r}"
    
    # Test locale-specific values
    assert hello_var.resolve("zh-cn") == "你好"
    assert hello_var.resolve("es") == "Hola"
    
    # Test that setting locale in dspy affects resolution
    dspy.configure(locale="zh-cn")
    assert hello_var.resolve() == "你好"
    
    # Test locale listing
    locales = hello_var.list_locales()
    assert "zh-cn" in locales
    assert "es" in locales
    
    print("✓ Variable locale test passed")


def test_chainofthought_integration():
    """Test that ChainOfThought uses Variables."""
    print("\nTesting ChainOfThought integration...")
    
    try:
        from dspy.predict.chain_of_thought import COT_REASONING_PREFIX, COT_REASONING_DESC
        
        print(f"COT reasoning prefix: {COT_REASONING_PREFIX}")
        print(f"COT reasoning desc: {COT_REASONING_DESC}")
        
        assert isinstance(COT_REASONING_PREFIX, Variable)
        assert isinstance(COT_REASONING_DESC, Variable)
        assert str(COT_REASONING_PREFIX) == "Reasoning: Let's think step by step in order to"
        assert str(COT_REASONING_DESC) == "${reasoning}"
        
        print("✓ ChainOfThought integration test passed")
    except ImportError as e:
        print(f"⚠ ChainOfThought test skipped due to import error: {e}")


if __name__ == "__main__":
    print("Running dspy.Variable system tests...\n")
    
    try:
        test_basic_variable()
        test_variable_in_fields()
        test_variable_registry()
        test_locale_support()
        test_variable_with_locale()
        test_chainofthought_integration()
        
        print(f"\n🎉 All tests passed! Variable system is working correctly.")
        
        # Show summary of registered variables
        print(f"\nRegistered variables:")
        vars_by_name = dspy.list_variables_by_semantic_name()
        for name, var in vars_by_name.items():
            print(f"  {name}: {var.default_value!r}")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
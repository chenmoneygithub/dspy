---
sidebar_position: 1
---

!!! warning "This page is outdated and may not be fully accurate in DSPy 2.5"

# Examples in DSPy

Working in DSPy involves training sets, development sets, and test sets. This is like traditional ML, but you usually need far fewer labels (or zero labels) to use DSPy effectively.

The core data type for data in DSPy is `Example`. You will use **Examples** to represent items in your training set and test set. 

DSPy **Examples** are similar to Python `dict`s but have a few useful utilities. Your DSPy modules will return values of the type `Prediction`, which is a special sub-class of `Example`.

## Creating an `Example`

When you use DSPy, you will do a lot of evaluation and optimization runs. Your individual datapoints will be of type `Example`:

```python
qa_pair = dspy.Example(question="This is a question?", answer="This is an answer.")

print(qa_pair)
print(qa_pair.question)
print(qa_pair.answer)
```
**Output:**
```text
Example({'question': 'This is a question?', 'answer': 'This is an answer.'}) (input_keys=None)
This is a question?
This is an answer.
```

Examples can have any field keys and any value types, though usually values are strings.

```text
object = Example(field1=value1, field2=value2, field3=value3, ...)
```

## Specifying Input Keys

In traditional ML, there are separated "inputs" and "labels".

In DSPy, the `Example` objects have a `with_inputs()` method, which can mark specific fields as inputs. (The rest are just metadata or labels.)

```python
# Single Input.
print(qa_pair.with_inputs("question"))

# Multiple Inputs; be careful about marking your labels as inputs unless you mean it.
print(qa_pair.with_inputs("question", "answer"))
```

This flexibility allows for customized tailoring of the `Example` object for different DSPy scenarios.

When you call `with_inputs()`, you get a new copy of the example. The original object is kept unchanged.


## Element Access and Updation

Values can be accessed using the `.`(dot) operator. You can access the value of key `name` in defined object `Example(name="John Doe", job="sleep")` through `object.name`. 

To access or exclude certain keys, use `inputs()` and `labels()` methods to return new Example objects containing only input or non-input keys, respectively.

```python
article_summary = dspy.Example(article= "This is an article.", summary= "This is a summary.").with_inputs("article")

input_key_only = article_summary.inputs()
non_input_key_only = article_summary.labels()

print("Example object with Input fields only:", input_key_only)
print("Example object with Non-Input fields only:", non_input_key_only)
```

**Output**
```
Example object with Input fields only: Example({'article': 'This is an article.'}) (input_keys=None)
Example object with Non-Input fields only: Example({'summary': 'This is a summary.'}) (input_keys=None)
```

To exclude keys, use `without()`:

```python
article_summary = dspy.Example(context="This is an article.", question="This is a question?", answer="This is an answer.", rationale= "This is a rationale.").with_inputs("context", "question")

print("Example object without answer & rationale keys:", article_summary.without("answer", "rationale"))
```

**Output**
```
Example object without answer & rationale keys: Example({'context': 'This is an article.', 'question': 'This is a question?'}) (input_keys=None)
```

Updating values is simply assigning a new value using the `.` operator.

```python
article_summary.context = "new context"
```

## Iterating over Example

Iteration in the `Example` class also functions like a dictionary, supporting methods like `keys()`, `values()`, etc: 

```python
for k, v in article_summary.items():
    print(f"{k} = {v}")
```

**Output**

```text
context = This is an article.
question = This is a question?
answer = This is an answer.
rationale = This is a rationale.
```

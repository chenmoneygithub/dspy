# Creating Custom RM Client

DSPy provides support for various retrieval modules out of the box like `ColBERTv2`, `AzureCognitiveSearch`, `Lancedb`, `Pinecone`, `Weaviate`, etc. Unlike Language Model (LM) modules, creating a custom RM module is much more simple and flexible. 

As of now, DSPy offers 2 ways to create a custom RM: the Pythonic way and the DSPythonic way. We'll take a look at both, understand why both are performing the same behavior, and how you can implement each!

## I/O of RM Client

Before understanding the implementation, let's understand the idea and I/O within RM modules. 

The **input** to an RM module is either 1) a single query or 2) a list of queries.

The **output** is the `top-k` passages per query retrieved from a retrieval model, vector store, or search client. 

![I/O in RM Module](./img/io_rm_module.png)

Conventionally, we simply call the RM module object through the `__call__` method, inputting the query/queries as argument(s) of the call with the corresponding output returned as a list of strings. 

We'll see how this I/O is essentially same in both methods of implementation but differs in their delivery.

## The Pythonic Way

To account for our RM I/O, we create a class that conducts the retrieval logic, which we implement in the `__init__` and `__call__` methods:

```python
from typing import List, Union

class PythonicRMClient:
    def __init__(self):
        pass

    def __call__(self, query: Union[str, List[str]], k:int) -> Union[List[str], List[List[str]]]:
        pass
```

!!! info
    Don't worry about the extensive type-hinting above. `typing` is a package that provides type-definitions for function inputs and outputs.

    `Union` covers all possible types of the argument/output. So:
    * `Union[str, List[str]]`: Assigned to `query` to work with a single query string or a list of queries strings.
    * `Union[List[str], List[List[str]]]`: Assigned to the output of `__call__` to work with a single query string as a list or a list of multiple query string lists.

So let's start by implementing `PythonicRMClient` for a local retrieval model hosted on a API with endpoint being `/`. We'll start by implementing the `__init__` method, which simply initializes the class attributes, `url` and `port`, and attaches the port to the url if present.

```python
def __init__(self, url: str, port:int = None):
    self.url = f`{url}:{port}` if port else url
```

Now it's time to write the retrieval logic in `__call__` method:

```python
def __call__(self, query:str, k:int) -> List[str]:
    params = {"query": query, "k": k}
    response = requests.get(self.url, params=params)

    response = response.json()["retrieved_passages"]    # List of top-k passages
    return response
```

This serves to represent our API request call to retrieve our list of **top-k passages** which we return as the response. Let's bring it all together and see how our RM class looks like:

```python
from typing import List

class PythonicRMClient:
    def __init__(self, url: str, port:int = None):
        self.url = f`{url}:{port}` if port else url

    def __call__(self, query:str, k:int) -> List[str]:
        # Only accept single query input, feel free to modify it to support 

        params = {"query": query, "k": k}
        response = requests.get(self.url, params=params)

        response = response.json()["retrieved_passages"]    # List of top k passages
        return response
```

That's all!! This is the most basic way to implement a RM model and mirrors DSP-v1-hosted RM models like `ColBERTv2` and `AzureCognitiveSearch`. 

Now let's take a look at how we streamline this process in DSPy!

## The DSPythonic Way

The DSPythonic way mirrors the Pythonic way in maintaining the same input but now returning an object of `dspy.Prediction` class, the standard output format for any DSPy module as we've seen in previous docs. Additionally, this class would now inherit the `dspy.Retrieve` class to maintain state management within the DSPy library.

So let's implement `__init__` and `forward` method where our class's `__call__` is calling the `forward` method as is=:

```python
import dspy
from typing import List, Union, Optional

class DSPythonicRMClient(dspy.Retrieve):
    def __init__(self, k:int):
        pass

    def forward(self, query: Union[str, List[str]], k:Optional[str]) -> dspy.Prediction:
        pass
```

Unlike `PythonicRMClient`, we initialize `k` as part of the initialization call and the `forward` method will take query/queries as arguments and the `k` number of retrieved passages as an optional argument. `k` is used within the inherited `dspy.Retrieve` initialization when we call `super().__init__()`.

We'll be implementing `DSPythonicRMClient` for the same local retrieval model API we used above. We'll start by implementing the `__init__` method, which mirrors the `PythonicRMClient`.

```python
def __init__(self, url: str, port:int = None, k:int = 3):
    super().__init__(k=k)

    self.url = f`{url}:{port}` if port else url
```

We'll now implement the `forward` method, returning the output as a `dspy.Prediction` object under the `passage` attribute which is standard among all the RM modules. The call will default to the defined `self.k` argument unless overridden in this call. 

```python
def forward(self, query:str, k:Optional[int]) -> dspy.Prediction:
    params = {"query": query, "k": k if k else self.k}
    response = requests.get(self.url, params=params)

    response = response.json()["retrieved_passages"]    # List of top k passages
    return dspy.Prediction(
        passages=response
    )
```

Let's bring it all together and see how our RM class looks like:

```python
import dspy
from typing import List, Union, Optional

class DSPythonicRMClient(dspy.Retrieve):
    def __init__(self, url: str, port:int = None, k:int = 3):
        super().__init__(k=k)

        self.url = f`{url}:{port}` if port else url

    def forward(self, query_or_queries:str, k:Optional[int]) -> dspy.Prediction:
        params = {"query": query_or_queries, "k": k if k else self.k}
        response = requests.get(self.url, params=params)

        response = response.json()["retrieved_passages"]    # List of top k passages
        return dspy.Prediction(
            passages=response
        )
```

That's all!! This is the way to implement a custom RM model client within DSPy and how more recently-supported RM models like `QdrantRM`, `WeaviateRM`, `LancedbRM`, etc. are implemented in DSPy. 

Let's take a look at how we use these retrievers.

## Using Custom RM Models

DSPy offers two ways of using custom RM clients: Direct Method and using `dspy.Retrieve`.

### Direct Method

The most straightforward way to use your custom RM is by directly using its object within the DSPy Pipeline. 

Let's take a look at the following pseudocode of a DSPy Pipeline as an example:

```python
class DSPyPipeline(dspy.Module):
    def __init__(self):
        super().__init__()

        url = "http://0.0.0.0"
        port = 3000

        self.pythonic_rm = PythonicRMClient(url=url, port=port)
        self.dspythonic_rm = DSPythonicRMClient(url=url, port=port, k=3)

        ...

    def forward(self, *args):
        ...

        passages_from_pythonic_rm = self.pythonic_rm(query)
        passages_from_dspythonic_rm = self.dspythonic_rm(query).passages

        ...
```

This ensures you retrieve a list of passages from your RM client and can interact with the results within your forward pass in whichever way needed for your pipeline's purpose!

### Using `dspy.Retrieve`

This way is more experimental in essence, allowing you to maintain the same pipeline and experiment with different RMs. How? By configuring it!

```python
import dspy

lm = ...
url = "http://0.0.0.0"
port = 3000

# pythonic_rm = PythonicRMClient(url=url, port=port)
dspythonic_rm = DSPythonicRMClient(url=url, port=port, k=3)

dspy.settings.configure(lm=lm, rm=dspythonic_rm)
```

Now, in the pipeline, you just need to use `dspy.Retrieve` which will use this `rm` client to get the top-k passage for a given query!

```python
class DSPyPipeline(dspy.Module):
    def __init__(self):
        super().__init__()

        url = "http://0.0.0.0"
        port = 3000

        self.rm = dspy.Retrieve(k=3)
        ...

    def forward(self, *args):
        ...

        passages = self.rm(query)

        ...
```

Now if you'd like to use a different RM, you can just update the `rm` parameter via `dspy.settings.configure`.

!!! info "How `dspy.Retrieve` uses `rm`"
    When we call `dspy.Retrieve` the `__call__` method will execute the `forward` method as is. In `forward`, the top-k passages are received by the `dsp.retrieveEnsemble` method in [search.py](https://github.com/stanfordnlp/dspy/blob/main/dsp/primitives/search.py).

    If an `rm` is not initialized in `dsp.settings`, this would raise an error.

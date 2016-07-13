Title: Using Kendall's tau to compare recommendations
Date: 2016-07-12 15:00
Slug: kendall-tau-recommendations
Author: Rogier van der Geer
Excerpt: How to use Kendall's tau to compare recommendations.
Template: article
Latex:

<span class="lead">Kendall's tau is a rank correlation metric, used to compare the order of two lists.</span>

### Intro

The [Kendall Tau](https://en.wikipedia.org/wiki/Kendall_rank_correlation_coefficient) is a metric that can be used to compare the order of two ranks. It takes two ranks _that contain the same elements_ and calculates the correlation between them. A correlation of $+1$ means the ranks are equal, while a correlation of $-1$ means the ranks are exactly eachother's reverse. If two ranks are independent or randomly shuffled the correlation will be zero on average.

### Definition

The Kendall tau is defined as

$$\tau \equiv \frac{n_c - n_d}{n(n-1)/2},$$

where $n$ is the length of the ranks, $n_c$ is the number of _concordant_ pairs, and $n_d$ is the number of _discordant_ pairs.

Between two ranks $a$ and $b$, a pair of items $i$ and $j$ is

- _concordant_ if $a_i > a_j$ and $b_i > b_j$, or $a_i < a_j$ and $b_i < b_j$,
- _discordant_ If $a_i > a_j$ and $b_i < b_j$ or vice versa.
- neither _concordant_ nor _discordant_ in the case of ties, if $a_i = a_j$ or $b_i = b_j$.

### An example

Let's have a look at these two ranks:
```python
rank_a = {'apple': 0, 'banana': 2, 'kiwi': 3, 'pear': 1}
rank_b = {'apple': 2, 'banana': 1, 'kiwi': 3, 'pear': 0}
```


Here $a_\text{apple} < a_\text{pear}$, while $b_\text{apple} > b_\text{pear}$, so this pair is _discordant_. 
Also, $a_\text{pear} < a_\text{banana}$ and $b_\text{pear} < b_\text{banana}$, so that pair is _condordant_.
In total, this example contains four concordant pairs and two discordant pairs. Since $n=4$, this means that
$$\tau = \frac{4-2}{6} = \frac{1}{3},$$
which means the two ranks are slightly correlated.

Please note that since there are no ties in the above example, we can directly translate it to two lists:
```python
a = ['apple', 'pear', 'banana', 'kiwi']
b = ['pear', 'banana', 'apple', 'kiwi']
```
In list-form, a concordant pair has the same order in both lists, while the order of a discordant pair is swapped. Two elements cannot occupy the same spot, so we can not have ties.

### Comparing top items

I often encounter situations where I want to compare two ranks, but where I am mostly (if not only) interested in the top end of the rank. An example of this are recommenders: a recommender of a webshop will rank all products that the webshop has to offer and then display the most relevant (let's say top-5) products on a page. So if I want to compare the results of two recommenders I might be interested in the top-5 or top-10, but I'm definitely not interested at what happens at the bottom of the lists.

Of course I can compare the top-10 results from recommender A with the top-5 results from recommender B. 
But the problem here is that the Kendall tau is not defined if the lists do not contain the same elements. And of course
the top-5 of two (very) long ranks will most likely contain some mismatched elements (if not all!).

### Ignoring mismatches

The easiest way to deal with mismatches is to ignore them. By simply removing all elements that do not occur in both
lists we reduce the problem to one that we _can_ solve. For example,
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'pineapple']
b = ['pear', 'orange', 'banana', 'apple', 'kiwi']
```
would be reduced to the example above, where $\tau = \frac{1}{3}$. At first glance, that seems acceptable. However, in here:
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'pineapple']
b = ['apple', 'pear', 'banana', 'kiwi', 'orange']
```
lists `a` and `b` would be reduced to identical lists, yielding $\tau = 1$ even though the original lists are not the same.

The problems become worse when there are more mismatches in the list:
```python
a = ['pineapple', 'lemon', 'apple', 'kiwi', 'grape']
b = ['apple', 'pear', 'banana', 'kiwi', 'orange']
```
would _also_ evaluate to $\tau = 1$ (since `apple` and `kiwi` are concordant), while I would argue the lists are far from
equal. In the extreme case that there is only one match,
```python
a = ['pineapple', 'lemon', 'apple', 'kiwi', 'grape']
b = ['apple', 'pear', 'banana', 'plum', 'orange']
```
the Kendall tau is undefined, as the denominator $n(n-1)/2 = 0$ for $n=1$. So clearly, ignoring mismatches is not the solution to our problem.

### Appending mismatches

Instead of ignoring the mismatches, we can also append them to the bottom of the other list. In a way this makes sense, since all results _are_ in both lists, but not necessarily in the top-5. Since we do not have any information on _where_
the results are in the list (below the top-5) we should treat all results below the top-5 as equal. For example:
```python
a = ['pineapple', 'apple', 'pear', 'kiwi', 'grape']
b = ['apple', 'pear', 'banana', 'kiwi', 'orange']
```
would then become
```python
rank_a = {'apple': 1, 'banana': 5, 'grape': 4, 'orange': 5, 'pear': 2, 'pineapple': 0, 'kiwi': 3}
rank_b = {'apple': 0, 'banana': 2, 'grape': 5, 'orange': 4, 'pear': 1, 'pineapple': 5, 'kiwi': 3}
```
where `banana` and `orange` end up in a tied 5th place in rank `a`, and `pineapple` and `grape` share a tied 5th place
in rank `b`. This yields $\tau = 0.15$, which is close to what I would expect.

If we do this for other examples we get some nice results. For example if only the _last_ element of list `b` is replaced by one not in `a`,
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'grape']
b = ['apple', 'pear', 'banana', 'kiwi', 'orange']
```
we find $\tau = 0.87$. If instead we change the _first_ element,
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'grape']
b = ['orange', 'pear', 'banana', 'kiwi', 'grape']
```
we find $\tau = -0.20$ which is much lower, as we expect. Also, if we replace an additional element,
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'grape']
b = ['orange', 'pear', 'pineapple', 'kiwi', 'grape']
```
we again find a lower correlation: $\tau = -0.45$. 

#### The problem
If we replace _all_ elements, 
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'grape']
b = ['orange', 'tomato', 'pineapple', 'lemon', 'plum']
```
we find a largely negative correlation: $\tau = -0.71$. In principle a strongly negative correlation is what we expect 
here. However, if we compare this with
```python
a = ['apple', 'pear', 'banana', 'kiwi', 'grape']
c = ['grape', 'kiwi', 'banana', 'pear', 'apple']
```
which have a correlation of $\tau = -1$, I would say this is _not_ what we expect: I would say an inverted top-5 
is closer to the original than one that is completely different.

So why is the correlation of `a` and `b` larger than that of `a` and `c`? It is clear that between `a` and `c` all
pairs of words are discordant. If we have a closer look at the resulting ranks when we compare `a` and `b`:
```python
rank_a = {'apple': 0, 'banana': 2, 'grape': 4, 'kiwi': 3, 'lemon': 5, 
          'orange': 5, 'pear': 1, 'pineapple': 5, 'plum': 5, 'tomato': 5}
rank_b = {'apple': 5, 'banana': 5, 'grape': 5, 'kiwi': 5, 'lemon': 3, 
          'orange': 0, 'pear': 5, 'pineapple': 2, 'plum': 4, 'tomato': 1}        
```
we see that also here there are no concordant pairs. Not all pairs are discordant, however, as all pairs of which both items occur in the same list are tied in the other. For example `apple` and `banana` are tied in rank `b`, and are therefore not discordant. So the difference between the two correlations comes from the difference in number of ties, or the difference in length of the ranks.

### Extending the ranks

